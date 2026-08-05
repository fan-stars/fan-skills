"""Path helpers shared by consumers embedding the scripts."""
from pathlib import Path

def project_index_dir(workspace: Path, project: str) -> Path:
    if project not in {"A", "B"}:
        raise ValueError("project must be A or B")
    return workspace / "indexes" / project
