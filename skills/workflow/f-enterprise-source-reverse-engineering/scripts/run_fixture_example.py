#!/usr/bin/env python3
"""Run the bundled PHP fixture through the real pipeline and print query results."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MODULE_FILES = (
    "routes/api.php", "app/Http/Controllers/ProductController.php", "app/Http/Requests/ProductRequest.php",
    "app/Services/ProductService.php", "app/Services/InventoryService.php", "app/Repositories/ProductRepository.php",
    "app/Models/Product.php", "app/Jobs/SyncProductJob.php", "database/products.sql", "database/product_skus.sql",
)

def execute(script_dir: Path, script: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run([sys.executable, str(script_dir / script), *arguments], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"{script} failed ({result.returncode}): {result.stderr or result.stdout}")
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    skill = Path(__file__).parents[1]
    script_dir = skill / "scripts"
    with tempfile.TemporaryDirectory(prefix="f-esre-example-") as directory:
        root = Path(directory) / "project-a"
        workspace = Path(directory) / "workspace"
        shutil.copytree(skill / "tests/fixtures/mini-php-project", root)
        execute(script_dir, "build_source_index.py", ["--project", "A", "--root", str(root), "--workspace", str(workspace)])
        index = workspace / "indexes/A/source-index.jsonl"
        for file_name in MODULE_FILES:
            execute(script_dir, "update_module_ownership.py", ["--index", str(index), "--file", file_name, "--module", "product", "--role", "PRIMARY"])
        execute(script_dir, "run_analysis.py", ["--project", "A", "--module", "product", "--root", str(root), "--sql-root", str(root / "database"), "--workspace", str(workspace), "--analysis-run-id", "A-product-20260805-001"])
        callers = execute(script_dir, "query_indexes.py", ["--project", "A", "--workspace", str(workspace), "--callers-of", r"App\Repositories\ProductRepository::create"])
        rules = execute(script_dir, "query_indexes.py", ["--project", "A", "--workspace", str(workspace), "--business-rule", "DRAFT"])
        gate = json.loads((workspace / "reports/A/product-quality-gates.json").read_text(encoding="utf-8"))
        print(json.dumps({"callers": json.loads(callers.stdout), "rules": json.loads(rules.stdout), "quality_gate": {"status": gate["status"], "passed": gate["passed_count"], "total": gate["gate_count"]}}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
