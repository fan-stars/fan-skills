#!/usr/bin/env python3
"""Extract CREATE TABLE definitions and column/index hints without a SQL parser."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import atomic_write, ensure_outside_source, exclusive_lock, load_isolated_source_index, read_project_jsonl, text_lines, write_jsonl

TABLE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"]?([A-Za-z0-9_.$-]+)", re.I)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error(f"SQL root is not a directory: {args.root}")
    try:
        ensure_outside_source(args.workspace, args.root)
    except ValueError as exc:
        parser.error(str(exc))
    output = args.workspace / "indexes" / args.project / "table-index.jsonl"
    manifest = args.workspace / "indexes" / args.project / "table-manifest.json"
    try:
        source = load_isolated_source_index(args.workspace, args.project)
    except ValueError as exc:
        parser.error(str(exc))
    indexed_root = Path(source[0]["repository_root"]).resolve()
    sql_root = args.root.resolve()
    if sql_root != indexed_root and indexed_root not in sql_root.parents:
        parser.error(f"SQL root is outside indexed project root: {indexed_root}")
    with exclusive_lock(output):
        old_by_file = {}
        for row in read_project_jsonl(output, args.project): old_by_file.setdefault(row["file"], []).append(row)
        old_hashes = json.loads(manifest.read_text(encoding="utf-8")).get("file_hashes", {}) if manifest.exists() else {}
        rows = []; parsed = reused = 0; current_hashes = {}; parsed_files = []; reused_files = []
        for source_row in source:
            path = Path(source_row.get("absolute_path", ""))
            if source_row.get("language") != "SQL" or not path.is_file() or (path.resolve() != sql_root and sql_root not in path.resolve().parents): continue
            relative = source_row["relative_path"]; digest = source_row["sha256"]; current_hashes[relative] = digest
            if old_hashes.get(relative) == digest:
                rows.extend(old_by_file.get(relative, [])); reused += 1; reused_files.append(relative); continue
            parsed += 1; parsed_files.append(relative)
            for number, line in enumerate(text_lines(path), 1):
                match = TABLE.search(line)
                if match: rows.append({"project": args.project, "table": match.group(1), "file": relative, "file_sha256": digest, "start_line": number, "end_line": number, "columns": [], "primary_key": [], "unique_keys": [], "indexes": [], "classification": "FACT", "confidence": "HIGH"})
        rows.sort(key=lambda row: (row["file"], row["start_line"]))
        write_jsonl(output, rows)
        atomic_write(manifest, json.dumps({"project": args.project, "file_hashes": current_hashes, "content_read_files": sorted(parsed_files), "reused_without_content_read": sorted(reused_files)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"SQL_TABLES_OK project={args.project} count={len(rows)} parsed={parsed} reused={reused} output={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
