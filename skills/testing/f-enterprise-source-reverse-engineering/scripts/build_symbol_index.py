#!/usr/bin/env python3
"""Extract conservative PHP symbol candidates with line ranges."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import atomic_write, exclusive_lock, extract_php_symbols, load_isolated_source_index, read_project_jsonl, write_jsonl

SYMBOL_PARSER_VERSION = 2

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    try:
        rows = load_isolated_source_index(args.workspace, args.project)
    except ValueError as exc:
        parser.error(str(exc))
    output = args.workspace / "indexes" / args.project / "symbol-index.jsonl"
    manifest = args.workspace / "indexes" / args.project / "symbol-manifest.json"
    with exclusive_lock(output):
        old_manifest = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
        old_hashes = old_manifest.get("file_hashes", {}) if old_manifest.get("parser_version") == SYMBOL_PARSER_VERSION else {}
        old_by_file: dict[str, list[dict]] = {}
        for record in read_project_jsonl(output, args.project):
            old_by_file.setdefault(record.get("file", ""), []).append(record)
        records = []
        parsed = reused = 0
        parsed_files = []
        reused_files = []
        for row in rows:
            path = Path(row.get("absolute_path", ""))
            if row.get("language") != "PHP" or not path.is_file():
                continue
            old = old_by_file.get(row["relative_path"], [])
            if old_hashes.get(row["relative_path"]) == row.get("sha256"):
                records.extend(old)
                reused += 1
                reused_files.append(row["relative_path"])
            else:
                records.extend(extract_php_symbols(path, args.project, Path(row["repository_root"])))
                parsed += 1
                parsed_files.append(row["relative_path"])
        known = {record["fully_qualified_name"] for record in records}
        classes = {record["fully_qualified_name"] for record in records if record.get("symbol_type") in {"class", "interface", "trait"}}
        class_short = {}
        for name in classes:
            class_short.setdefault(name.split("\\")[-1], []).append(name)
        short = {}
        for name in known:
            short.setdefault(name.split("\\")[-1], []).append(name)
        for record in records:
            resolved = []
            for call in record.get("calls", []):
                if call in known:
                    resolved.append(call)
                else:
                    candidates = short.get(call.split("\\")[-1], [])
                    if len(candidates) == 1:
                        resolved.append(candidates[0])
                        continue
                    target, separator, method = call.rpartition("::")
                    class_candidates = class_short.get(target.split("\\")[-1], []) if separator else []
                    resolved.append(f"{class_candidates[0]}::{method}" if len(class_candidates) == 1 else call)
            record["calls"] = sorted(set(resolved))
            record["called_by"] = []
        by_name = {record["fully_qualified_name"]: record for record in records}
        for caller in records:
            for call in caller.get("calls", []):
                if call in by_name:
                    by_name[call]["called_by"].append(caller["fully_qualified_name"])
        for record in records:
            record["called_by"] = sorted(set(record["called_by"]))
        records.sort(key=lambda row: (row.get("file", ""), row.get("start_line", 0), row.get("fully_qualified_name", "")))
        write_jsonl(output, records)
        atomic_write(manifest, json.dumps({"project": args.project, "parser_version": SYMBOL_PARSER_VERSION, "file_hashes": {row["relative_path"]: row["sha256"] for row in rows if row.get("language") == "PHP" and Path(row.get("absolute_path", "")).is_file()}, "content_read_files": sorted(parsed_files), "reused_without_content_read": sorted(reused_files)}, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"SYMBOL_INDEX_OK project={args.project} symbols={len(records)} parsed={parsed} reused={reused} output={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
