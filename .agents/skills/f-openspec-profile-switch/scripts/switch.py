#!/usr/bin/env python3
"""OpenSpec profile switcher (legacy <-> opsx). Cross-platform.

Default is dry-run. Pass --apply to execute Moves/Copies/Removes.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

LEGACY_SKILLS = [
    "openspec-archiving",
    "openspec-context-loading",
    "openspec-implementation",
    "openspec-proposal-creation",
    "openspec-proposal-creation-cn",
]
OPSX_SKILLS_FIXED = [
    "openspec-apply-change",
    "openspec-archive-change",
    "openspec-bulk-archive-change",
    "openspec-continue-change",
    "openspec-explore",
    "openspec-ff-change",
    "openspec-new-change",
    "openspec-onboard",
    "openspec-propose",
    "openspec-sync-specs",
    "openspec-update-change",
    "openspec-verify-change",
]
SWITCHER_NAME = "f-openspec-profile-switch"
PROFILE_LIVE_ROOTS = {"legacy": "spec", "opsx": "openspec"}

VAULT_ROOT = Path.home() / ".openspec-profiles"
ACTIVE_FILE = VAULT_ROOT / "ACTIVE"
MANAGED_FILE = VAULT_ROOT / "managed-roots.json"
LOG_FILE = VAULT_ROOT / "LAST-SWITCH.log"


@dataclass
class Plan:
    op: str  # Move | Copy | Remove
    src: Path
    dest: Optional[Path] = None


def resolve_repo(hint: str) -> Path:
    if hint:
        p = Path(hint).expanduser().resolve()
        if p.exists():
            return p
    cwd = Path.cwd().resolve()
    try:
        out = subprocess.check_output(
            ["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if out:
            return Path(out).resolve()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return cwd


def candidate_roots(repo: Path) -> dict:
    home = Path.home()
    return {
        "skill_user": [
            home / ".cursor" / "skills",
            home / ".agents" / "skills",
            home / ".codex" / "skills",
            home / ".qoder" / "skills",
            home / ".claude" / "skills",
        ],
        "cmd_user": [
            home / ".cursor" / "commands",
            home / ".agents" / "commands",
            home / ".codex" / "commands",
            home / ".qoder" / "commands",
        ],
        "skill_repo": [
            repo / ".cursor" / "skills",
            repo / ".agents" / "skills",
            repo / ".codex" / "skills",
            repo / ".qoder" / "skills",
            repo / ".claude" / "skills",
        ],
        "cmd_repo": [
            repo / ".cursor" / "commands",
            repo / ".qoder" / "commands",
        ],
    }


def is_qoder_commands(root: Path) -> bool:
    parts = [p.lower() for p in root.parts]
    return len(parts) >= 2 and parts[-2] == ".qoder" and parts[-1] == "commands"


def is_profile_skill(name: str, profile: str) -> bool:
    if name == SWITCHER_NAME:
        return False
    if profile == "legacy":
        return name in LEGACY_SKILLS
    if name in OPSX_SKILLS_FIXED:
        return True
    return name.startswith("superpowers-")


def root_has_membership(root: Path, kind: str) -> bool:
    if not root.is_dir():
        return False
    if kind == "skills":
        for d in root.iterdir():
            if d.is_dir() and (
                is_profile_skill(d.name, "legacy") or is_profile_skill(d.name, "opsx")
            ):
                return True
        return False
    if (root / "opsx").is_dir() or (root / "superpowers").is_dir():
        return True
    return any(
        f.is_file()
        and (f.name.startswith("opsx-") or f.name.startswith("superpowers-"))
        and f.suffix == ".md"
        for f in root.iterdir()
    )


def ensure_vault() -> None:
    for profile in ("legacy", "opsx"):
        (VAULT_ROOT / profile / "skills").mkdir(parents=True, exist_ok=True)
        (VAULT_ROOT / profile / "commands" / "opsx").mkdir(parents=True, exist_ok=True)
        (VAULT_ROOT / profile / "commands" / "superpowers").mkdir(
            parents=True, exist_ok=True
        )


def read_active() -> str:
    if not ACTIVE_FILE.is_file():
        return ""
    return ACTIVE_FILE.read_text(encoding="utf-8-sig").strip()


def write_active(value: str) -> None:
    ensure_vault()
    ACTIVE_FILE.write_bytes(value.encode("utf-8"))


def read_managed() -> Optional[dict]:
    if not MANAGED_FILE.is_file():
        return None
    # PowerShell Set-Content -Encoding UTF8 often writes a BOM
    return json.loads(MANAGED_FILE.read_text(encoding="utf-8-sig"))


def write_managed(obj: dict) -> None:
    ensure_vault()
    # utf-8 without BOM for cross-tool compatibility
    text = json.dumps(obj, indent=4, ensure_ascii=False) + "\n"
    MANAGED_FILE.write_bytes(text.encode("utf-8"))


def write_log(message: str) -> None:
    ensure_vault()
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def ref_readme_root() -> str:
    return """# openspec-ref

