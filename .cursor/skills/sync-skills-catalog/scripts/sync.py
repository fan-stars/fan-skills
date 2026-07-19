#!/usr/bin/env python3
"""从 .agents/skills 按 skills-catalog.json 全量重建分类化 skills/ 并生成中文 README。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# .cursor/skills/sync-skills-catalog/scripts/sync.py → 仓库根
ROOT = Path(__file__).resolve().parents[4]
CATALOG_PATH = ROOT / "skills-catalog.json"
AGENTS_SKILLS = ROOT / ".agents" / "skills"
SKILLS_OUT = ROOT / "skills"
MISSING = "暂无"


def load_catalog() -> dict:
    if not CATALOG_PATH.is_file():
        raise SystemExit(f"缺少 catalog: {CATALOG_PATH}")
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def validate(catalog: dict) -> None:
    agents = {p.name for p in AGENTS_SKILLS.iterdir() if p.is_dir()} if AGENTS_SKILLS.is_dir() else set()
    skills = catalog.get("skills", {})
    categories = catalog.get("categories", {})
    names = set(skills)
    if names != agents:
        only_cat = sorted(names - agents)
        only_agents = sorted(agents - names)
        raise SystemExit(
            "catalog 与 .agents/skills 不一致:\n"
            f"  catalog 多出: {only_cat}\n"
            f"  agents 多出: {only_agents}"
        )
    for name, meta in skills.items():
        cats = meta.get("categories") or []
        if not cats:
            raise SystemExit(f"{name} 缺少 categories")
        if not (meta.get("descriptionZh") or "").strip():
            raise SystemExit(f"{name} 缺少 descriptionZh")
        for c in cats:
            if c not in categories:
                raise SystemExit(f"{name} 引用未知分类: {c}")


def clear_skills_dir() -> None:
    if SKILLS_OUT.exists():
        shutil.rmtree(SKILLS_OUT)
    SKILLS_OUT.mkdir(parents=True, exist_ok=True)


def copy_skills(catalog: dict) -> dict[str, list[str]]:
    """返回 category -> skill names。"""
    by_cat: dict[str, list[str]] = {c: [] for c in catalog["categories"]}
    for name, meta in sorted(catalog["skills"].items()):
        src = AGENTS_SKILLS / name
        if not src.is_dir():
            raise SystemExit(f"源目录不存在: {src}")
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


def write_category_readme(cat: str, cat_meta: dict, names: list[str], catalog: dict) -> None:
    cat_dir = SKILLS_OUT / cat
    cat_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {cat_meta['title']}",
        "",
        cat_meta.get("description", ""),
        "",
        "> 本目录由同步脚本从 `.agents/skills` 全量生成，请勿手改。",
        "",
        "| Skill 名称 | 路径 | 简介 | skills.sh | GitHub |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name in names:
        meta = catalog["skills"][name]
        lines.append(
            "| {name} | {path} | {desc} | {sh} | {gh} |".format(
                name=f"`{name}`",
                path=skill_path_in_category(cat, name),
                desc=meta["descriptionZh"].replace("|", "\\|"),
                sh=link_skills_sh(meta),
                gh=link_github(name, meta, cat_dir),
            )
        )
    lines.append("")
    (cat_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_root_readme(catalog: dict, by_cat: dict[str, list[str]]) -> None:
    lines = [
        "# Skills 分类目录",
        "",
        "本目录是仓库的 **只读派生产物**：内容由 `.agents/skills`（经 `skills-lock.json` 更新）"
        "按 `skills-catalog.json` **全量清空后重建**。",
        "",
        "## 约定",
        "",
        "- **真相源**：`.agents/skills/` + `skills-lock.json`",
        "- **派生产物**：本目录 `skills/`（禁止手改）",
        "- **多分类**：同一 skill 可出现在多个分类下（完整副本）",
        "- **同步方式**：使用 `.cursor/skills/sync-skills-catalog/` 运维 skill（该 skill 不会同步到本目录）",
        "- **第一期**：不提供按框架的 presets 预设包；请按分类手工拷贝所需 skill",
        "",
        "## 如何给新项目拷贝",
        "",
        "1. 打开对应分类目录（或本页下方链接）",
        "2. 将需要的 skill 文件夹复制到目标项目的 `.agents/skills/`（或该项目约定的 skills 目录）",
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
            "# 1) 按 lock 更新 .agents/skills（可选）",
            "npx skills update -y",
            "",
            "# 2) 全量重建 skills/ 与中文 README",
            "python3 .cursor/skills/sync-skills-catalog/scripts/sync.py",
            "```",
            "",
        ]
    )
    (SKILLS_OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def sync() -> None:
    if not AGENTS_SKILLS.is_dir():
        raise SystemExit(f"缺少源目录: {AGENTS_SKILLS}")
    catalog = load_catalog()
    validate(catalog)
    clear_skills_dir()
    by_cat = copy_skills(catalog)
    for cat, cat_meta in catalog["categories"].items():
        names = by_cat.get(cat) or []
        if not names:
            continue
        write_category_readme(cat, cat_meta, names, catalog)
    write_root_readme(catalog, by_cat)
    total_copies = sum(len(v) for v in by_cat.values())
    print(f"同步完成: {len(catalog['skills'])} 个 skill，{total_copies} 份分类副本 → {SKILLS_OUT}")


def main() -> None:
    parser = argparse.ArgumentParser(description="同步 .agents/skills 到分类化 skills/")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="仓库根目录（默认根据脚本位置推断）",
    )
    args = parser.parse_args()
    if args.root is not None:
        global ROOT, CATALOG_PATH, AGENTS_SKILLS, SKILLS_OUT
        ROOT = args.root.resolve()
        CATALOG_PATH = ROOT / "skills-catalog.json"
        AGENTS_SKILLS = ROOT / ".agents" / "skills"
        SKILLS_OUT = ROOT / "skills"
    sync()


if __name__ == "__main__":
    main()
