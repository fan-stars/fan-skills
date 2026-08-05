#!/usr/bin/env python3
"""Extract route declarations as candidates; framework certainty is explicit."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import atomic_write, ensure_outside_source, exclusive_lock, load_isolated_source_index, read_project_jsonl, text_lines, write_jsonl

PATTERNS = [
    ("laravel", re.compile(r"Route::(?:get|post|put|patch|delete|match|any)\s*\(\s*['\"]([^'\"]+)['\"]")),
    ("thinkphp", re.compile(r"Route::(?:rule|get|post|put|delete)\s*\(\s*['\"]([^'\"]+)['\"]")),
]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"route root is not a directory: {args.root}")
    try:
        ensure_outside_source(args.workspace, args.root)
    except ValueError as exc:
        parser.error(str(exc))
    output = args.workspace / "indexes" / args.project / "routes.jsonl"
    manifest = args.workspace / "indexes" / args.project / "route-manifest.json"
    try:
        source = load_isolated_source_index(args.workspace, args.project, args.root)
    except ValueError as exc:
        parser.error(str(exc))
    with exclusive_lock(output):
        old_by_file = {}
        for row in read_project_jsonl(output, args.project): old_by_file.setdefault(row["file"], []).append(row)
        old_hashes = json.loads(manifest.read_text(encoding="utf-8")).get("file_hashes", {}) if manifest.exists() else {}
        records = []; parsed = reused = 0; current_hashes = {}; parsed_files = []; reused_files = []
        for source_row in source:
            path = Path(source_row.get("absolute_path", ""))
            if source_row.get("language") != "PHP" or not path.is_file(): continue
            relative = source_row["relative_path"]; digest = source_row["sha256"]; current_hashes[relative] = digest
            if old_hashes.get(relative) == digest:
                records.extend(old_by_file.get(relative, [])); reused += 1; reused_files.append(relative); continue
            parsed += 1; parsed_files.append(relative); lines = text_lines(path)
            imports = {value.split("\\")[-1]: value for value in re.findall(r"^\s*use\s+([^;]+);", "\n".join(lines), re.M)}
            for number, line in enumerate(lines, 1):
                for framework, pattern in PATTERNS:
                    match = pattern.search(line)
                    if not match: continue
                    method = re.search(r"Route::(get|post|put|patch|delete|match|any|rule)", line, re.I)
                    handler = re.search(r"\[\s*([A-Za-z_\\][A-Za-z0-9_\\]*)::class\s*,\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\]", line)
                    controller = imports.get(handler.group(1).split("\\")[-1], handler.group(1).lstrip("\\")) if handler else None
                    action = handler.group(2) if handler else None
                    records.append({"project": args.project, "file": relative, "file_sha256": digest, "start_line": number, "end_line": number, "framework": framework, "method": (method.group(1).upper() if method else "UNKNOWN"), "path": match.group(1), "controller": controller, "action": action, "classification": "CANDIDATE", "confidence": "MEDIUM", "notes": ["轻量正则候选；需结合路由框架和控制器验证"]})
                    break
        records.sort(key=lambda row: (row["file"], row["start_line"]))
        write_jsonl(output, records)
        atomic_write(manifest, json.dumps({"project": args.project, "file_hashes": current_hashes, "content_read_files": sorted(parsed_files), "reused_without_content_read": sorted(reused_files)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"ROUTES_OK project={args.project} count={len(records)} parsed={parsed} reused={reused} output={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