Parked specification roots for profile switching.

Profiles use **different live directories** (do not mix):
- `legacy` live root: `spec/`
- `opsx` live root: `openspec/`

- Trees under `openspec-ref/<profile>/` are **not** active. **Reference only** — do not run openspec/legacy workflows against them.
- Managed by skill `f-openspec-profile-switch`.
"""


def ref_readme_profile(profile: str) -> str:
    live = PROFILE_LIVE_ROOTS[profile]
    when = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""# openspec-ref / {profile}

Parked root for profile **{profile}**.

- Live directory when active: `{live}/`
- **Reference only** — do not operate; do not treat as the live root.
- To activate: `f-openspec-profile-switch` switch {profile} --apply
- Parked: {when}
"""


def write_ref_readmes(repo: Path, profile: str) -> None:
    ref_root = repo / "openspec-ref"
    prof = ref_root / profile
    prof.mkdir(parents=True, exist_ok=True)
    (ref_root / "README.md").write_text(ref_readme_root(), encoding="utf-8", newline="\n")
    (prof / "README.md").write_text(
        ref_readme_profile(profile), encoding="utf-8", newline="\n"
    )


def invoke_plans(plans: List[Plan], apply: bool) -> None:
    if not plans:
        print("No file operations planned.")
        return
    print()
    print("=== PLAN ===")
    for p in plans:
        if p.op == "Remove":
            print(f"Remove: {p.src}")
        else:
            print(f"{p.op}: {p.src}")
            print(f"  -> {p.dest}")
    if not apply:
        print()
        print("Dry-run only. Re-run with --apply to execute.")
        return
    for p in plans:
        if p.op == "Remove":
            if p.src.exists():
                if p.src.is_dir():
                    shutil.rmtree(p.src)
                else:
                    p.src.unlink()
            write_log(f"Remove {p.src}")
            continue
        if p.dest is None:
            print(f"Warning: Skip {p.op}: empty destination (from {p.src})", file=sys.stderr)
            continue
        p.dest.parent.mkdir(parents=True, exist_ok=True)
        if not p.src.exists():
            print(f"Warning: Skip missing: {p.src}", file=sys.stderr)
            continue
        if p.dest.exists():
            if p.dest.is_dir():
                shutil.rmtree(p.dest)
            else:
                p.dest.unlink()
        if p.op == "Move":
            shutil.move(str(p.src), str(p.dest))
        elif p.op == "Copy":
            if p.src.is_dir():
                shutil.copytree(p.src, p.dest)
            else:
                shutil.copy2(p.src, p.dest)
        write_log(f"{p.op} {p.src} -> {p.dest}")
    print()
    print(f"Applied. Log: {LOG_FILE}")


def collect_command_moves_to_vault(
    cmd_roots: Iterable[Path], profile: str, vault_cmds: Path
) -> List[Plan]:
    if profile != "opsx":
        return []
    plans: List[Plan] = []
    claimed = set()
    for root in cmd_roots:
        if not root.is_dir():
            continue
        files: List[Path] = []
        for group in ("opsx", "superpowers"):
            nested = root / group
            if nested.is_dir():
                files.extend(p for p in nested.glob("*.md") if p.is_file())
        files.extend(
            p
            for p in root.glob("*.md")
            if p.is_file()
            and (p.name.startswith("opsx-") or p.name.startswith("superpowers-"))
        )
        for f in files:
            parent_leaf = f.parent.name
            if parent_leaf in ("opsx", "superpowers"):
                group, cmd = parent_leaf, f.name
            elif f.name.startswith("opsx-"):
                group, cmd = "opsx", f.name[5:]
            elif f.name.startswith("superpowers-"):
                group, cmd = "superpowers", f.name[12:]
            else:
                continue
            if not cmd.endswith(".md"):
                cmd = f"{cmd}.md"
            dest = vault_cmds / group / cmd
            key = str(dest)
            if dest.exists() or key in claimed:
                plans.append(Plan("Remove", f, None))
            else:
                claimed.add(key)
                plans.append(Plan("Move", f, dest))
    return plans


