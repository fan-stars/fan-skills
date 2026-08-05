"""Index store facade with project isolation."""
from .core import read_jsonl, write_jsonl

def ensure_project(project: str) -> None:
    if project not in {"A", "B"}:
        raise ValueError("project must be A or B; cross-project facts belong only in comparison")

__all__ = ["read_jsonl", "write_jsonl", "ensure_project"]
