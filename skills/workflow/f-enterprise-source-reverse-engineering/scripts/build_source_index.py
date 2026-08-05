#!/usr/bin/env python3
"""Build an isolated, hash-backed JSONL source index for one project."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from common.core import atomic_write, ensure_outside_source, exclusive_lock, iter_source_files, read_jsonl, source_record, write_jsonl

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=("A", "B"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"repository root is not a directory: {root}")
    try:
        ensure_outside_source(args.workspace, root)
    except ValueError as exc:
        parser.error(str(exc))
    output = args.workspace / "indexes" / args.project / "source-index.jsonl"
    now = datetime.now(timezone.utc).isoformat()
    with exclusive_lock(output):
        old_rows = {row.get("relative_path"): row for row in read_jsonl(output)}
        rows = []
        changed_files = []
        reused_files = []
        deleted_files = []
        changed = unchanged = 0
        for path in iter_source_files(root):
            relative = path.relative_to(root).as_posix()
            old = old_rows.get(relative)
            stat = path.stat()
            if old and old.get("size_bytes") == stat.st_size and old.get("mtime_ns") == stat.st_mtime_ns:
                record = dict(old)
                record["last_indexed_at"] = now
                unchanged += 1
                reused_files.append(relative)
            else:
                record = source_record(args.project, root, path, old)
                record["first_indexed_at"] = record["first_indexed_at"] or now
                record["last_indexed_at"] = now
                changed += 1
                changed_files.append(relative)
            rows.append(record)
        current_paths = {row["relative_path"] for row in rows}
        for relative, old in old_rows.items():
            if relative not in current_paths:
                deleted = dict(old)
                deleted["analysis_status"] = "STALE"
                deleted["last_indexed_at"] = now
                notes = list(deleted.get("notes", []))
                if "file deleted" not in notes:
                    notes.append("file deleted")
                deleted["notes"] = notes
                rows.append(deleted)
                changed += 1
                deleted_files.append(relative)
        rows.sort(key=lambda row: row.get("relative_path", ""))
        write_jsonl(output, rows)
    manifest = args.workspace / "indexes" / args.project / "index-manifest.json"
    atomic_write(manifest, __import__("json").dumps({"project": args.project, "repository_root": str(root), "source_index_version": 1, "file_count": len(rows), "changed_or_deleted": changed, "unchanged_reused": unchanged, "content_read_files": sorted(changed_files), "reused_without_content_read": sorted(reused_files), "deleted_files": sorted(deleted_files), "updated_at": now}, ensure_ascii=False, indent=2) + "\n")
    print(f"INDEX_OK project={args.project} files={len(rows)} changed={changed} reused={unchanged} output={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
