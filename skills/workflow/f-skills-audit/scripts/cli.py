#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("sync_lib", SCRIPT_DIR / "sync_lib.py")
sync_lib = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(sync_lib)


def _library(args: argparse.Namespace) -> Path:
    if getattr(args, "library", None):
        return Path(args.library).expanduser().resolve()
    return sync_lib.find_library_root()


def _load(library: Path):
    cfg = sync_lib.load_config(library / "skills-sync.yaml")
    catalog = sync_lib.load_catalog(library / "skills-catalog.json")
    agents = library / ".agents" / "skills"
    return cfg, catalog, agents


def _confirm(prompt: str, yes: bool) -> bool:
    if yes:
        return True
    try:
        answer = input(f"{prompt} [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def _now_id(action: str, skill: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{action}-{skill}"


def cmd_validate_config(args: argparse.Namespace) -> int:
    library = _library(args)
    sync_lib.load_config(library / "skills-sync.yaml")
    print(f"OK: {library / 'skills-sync.yaml'}")
    return 0


def cmd_hash(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser().resolve()
    print(sync_lib.content_hash(path))
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    library = _library(args)
    cfg, _catalog, agents = _load(library)
    lib_skills = sync_lib.list_skill_dirs(agents)
    print(f"library: {library}")
    print(f"truth skills: {len(lib_skills)}")

    for name, meta in (cfg.get("targets") or {}).items():
        writable = bool((meta or {}).get("write"))
        try:
            root = sync_lib.resolve_target_path(name, meta or {})
        except ValueError as e:
            print(f"[{name}] error: {e}")
            continue
        if root is None:
            print(f"[{name}] skipped: not detectable")
            continue
        if sync_lib.is_forbidden_write_path(root):
            print(f"[{name}] forbidden path (never write): {root}")
            continue
        remote = sync_lib.list_skill_dirs(root)
        only_lib = sorted(set(lib_skills) - set(remote))
        only_tgt = sorted(set(remote) - set(lib_skills))
        both = sorted(set(lib_skills) & set(remote))
        diverged = []
        for skill in both:
            if sync_lib.content_hash(lib_skills[skill]) != sync_lib.content_hash(remote[skill]):
                diverged.append(skill)
        mode = "write" if writable else "read-only"
        print(f"\n[{name}] {mode} -> {root}")
        print(f"  only-in-lib: {len(only_lib)}")
        print(f"  only-in-target: {len(only_tgt)}")
        print(f"  diverged: {len(diverged)}")
        if args.verbose:
            if only_lib[:20]:
                print("  only-in-lib sample:", ", ".join(only_lib[:20]))
            if only_tgt[:20]:
                print("  only-in-target sample:", ", ".join(only_tgt[:20]))
            if diverged[:20]:
                print("  diverged sample:", ", ".join(diverged[:20]))
    return 0


def _writable_targets(cfg: dict) -> list[str]:
    return [n for n, m in (cfg.get("targets") or {}).items() if (m or {}).get("write")]


def _sync_one(
    library: Path,
    cfg: dict,
    skill: str,
    src: Path,
    target_name: str,
    target_root: Path,
    yes: bool,
) -> bool:
    if sync_lib.is_forbidden_write_path(target_root):
        print(f"  ! refuse forbidden target {target_name}: {target_root}")
        return False
    dest = target_root / skill
    if dest.exists():
        same = sync_lib.content_hash(src) == sync_lib.content_hash(dest)
        if same:
            print(f"  = {target_name}: skip (same hash)")
            return True
        if not _confirm(f"  ? {target_name}: diverged {skill}, overwrite?", yes):
            print(f"  - {target_name}: skipped (no confirm)")
            return False
    target_root.mkdir(parents=True, exist_ok=True)
    sync_lib.copy_skill_dir(src, dest)
    print(f"  + {target_name}: copied")
    return True


def cmd_sync_out(args: argparse.Namespace) -> int:
    library = _library(args)
    cfg, catalog, agents = _load(library)
    skills = sync_lib.resolve_profile(cfg, catalog, agents, args.profile)
    if args.skill:
        skills = [s for s in skills if s == args.skill]
        if not skills:
            # allow explicit skill even if not in profile, unless excluded
            exclude = set((cfg.get("exclude") or {}).get("names") or []) | set(sync_lib.DEFAULT_SYSTEM_EXCLUDE)
            if args.skill in exclude:
                raise SystemExit(f"skill 在 exclude 中: {args.skill}")
            if not (agents / args.skill).is_dir():
                raise SystemExit(f"真相源不存在: {args.skill}")
            skills = [args.skill]

    targets = args.targets.split(",") if args.targets else _writable_targets(cfg)
    print(f"sync-out profile={args.profile} skills={len(skills)} targets={targets}")

    for skill in skills:
        src = agents / skill
        ok_targets: list[str] = []
        print(f"* {skill}")
        for tname in targets:
            meta = (cfg.get("targets") or {}).get(tname)
            if not meta or not meta.get("write"):
                print(f"  ! {tname}: not writable / missing")
                continue
            root = sync_lib.resolve_target_path(tname, meta)
            if root is None:
                print(f"  ! {tname}: not detectable")
                continue
            if _sync_one(library, cfg, skill, src, tname, root, args.yes):
                ok_targets.append(tname)
        if ok_targets:
            entry = {
                "id": _now_id("sync-out", skill),
                "action": "sync-out",
                "skill": skill,
                "dest_targets": ok_targets,
                "library_rel": f".agents/skills/{skill}",
                "contentHash": sync_lib.content_hash(src),
                "at": datetime.now(timezone.utc).isoformat(),
                "machine": socket.gethostname(),
                "mode": "copy",
                "note": args.note or "",
            }
            path = sync_lib.write_journal_entry(library, cfg, entry)
            print(f"  journal: {path.relative_to(library)}")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    library = _library(args)
    cfg, catalog, agents = _load(library)
    skill = args.skill
    source_name = args.source
    meta = (cfg.get("targets") or {}).get(source_name)
    if not meta:
        raise SystemExit(f"未知 source target: {source_name}")
    src_root = sync_lib.resolve_target_path(source_name, meta)
    if src_root is None:
        raise SystemExit(f"无法解析 source: {source_name}")
    if sync_lib.is_forbidden_write_path(src_root):
        raise SystemExit(f"禁止从该路径 promote: {src_root}")
    src = src_root / skill
    if not src.is_dir():
        raise SystemExit(f"源不存在: {source_name}/{skill}")
    if skill not in (catalog.get("skills") or {}):
        print(f"警告: {skill} 不在 skills-catalog.json，promote 后请按 ingest 规则补 catalog")
    if not _confirm(f"promote {source_name}/{skill} -> .agents/skills/{skill} ?", args.yes):
        print("cancelled")
        return 1
    dest = agents / skill
    sync_lib.copy_skill_dir(src, dest)
    digest = sync_lib.content_hash(dest)
    promote_entry = {
        "id": _now_id("promote", skill),
        "action": "promote",
        "skill": skill,
        "source_target": source_name,
        "library_rel": f".agents/skills/{skill}",
        "contentHash": digest,
        "at": datetime.now(timezone.utc).isoformat(),
        "machine": socket.gethostname(),
        "mode": "copy",
        "note": args.note or "",
    }
    p1 = sync_lib.write_journal_entry(library, cfg, promote_entry)
    dest_targets = _writable_targets(cfg)
    sync_entry = {
        "id": _now_id("sync-out", skill),
        "action": "sync-out",
        "skill": skill,
        "dest_targets": dest_targets,
        "library_rel": f".agents/skills/{skill}",
        "contentHash": digest,
        "at": datetime.now(timezone.utc).isoformat(),
        "machine": socket.gethostname(),
        "mode": "copy",
        "note": "companion of promote",
    }
    p2 = sync_lib.write_journal_entry(library, cfg, sync_entry)
    print(f"promoted -> {dest}")
    print(f"journal: {p1.relative_to(library)}")
    print(f"companion sync-out journal: {p2.relative_to(library)}")
    print("下一步: 运行 sync-skills-catalog status → 生成说明 → render → validate（禁止手改 skills/）")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    library = _library(args)
    cfg, _catalog, agents = _load(library)
    applied = sync_lib.load_applied()
    entries = sync_lib.read_journal_entries(library, cfg)
    for entry in entries:
        eid = entry.get("id") or ""
        action = entry.get("action")
        if eid in applied and not args.force:
            print(f"= skip applied {eid}")
            continue
        if action == "promote":
            print(f"! skip promote-only {eid}（需伴生 sync-out 或显式 sync-out）")
            continue
        if action != "sync-out":
            print(f"! skip unknown action {action} id={eid}")
            continue
        skill = entry.get("skill")
        src = agents / skill
        if not src.is_dir():
            print(f"! missing library skill {skill} for {eid}")
            continue
        ok_all = True
        for tname in entry.get("dest_targets") or []:
            meta = (cfg.get("targets") or {}).get(tname)
            if not meta or not meta.get("write"):
                print(f"  ! {tname}: not writable")
                ok_all = False
                continue
            root = sync_lib.resolve_target_path(tname, meta)
            if root is None:
                print(f"  ! {tname}: not detectable")
                ok_all = False
                continue
            # S1: always copy
            if not _sync_one(library, cfg, skill, src, tname, root, args.yes):
                ok_all = False
        if ok_all:
            sync_lib.mark_applied(eid)
            print(f"+ applied {eid}")
        else:
            print(f"- partial/failed {eid}（未标记 applied）")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="f-skills-sync-cli")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--library", help="fan-skills 库根（含 skills-catalog.json）")
    sub = p.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate-config", parents=[common])
    v.set_defaults(func=cmd_validate_config)

    h = sub.add_parser("hash", parents=[common])
    h.add_argument("path")
    h.set_defaults(func=cmd_hash)

    a = sub.add_parser("audit", parents=[common])
    a.add_argument("-v", "--verbose", action="store_true")
    a.set_defaults(func=cmd_audit)

    s = sub.add_parser("sync-out", parents=[common])
    s.add_argument("--profile", default="default")
    s.add_argument("--skill", default="")
    s.add_argument("--targets", default="", help="逗号分隔逻辑名，默认全部可写 target")
    s.add_argument("--yes", action="store_true")
    s.add_argument("--note", default="")
    s.set_defaults(func=cmd_sync_out)

    pr = sub.add_parser("promote", parents=[common])
    pr.add_argument("--skill", required=True)
    pr.add_argument("--from", dest="source", default="cursor")
    pr.add_argument("--yes", action="store_true")
    pr.add_argument("--note", default="")
    pr.set_defaults(func=cmd_promote)

    ap = sub.add_parser("apply", parents=[common])
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--force", action="store_true", help="忽略本机已应用标记并重放")
    ap.set_defaults(func=cmd_apply)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