def collect_park_live_to_vault(
    skill_roots: Iterable[Path], cmd_roots: Iterable[Path], profile: str
) -> List[Plan]:
    plans: List[Plan] = []
    v_skills = VAULT_ROOT / profile / "skills"
    v_cmds = VAULT_ROOT / profile / "commands"
    v_skills.mkdir(parents=True, exist_ok=True)
    (v_cmds / "opsx").mkdir(parents=True, exist_ok=True)
    (v_cmds / "superpowers").mkdir(parents=True, exist_ok=True)
    claimed = set()
    for root in skill_roots:
        if not root.is_dir():
            continue
        for d in root.iterdir():
            if not d.is_dir() or not is_profile_skill(d.name, profile):
                continue
            dest = v_skills / d.name
            key = str(dest)
            if dest.exists() or key in claimed:
                plans.append(Plan("Remove", d, None))
            else:
                claimed.add(key)
                plans.append(Plan("Move", d, dest))
    plans.extend(collect_command_moves_to_vault(cmd_roots, profile, v_cmds))
    return plans


def collect_deploy_from_vault(
    skill_roots: Iterable[Path], cmd_roots: Iterable[Path], profile: str
) -> List[Plan]:
    plans: List[Plan] = []
    v_skills = VAULT_ROOT / profile / "skills"
    v_cmds = VAULT_ROOT / profile / "commands"
    if v_skills.is_dir():
        for skill in v_skills.iterdir():
            if not skill.is_dir():
                continue
            for root in skill_roots:
                plans.append(Plan("Copy", skill, root / skill.name))
    if profile == "opsx" and v_cmds.is_dir():
        for root in cmd_roots:
            qoder = is_qoder_commands(root)
            for group in ("opsx", "superpowers"):
                gdir = v_cmds / group
                if not gdir.is_dir():
                    continue
                for f in gdir.glob("*.md"):
                    if not f.is_file():
                        continue
                    if qoder:
                        dest = root / group / f.name
                    else:
                        dest = root / f"{group}-{f.name}"
                    plans.append(Plan("Copy", f, dest))
    return plans


def profile_live_root(repo: Path, profile: str) -> Path:
    rel = PROFILE_LIVE_ROOTS.get(profile)
    if not rel:
        raise ValueError(f"Unknown profile live root: {profile}")
    return repo / rel


def park_content_entries(path: Path) -> List[Path]:
    if not path.is_dir():
        return []
    return [p for p in path.iterdir() if p.name != "README.md"]


def resolve_park_with_content(repo: Path, profile: str) -> Optional[Path]:
    """Prefer canonical openspec-ref/<profile>/; else newest openspec-ref/<profile>_*. """
    ref = repo / "openspec-ref"
    candidates: List[Path] = []
    canon = ref / profile
    if canon.is_dir():
        candidates.append(canon)
    stamped = sorted(
        (p for p in ref.glob(f"{profile}_*") if p.is_dir()),
        key=lambda p: p.name,
        reverse=True,
    )
    candidates.extend(stamped)
    for c in candidates:
        if park_content_entries(c):
            return c
    return None


def collect_park_profile_root(repo: Path, park_profile: str) -> List[Plan]:
    live = profile_live_root(repo, park_profile)
    if not live.exists():
        return []
    dest = repo / "openspec-ref" / park_profile
    plans: List[Plan] = []
    if dest.exists():
        if not park_content_entries(dest):
            # README-only stub from a prior restore — remove so park uses canonical path
            plans.append(Plan("Remove", dest, None))
        else:
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            dest = repo / "openspec-ref" / f"{park_profile}_{stamp}"
    plans.append(Plan("Move", live, dest))
    return plans


def collect_restore_profile_root(repo: Path, profile: str) -> List[Plan]:
    src = resolve_park_with_content(repo, profile)
    if src is None:
        return []
    live = profile_live_root(repo, profile)
    if live.exists():
        raise RuntimeError(
            f"Cannot restore openspec-ref/{profile}: live root "
            f"{PROFILE_LIVE_ROOTS[profile]}/ already exists. Park it first."
        )
    return [Plan("Move", src, live)]


def collect_sync_spec_roots(repo: Path, target: str) -> List[Plan]:
    plans: List[Plan] = []
    for p in ("legacy", "opsx"):
        if p == target:
            plans.extend(collect_restore_profile_root(repo, p))
        else:
            plans.extend(collect_park_profile_root(repo, p))
    return plans


