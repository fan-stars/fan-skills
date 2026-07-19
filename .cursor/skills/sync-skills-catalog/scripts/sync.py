#!/usr/bin/env python3
"""从 .agents/skills 按 skills-catalog.json 全量重建分类化 skills/，
并基于 AI 生成结果（generated/skill-docs.json）渲染中文 README。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

# .cursor/skills/sync-skills-catalog/scripts/sync.py → 仓库根
ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = ROOT / "skills-catalog.json"
AGENTS_SKILLS = ROOT / ".agents" / "skills"
SKILLS_OUT = ROOT / "skills"
GENERATED_DIR = Path(__file__).resolve().parents[1] / "generated"
DOCS_PATH = GENERATED_DIR / "skill-docs.json"
MISSING = "暂无"

MIN_SUMMARY = 24
MIN_DETAIL = 40
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
FORBIDDEN_SUMMARY_CHARS = "|"


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"缺少文件: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def content_hash(skill_dir: Path) -> str:
    h = hashlib.sha256()
    files = sorted(p for p in skill_dir.rglob("*") if p.is_file())
    for p in files:
        rel = p.relative_to(skill_dir).as_posix()
        h.update(rel.encode())
        h.update(b"\0")
        h.update(p.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text or ""))


def validate_doc_entry(name: str, entry: dict, expected_hash: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(entry, dict):
        return [f"{name}: 条目必须是对象"]
    if entry.get("contentHash") != expected_hash:
        errors.append(f"{name}: contentHash 与源目录不一致或缺失")
    summary = (entry.get("summary") or "").strip()
    if len(summary) < MIN_SUMMARY or not has_cjk(summary):
        errors.append(f"{name}: summary 过短或非中文")
    if FORBIDDEN_SUMMARY_CHARS in summary:
        errors.append(f"{name}: summary 含非法字符 '|'")
    for field in ("capabilities", "scenarios", "coverage", "notes"):
        val = (entry.get(field) or "").strip()
        if len(val) < MIN_DETAIL or not has_cjk(val):
            errors.append(f"{name}: {field} 过短或非中文")
    return errors


def load_catalog() -> dict:
    return load_json(CATALOG_PATH)


def validate_catalog(catalog: dict) -> None:
    agents = {p.name for p in AGENTS_SKILLS.iterdir() if p.is_dir()} if AGENTS_SKILLS.is_dir() else set()
    skills = catalog.get("skills", {})
    categories = catalog.get("categories", {})
    names = set(skills)
    if names != agents:
        raise SystemExit(
            "catalog 与 .agents/skills 不一致:\n"
            f"  catalog 多出: {sorted(names - agents)}\n"
            f"  agents 多出: {sorted(agents - names)}"
        )
    for name, meta in skills.items():
        if "descriptionZh" in meta or "detailsZh" in meta:
            raise SystemExit(f"{name}: catalog 不得包含 descriptionZh/detailsZh")
        cats = meta.get("categories") or []
        if not cats:
            raise SystemExit(f"{name} 缺少 categories")
        for c in cats:
            if c not in categories:
                raise SystemExit(f"{name} 引用未知分类: {c}")


def current_hashes(catalog: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in catalog["skills"]:
        src = AGENTS_SKILLS / name
        if not src.is_dir():
            raise SystemExit(f"源目录不存在: {src}")
        out[name] = content_hash(src)
    return out


def load_docs() -> dict:
    if not DOCS_PATH.is_file():
        return {"version": 1, "skills": {}}
    return load_json(DOCS_PATH)


def classify_docs(catalog: dict, docs: dict, hashes: dict[str, str]) -> tuple[list[str], list[str], list[str]]:
    """返回 (reusable, need_generate, invalid)."""
    reusable: list[str] = []
    need: list[str] = []
    invalid: list[str] = []
    existing = docs.get("skills") or {}
    for name, expected in hashes.items():
        entry = existing.get(name)
        if entry is None:
            need.append(name)
            continue
        errs = validate_doc_entry(name, entry, expected)
        if errs:
            invalid.append(name)
            need.append(name)
        else:
            reusable.append(name)
    return reusable, need, invalid


def status_cmd() -> None:
    catalog = load_catalog()
    validate_catalog(catalog)
    hashes = current_hashes(catalog)
    docs = load_docs()
    reusable, need, invalid = classify_docs(catalog, docs, hashes)
    print(f"总计 {len(hashes)} | 可复用 {len(reusable)} | 需生成 {len(need)} | 校验失败 {len(invalid)}")
    if need:
        print("NEED_GENERATE:")
        for n in need:
            print(f"  - {n}")
    else:
        print("NEED_GENERATE: (none)")
    # machine-readable sidecar for agents
    report = {
        "hashes": hashes,
        "reusable": reusable,
        "needGenerate": need,
        "invalid": invalid,
        "docsPath": str(DOCS_PATH.relative_to(ROOT)),
    }
    report_path = GENERATED_DIR / "status.json"
    save_json(report_path, report)
    print(f"status written: {report_path.relative_to(ROOT)}")
    if need:
        sys.exit(2)


def require_all_docs(catalog: dict, docs: dict, hashes: dict[str, str]) -> dict:
    skills_docs = docs.get("skills") or {}
    missing: list[str] = []
    errors: list[str] = []
    for name, expected in hashes.items():
        entry = skills_docs.get(name)
        if entry is None:
            missing.append(name)
            continue
        errs = validate_doc_entry(name, entry, expected)
        errors.extend(errs)
    if missing or errors:
        msg = []
        if missing:
            msg.append("缺少 AI 说明: " + ", ".join(missing))
        if errors:
            msg.append("无效说明:\n  " + "\n  ".join(errors))
        raise SystemExit("\n".join(msg))
    return skills_docs


def clear_skills_dir() -> None:
    if SKILLS_OUT.exists():
        shutil.rmtree(SKILLS_OUT)
    SKILLS_OUT.mkdir(parents=True, exist_ok=True)


def copy_skills(catalog: dict) -> dict[str, list[str]]:
    by_cat: dict[str, list[str]] = {c: [] for c in catalog["categories"]}
    for name, meta in sorted(catalog["skills"].items()):
        src = AGENTS_SKILLS / name
        for cat in meta["categories"]:
            dest = SKILLS_OUT / cat / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dest)
            by_cat[cat].append(name)
    return by_cat


def link_skills_sh(meta: dict) -> str:
    url = meta.get("skillsShUrl")
    if not url:
        return MISSING
    return f"[skills.sh]({url})"


def link_github(name: str, meta: dict, from_dir: Path) -> str:
    url = meta.get("githubUrl")
    if url:
        return f"[GitHub]({url})"
    target = AGENTS_SKILLS / name / "SKILL.md"
    rel = Path(os.path.relpath(target, from_dir))
    return f"[本仓库]({rel.as_posix()})"


def skill_path_in_category(cat: str, name: str) -> str:
    return f"`skills/{cat}/{name}/`"


def md_escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def write_category_readme(
    cat: str,
    cat_meta: dict,
    names: list[str],
    catalog: dict,
    skills_docs: dict,
) -> None:
    cat_dir = SKILLS_OUT / cat
    cat_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {cat_meta['title']}",
        "",
        cat_meta.get("description", ""),
        "",
        "> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。"
        "简介与详细说明由 AI 基于各 skill 的 `SKILL.md` 生成。",
        "",
        "## 总览",
        "",
        "| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in names:
        meta = catalog["skills"][name]
        doc = skills_docs[name]
        lines.append(
            "| {name} | {path} | {desc} | {sh} | {gh} |".format(
                name=f"`{name}`",
                path=skill_path_in_category(cat, name),
                desc=md_escape_cell(doc["summary"]),
                sh=link_skills_sh(meta),
                gh=link_github(name, meta, cat_dir),
            )
        )
    lines.extend(["", "## 详细介绍", ""])
    for name in names:
        doc = skills_docs[name]
        lines.extend(
            [
                f"### `{name}`",
                "",
                f"**路径**：{skill_path_in_category(cat, name)}",
                "",
                "#### 核心能力",
                "",
                doc["capabilities"].strip(),
                "",
                "#### 适用场景",
                "",
                doc["scenarios"].strip(),
                "",
                "#### 主要覆盖内容",
                "",
                doc["coverage"].strip(),
                "",
                "#### 注意事项",
                "",
                doc["notes"].strip(),
                "",
            ]
        )
    (cat_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_root_readme(catalog: dict, by_cat: dict[str, list[str]]) -> None:
    lines = [
        "# Skills 分类目录",
        "",
        "本目录是仓库的 **只读派生产物**：内容由 `.agents/skills`（经 `skills-lock.json` 更新）"
        "按 `skills-catalog.json` **全量清空后重建**；中文简介与详细说明由 AI 生成。",
        "",
        "## 约定",
        "",
        "- **真相源**：`.agents/skills/` + `skills-lock.json`",
        "- **分类元数据**：`skills-catalog.json`（不含中文文案）",
        "- **AI 说明缓存**：`.cursor/skills/sync-skills-catalog/generated/skill-docs.json`",
        "- **派生产物**：本目录 `skills/`（禁止手改）",
        "- **同步方式**：使用 `.cursor/skills/sync-skills-catalog/` 运维 skill",
        "- **第一期**：不提供 presets 预设包",
        "",
        "## 如何给新项目拷贝",
        "",
        "1. 打开对应分类目录，阅读总览表与详细介绍",
        "2. 将需要的 skill 文件夹复制到目标项目的 `.agents/skills/`",
        "3. 如目标项目使用 `skills-lock.json`，请按需补齐 lock 条目",
        "",
        "## 分类索引",
        "",
        "| 分类 | 说明 | Skill 数量 | 入口 |",
        "| --- | --- | ---: | --- |",
    ]
    for cat, cat_meta in catalog["categories"].items():
        names = by_cat.get(cat) or []
        if not names:
            continue
        lines.append(
            f"| `{cat}` | {cat_meta['title']} — {cat_meta.get('description', '')} "
            f"| {len(names)} | [README]({cat}/README.md) |"
        )
    lines.extend(
        [
            "",
            "## 维护",
            "",
            "```bash",
            "npx skills update -y   # 可选",
            "python3 .cursor/skills/sync-skills-catalog/scripts/sync.py status",
            "# 按运维 skill：为 NEED_GENERATE 列表生成/更新 skill-docs.json",
            "python3 .cursor/skills/sync-skills-catalog/scripts/sync.py render",
            "```",
            "",
        ]
    )
    (SKILLS_OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def render_cmd() -> None:
    if not AGENTS_SKILLS.is_dir():
        raise SystemExit(f"缺少源目录: {AGENTS_SKILLS}")
    catalog = load_catalog()
    validate_catalog(catalog)
    hashes = current_hashes(catalog)
    docs = load_docs()
    skills_docs = require_all_docs(catalog, docs, hashes)
    clear_skills_dir()
    by_cat = copy_skills(catalog)
    for cat, cat_meta in catalog["categories"].items():
        names = by_cat.get(cat) or []
        if not names:
            continue
        write_category_readme(cat, cat_meta, names, catalog, skills_docs)
    write_root_readme(catalog, by_cat)
    total_copies = sum(len(v) for v in by_cat.values())
    print(f"渲染完成: {len(catalog['skills'])} 个 skill，{total_copies} 份分类副本 → {SKILLS_OUT}")


def validate_cmd() -> None:
    catalog = load_catalog()
    validate_catalog(catalog)
    hashes = current_hashes(catalog)
    docs = load_docs()
    require_all_docs(catalog, docs, hashes)
    # README consistency if skills/ exists
    if SKILLS_OUT.is_dir():
        for cat, cat_meta in catalog["categories"].items():
            names = [
                n
                for n, m in catalog["skills"].items()
                if cat in m["categories"]
            ]
            if not names:
                continue
            readme = SKILLS_OUT / cat / "README.md"
            if not readme.is_file():
                raise SystemExit(f"缺少分类 README: {readme}")
            text = readme.read_text(encoding="utf-8")
            table_rows = sum(1 for n in names if f"`{n}`" in text.split("## 详细介绍")[0])
            detail_heads = sum(1 for n in names if f"### `{n}`" in text)
            if table_rows != len(names) or detail_heads != len(names):
                raise SystemExit(
                    f"{cat}: 表格行={table_rows} 详细章={detail_heads} 期望={len(names)}"
                )
    print("VALIDATE_OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="同步 .agents/skills 到分类化 skills/")
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=["status", "render", "validate"],
        help="status=列出需 AI 生成的 skill；render=校验说明并重建 skills/；validate=仅校验",
    )
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()
    if args.root is not None:
        global ROOT, CATALOG_PATH, AGENTS_SKILLS, SKILLS_OUT
        ROOT = args.root.resolve()
        CATALOG_PATH = ROOT / "skills-catalog.json"
        AGENTS_SKILLS = ROOT / ".agents" / "skills"
        SKILLS_OUT = ROOT / "skills"
    if args.command == "status":
        status_cmd()
    elif args.command == "render":
        render_cmd()
    else:
        validate_cmd()


if __name__ == "__main__":
    main()
