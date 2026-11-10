from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

TRANSIENT_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}
TRANSIENT_FILES = {".DS_Store"}
TRANSIENT_SUFFIXES = {".pyc", ".pyo"}

ABS_UNIX = re.compile(r"^/")
ABS_WIN = re.compile(r"^[A-Za-z]:[\\/]")


def content_hash(skill_dir: Path) -> str:
    """与 sync-skills-catalog/scripts/sync.py 对齐的稳定指纹。"""
    h = hashlib.sha256()
    files = sorted(
        p
        for p in skill_dir.rglob("*")
        if p.is_file()
        and not any(part in TRANSIENT_DIRS for part in p.relative_to(skill_dir).parts)
        and p.name not in TRANSIENT_FILES
        and p.suffix not in TRANSIENT_SUFFIXES
    )
    for p in files:
        rel = p.relative_to(skill_dir).as_posix()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _looks_absolute(value: str) -> bool:
    if value.startswith("~/") or value.startswith("$HOME/") or value in ("~", "$HOME"):
        return False
    if value.startswith("cursor-store://"):
        return False
    return bool(ABS_UNIX.match(value) or ABS_WIN.match(value))


def find_absolute_paths(obj: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found.extend(find_absolute_paths(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(find_absolute_paths(v, f"{path}[{i}]"))
    elif isinstance(obj, str) and _looks_absolute(obj):
        found.append(f"{path}={obj}")
    return found


def expand_user_path(template: str) -> Path:
    if template.startswith("~/"):
        return Path.home() / template[2:]
    if template.startswith("$HOME/"):
        return Path(os.environ["HOME"]) / template[6:]
    if template in ("~", "$HOME"):
        return Path.home()
    if template.startswith("cursor-store://"):
        raise ValueError(f"非文件系统路径，需专用探测: {template}")
    if _looks_absolute(template):
        raise ValueError(f"拒绝绝对路径模板: {template}")
    return Path(template)


DEFAULT_SYSTEM_EXCLUDE = [
    "sync-skills-catalog",
    "automate",
    "autopilot",
    "canvas",
    "create-hook",
    "create-rule",
    "create-skill",
    "create-subagent",
    "deploy-with-vercel",
    "goal",
    "loop",
    "migrate-to-skills",
    "new-repo",
    "onboard",
    "origin",
    "rename-chat",
    "review",
    "review-bugbot",
    "review-security",
    "sdk",
    "share",
    "shell",
    "split-to-prs",
    "statusline",
    "update-cli-config",
    "update-cursor-settings",
]


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise SystemExit("需要 PyYAML：pip install pyyaml") from e
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise SystemExit(f"配置必须是对象: {path}")
    errs = find_absolute_paths(data)
    if errs:
        raise SystemExit("配置含绝对路径:\n" + "\n".join(errs))
    return data


def load_catalog(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_profile(cfg: dict, catalog: dict, agents_dir: Path, profile: str) -> list[str]:
    profiles = cfg.get("profiles") or {}
    if profile not in profiles:
        raise KeyError(f"未知 profile: {profile}")
    prof = profiles[profile]
    include = prof.get("include") or {}
    names: set[str] = set(include.get("names") or [])
    cats = set(include.get("categories") or [])
    skills_meta = catalog.get("skills") or {}
    for name, meta in skills_meta.items():
        if cats & set((meta or {}).get("categories") or []):
            names.add(name)
    exclude = set((cfg.get("exclude") or {}).get("names") or [])
    exclude |= set(DEFAULT_SYSTEM_EXCLUDE)
    existing = {p.name for p in agents_dir.iterdir() if p.is_dir()}
    return sorted((names & existing) - exclude)


def find_library_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for candidate in [cur, *cur.parents]:
        if (candidate / "skills-catalog.json").is_file() and (candidate / ".agents" / "skills").is_dir():
            return candidate
    raise SystemExit("未找到 fan-skills 库根（需含 skills-catalog.json 与 .agents/skills）")


def list_skill_dirs(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {p.name: p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")}


def is_forbidden_write_path(path: Path) -> bool:
    parts = set(path.resolve().parts)
    return "skills-cursor" in parts or ".system" in parts


def detect_cursor_store_skills() -> list[Path]:
    base = Path.home() / "Library" / "Application Support" / "Cursor" / "AgentStores" / "cursor_agent_stores"
    if not base.is_dir():
        return []
    found: list[Path] = []
    for skills in base.glob("*/files/skills"):
        if skills.is_dir():
            found.append(skills)
    return found


def resolve_target_path(name: str, meta: dict) -> Path | None:
    template = (meta or {}).get("path") or ""
    if isinstance(template, str) and template.startswith("cursor-store://"):
        roots = detect_cursor_store_skills()
        return roots[0] if roots else None
    return expand_user_path(template)


def journal_dir(library: Path, cfg: dict) -> Path:
    rel = ((cfg.get("journal") or {}).get("path")) or "skills-sync-journal"
    if _looks_absolute(str(rel)):
        raise SystemExit(f"journal.path 禁止绝对路径: {rel}")
    return library / rel


def write_journal_entry(library: Path, cfg: dict, entry: dict) -> Path:
    import yaml  # type: ignore

    errs = find_absolute_paths(entry)
    if errs:
        raise SystemExit("journal 含绝对路径:\n" + "\n".join(errs))
    jdir = journal_dir(library, cfg)
    jdir.mkdir(parents=True, exist_ok=True)
    path = jdir / f"{entry['id']}.yaml"
    path.write_text(yaml.safe_dump(entry, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def read_journal_entries(library: Path, cfg: dict) -> list[dict]:
    import yaml  # type: ignore

    jdir = journal_dir(library, cfg)
    if not jdir.is_dir():
        return []
    entries: list[dict] = []
    for path in sorted(jdir.glob("*.yaml")):
        if path.name.upper() == "README.YAML":
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("action"):
            entries.append(data)
    entries.sort(key=lambda e: (e.get("at") or "", e.get("id") or ""))
    return entries


def applied_state_path() -> Path:
    return Path.home() / ".config" / "fan-skills" / "applied.json"


def load_applied() -> set[str]:
    path = applied_state_path()
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("applied_ids") or [])


def mark_applied(entry_id: str) -> None:
    path = applied_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    ids = load_applied()
    ids.add(entry_id)
    path.write_text(json.dumps({"applied_ids": sorted(ids)}, indent=2) + "\n", encoding="utf-8")


def copy_skill_dir(src: Path, dest: Path) -> None:
    """原子替换：先拷到临时目录，再替换目标，避免中途失败留下空目录。"""
    import shutil
    import tempfile

    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=str(dest.parent)) as tmp:
        staging = Path(tmp) / "staging"
        shutil.copytree(src, staging)
        backup = Path(tmp) / "backup"
        if dest.exists():
            dest.rename(backup)
        try:
            staging.rename(dest)
        except Exception:
            if backup.exists() and not dest.exists():
                backup.rename(dest)
            raise