def deploy_switcher(user_skill_roots: Iterable[Path], source_skill_dir: Path) -> List[Plan]:
    if not source_skill_dir.is_dir():
        print(f"Warning: Switcher source missing: {source_skill_dir}", file=sys.stderr)
        return []
    plans: List[Plan] = []
    seen = set()
    for root in user_skill_roots:
        if not root:
            continue
        dest = root / SWITCHER_NAME
        key = str(dest.resolve()) if dest.parent.exists() else str(dest)
        if key in seen or dest.resolve() == source_skill_dir.resolve():
            continue
        seen.add(key)
        plans.append(Plan("Copy", source_skill_dir, dest))
    return plans


def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def cmd_status(repo: Path) -> int:
    ensure_vault()
    cands = candidate_roots(repo)
    active = read_active()
    managed = read_managed()
    print(f"RepoRoot: {repo}")
    print(f"Vault:    {VAULT_ROOT}")
    print(
        f"ACTIVE:   {active if active else '(none — run init, then switch --apply)'}"
    )
    if managed:
        print("Managed skill roots:")
        for r in managed.get("skillRoots") or []:
            print(f"  - {r}")
        print("Managed command roots:")
        for r in managed.get("commandRoots") or []:
            print(f"  - {r}")
    else:
        print("managed-roots.json: missing (run init)")
    print()
    print("Live membership in candidate roots:")
    for root in cands["skill_user"] + cands["skill_repo"]:
        if not root.is_dir():
            continue
        hits = []
        for d in root.iterdir():
            if not d.is_dir():
                continue
            if is_profile_skill(d.name, "legacy"):
                hits.append(f"legacy:{d.name}")
            elif is_profile_skill(d.name, "opsx"):
                hits.append(f"opsx:{d.name}")
            elif d.name == SWITCHER_NAME:
                hits.append(f"switcher:{d.name}")
        if hits:
            print(f"  {root}")
            for h in hits:
                print(f"    {h}")
    print(f"legacy live (spec/):     {'present' if (repo / 'spec').exists() else 'absent'}")
    print(
        f"opsx live (openspec/):   {'present' if (repo / 'openspec').exists() else 'absent'}"
    )
    ref = repo / "openspec-ref"
    print(f"openspec-ref/:           {'present' if ref.exists() else 'absent'}")
    if ref.is_dir():
        for d in sorted(ref.iterdir()):
            if d.is_dir():
                print(f"  parked: {d.name}")
    if LOG_FILE.is_file():
        print()
        print("Last log lines:")
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        for line in lines[-5:]:
            print(f"  {line}")
    return 0


def cmd_init(repo: Path, apply: bool) -> int:
    ensure_vault()
    cands = candidate_roots(repo)
    skill_scan = [
        r
        for r in cands["skill_user"] + cands["skill_repo"]
        if root_has_membership(r, "skills")
    ]
    skill_managed = [r for r in cands["skill_user"] if r.exists()]
    for r in skill_scan:
        if r not in cands["skill_repo"] and r not in skill_managed:
            skill_managed.append(r)
    cmd_roots = [
        r
        for r in cands["cmd_user"] + cands["cmd_repo"]
        if root_has_membership(r, "commands")
    ]
    plans: List[Plan] = []
    plans.extend(collect_park_live_to_vault(skill_scan, cmd_roots, "legacy"))
    plans.extend(collect_park_live_to_vault(skill_scan, cmd_roots, "opsx"))

    print("Init will park BOTH profiles into vault. Does NOT set ACTIVE.")
    print("Skill roots scanned: " + "; ".join(str(p) for p in skill_scan))
    print(
        "Skill roots managed (user-global deploy): "
        + "; ".join(str(p) for p in skill_managed)
    )
    print("Command roots to manage: " + "; ".join(str(p) for p in cmd_roots))

    if apply:
        write_managed(
            {
                "skillRoots": [str(p) for p in skill_managed],
                "commandRoots": [str(p) for p in cmd_roots],
                "repoRoot": str(repo),
                "skillRootsScope": "user-global",
                "note": (
                    "opsx/superpowers skills+commands deploy to user-global only; "
                    "not project .cursor"
                ),
                "initialized": datetime.now().isoformat(),
            }
        )
        write_active("")
        write_log(f"init begin repo={repo}")

    invoke_plans(plans, apply)

    if apply:
        for d in VAULT_ROOT.glob("_dup*"):
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
        src = skill_dir()
        if src.name == SWITCHER_NAME:
            extra = [r for r in cands["skill_user"] if r.exists()]
            invoke_plans(deploy_switcher(extra, src), True)
        write_log("init done (ACTIVE unset)")
        print(
            "Next: python scripts/switch.py switch opsx|legacy --repo-root <repo> --apply"
        )
    return 0


