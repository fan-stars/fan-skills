"""Compatibility exports for atomic and JSONL I/O."""
from .core import atomic_write, read_jsonl, write_jsonl

__all__ = ["atomic_write", "read_jsonl", "write_jsonl"]
