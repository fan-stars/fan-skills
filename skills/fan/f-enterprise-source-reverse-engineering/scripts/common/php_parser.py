"""Conservative PHP parser facade; callers must treat output as candidates."""
from .core import extract_php_symbols

PARSER_LIMITATION = "轻量正则无法覆盖 PHP 动态语法、属性钩子和复杂嵌套；必须人工复核。"

__all__ = ["extract_php_symbols", "PARSER_LIMITATION"]