def cmd_switch(
    repo: Path, profile: str, apply: bool, specs_only: bool
) -> int:
    ensure_vault()
    cands = candidate_roots(repo)
    managed = read_managed()
    if not managed and not specs_only:
        raise SystemExit("managed-roots.json missing. Run init first.")

    active = read_active()
    plans: List[Plan] = []

    print(
        f"Switch -> {profile} (current ACTIVE='{active or '(none)'}')"
        + (" [specs-only]" if specs_only else "")
    )

    if not specs_only:
        skill_roots = [Path(p) for p in (managed.get("skillRoots") or [])]
        cmd_roots = [Path(p) for p in (managed.get("commandRoots") or [])]
        skill_park = list(skill_roots)
        for pr in cands["skill_repo"]:
            if pr.exists() and pr not in skill_park:
                skill_park.append(pr)
        print(
            "Deploy skills to (user-global): "
            + "; ".join(str(p) for p in skill_roots)
        )
        plans.extend(collect_park_live_to_vault(skill_park, cmd_roots, "legacy"))
        plans.extend(collect_park_live_to_vault(skill_park, cmd_roots, "opsx"))
        plans.extend(collect_sync_spec_roots(repo, profile))
        plans.extend(collect_deploy_from_vault(skill_roots, cmd_roots, profile))
    else:
        print("Skipping skills/commands; syncing spec roots only for this repo.")
        plans.extend(collect_sync_spec_roots(repo, profile))

    if apply:
        write_log(
            f"switch begin -> {profile}" + (" specs-only" if specs_only else "")
        )

    invoke_plans(plans, apply)

    if apply:
        write_ref_readmes(repo, "legacy")
        write_ref_readmes(repo, "opsx")
        ref_root = repo / "openspec-ref"
        if ref_root.exists():
            (ref_root / "README.md").write_text(
                ref_readme_root(), encoding="utf-8", newline="\n"
            )
        if not specs_only:
            write_active(profile)
            src = skill_dir()
            if src.name == SWITCHER_NAME and managed:
                user_roots = [
                    Path(p)
                    for p in (managed.get("skillRoots") or [])
                    if not str(p).startswith(str(repo))
                ]
                user_roots.extend(r for r in cands["skill_user"] if r.exists())
                # unique
                seen = set()
                uniq = []
                for r in user_roots:
                    k = str(r)
                    if k not in seen:
                        seen.add(k)
                        uniq.append(r)
                invoke_plans(deploy_switcher(uniq, src), True)
            for d in VAULT_ROOT.glob("_dup*"):
                if d.is_dir():
                    shutil.rmtree(d, ignore_errors=True)
            write_log(f"switch done ACTIVE={profile}")
            print(f"ACTIVE={profile}")
        else:
            write_log(f"switch specs-only done target={profile} (ACTIVE unchanged={active})")
            print(f"specs-only done for {repo}; global ACTIVE unchanged ({active or 'none'})")
        print("Live roots: legacy=spec/ opsx=openspec/ (only target profile root should be present)")
        if not specs_only:
            print("Fully quit Cursor, reopen, start a NEW Agent chat, then verify with /")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="OpenSpec profile switcher (legacy <-> opsx)"
    )
    parser.add_argument(
        "action", choices=["status", "init", "switch"], help="Action to run"
    )
    parser.add_argument(
        "profile",
        nargs="?",
        choices=["legacy", "opsx"],
        help="Target profile (required for switch)",
    )
    parser.add_argument(
        "--repo-root",
        default="",
        help="Repository root (default: git toplevel or cwd)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute planned file operations (default: dry-run)",
    )
    parser.add_argument(
        "--specs-only",
        action="store_true",
        help="Only sync this repo's spec/openspec/openspec-ref; do not touch global skills or ACTIVE",
    )
    args = parser.parse_args(argv)
    repo = resolve_repo(args.repo_root)

    if args.action == "status":
        return cmd_status(repo)
    if args.action == "init":
        if args.specs_only:
            raise SystemExit("--specs-only is only valid with switch")
        return cmd_init(repo, args.apply)
    if args.action == "switch":
        if not args.profile:
            raise SystemExit("switch requires profile: legacy | opsx")
        return cmd_switch(repo, args.profile, args.apply, args.specs_only)
    return 1


if __name__ == "__main__":
    sys.exit(main())
