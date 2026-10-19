#!/usr/bin/env python3
"""Find spacing/layout candidates; semantic confirmation remains an agent task."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_EXTENSIONS = {
    ".css",
    ".less",
    ".scss",
    ".sass",
    ".styl",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
}
DEFAULT_EXCLUDES = {
    ".git",
    ".next",
    ".nuxt",
    "node_modules",
    "dist",
    "build",
    "coverage",
}
STYLE_EXTENSIONS = {".css", ".less", ".scss", ".sass", ".styl"}
CHECKS = {
    "hardcode",
    "layout-margin",
    "gap",
    "breakpoint",
    "safe-area",
    "custom-token",
    "inline-style",
}


@dataclass(frozen=True)
class Candidate:
    code: str
    severity: str
    file: str
    line: int
    check: str
    snippet: str
    note: str


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def iter_files(root: Path, excludes: set[str]) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in DEFAULT_EXTENSIONS:
            yield root
        return
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in DEFAULT_EXTENSIONS:
            continue
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            parts = path.parts
        if any(part in excludes for part in parts):
            continue
        yield path


def add_match(
    results: list[Candidate],
    *,
    code: str,
    severity: str,
    path: Path,
    text: str,
    match: re.Match[str],
    check: str,
    note: str,
) -> None:
    snippet = " ".join(match.group(0).strip().split())
    results.append(
        Candidate(
            code=code,
            severity=severity,
            file=str(path),
            line=line_number(text, match.start()),
            check=check,
            snippet=snippet[:240],
            note=note,
        )
    )


def scan_hardcodes(path: Path, text: str, results: list[Candidate]) -> None:
    pattern = re.compile(
        r"(?im)^\s*(?:margin(?:-(?:top|right|bottom|left|inline|block)(?:-(?:start|end))?)?"
        r"|padding(?:-(?:top|right|bottom|left|inline|block)(?:-(?:start|end))?)?"
        r"|gap|row-gap|column-gap)\s*:\s*[^;{}\n]*?(?<![\w.-])(?:[1-9]\d*(?:\.\d+)?|0?\.\d+)px\b[^;{}\n]*;?"
    )
    for match in pattern.finditer(text):
        add_match(
            results,
            code="SPACING-HARDCODE",
            severity="medium",
            path=path,
            text=text,
            match=match,
            check="hardcode",
            note="Candidate only: verify that the px value is design spacing, not a component dimension or required exception.",
        )


def scan_layout_margins(path: Path, text: str, results: list[Candidate]) -> None:
    pattern = re.compile(
        r"(?im)^\s*margin-(?:top|bottom|block(?:-(?:start|end))?)\s*:\s*[^;{}\n]+;?"
    )
    for match in pattern.finditer(text):
        add_match(
            results,
            code="SPACING-MODULE-MARGIN",
            severity="medium",
            path=path,
            text=text,
            match=match,
            check="layout-margin",
            note="Inspect the selector, component root, parent layout, and intent; alignment/internal/legacy margins may be valid.",
        )


def scan_gap_context(path: Path, text: str, results: list[Candidate]) -> None:
    # Deliberately shallow: nested preprocessor blocks and split selectors require semantic inspection.
    block_pattern = re.compile(r"(?s)([^{}]+)\{([^{}]*)\}")
    gap_pattern = re.compile(r"(?im)^\s*(?:gap|row-gap|column-gap)\s*:\s*[^;{}\n]+;?")
    layout_pattern = re.compile(r"(?im)^\s*display\s*:\s*(?:flex|inline-flex|grid|inline-grid)\b")
    for block in block_pattern.finditer(text):
        body = block.group(2)
        if not gap_pattern.search(body) or layout_pattern.search(body):
            continue
        gap = gap_pattern.search(body)
        assert gap is not None
        absolute_start = block.start(2) + gap.start()
        absolute_end = block.start(2) + gap.end()
        synthetic = re.match(r"[\s\S]+", text[absolute_start:absolute_end])
        assert synthetic is not None
        # Recreate an offset-aware match by searching the exact span in the full text.
        exact = re.compile(re.escape(text[absolute_start:absolute_end])).search(text, absolute_start)
        assert exact is not None
        selector = " ".join(block.group(1).strip().split())[-120:]
        add_match(
            results,
            code="SPACING-GAP-NO-LAYOUT",
            severity="high",
            path=path,
            text=text,
            match=exact,
            check="gap",
            note=f"Selector `{selector}` has gap without flex/grid in the same rule. Check cascade/composition before changing display.",
        )


def scan_breakpoints(path: Path, text: str, results: list[Candidate]) -> None:
    pattern = re.compile(r"@media[^\n{]*\((?:min|max)-width\s*:\s*[^)]*\)", re.IGNORECASE)
    for match in pattern.finditer(text):
        add_match(
            results,
            code="SPACING-BREAKPOINT-DUPLICATION",
            severity="medium",
            path=path,
            text=text,
            match=match,
            check="breakpoint",
            note="Inventory candidate: compare with Ant screen* and the repository's centralized breakpoint source; var() thresholds are invalid in ordinary media queries.",
        )


def scan_safe_area(path: Path, text: str, results: list[Candidate]) -> None:
    pattern = re.compile(r"env\(safe-area-inset-(?:top|right|bottom|left)(?:\s*,[^)]*)?\)", re.IGNORECASE)
    for match in pattern.finditer(text):
        add_match(
            results,
            code="SPACING-SAFE-AREA-DUPLICATE",
            severity="high",
            path=path,
            text=text,
            match=match,
            check="safe-area",
            note="Inventory candidate: trace ownership across page container, BottomNav, and sticky/fixed actions before deciding missing versus duplicate.",
        )


def scan_custom_tokens(path: Path, text: str, results: list[Candidate]) -> None:
    pattern = re.compile(r"(?im)^\s*--[\w-]*(?:space|spacing|gap)[\w-]*\s*:\s*[^;{}\n]+;?")
    for match in pattern.finditer(text):
        add_match(
            results,
            code="SPACING-CUSTOM-TOKEN-DUPLICATION",
            severity="medium",
            path=path,
            text=text,
            match=match,
            check="custom-token",
            note="Verify whether this duplicates Ant spacing; semantic component dimensions and non-duplicate constraints are valid.",
        )


def scan_inline_styles(path: Path, text: str, results: list[Candidate]) -> None:
    pattern = re.compile(
        r"\b(?:margin(?:Top|Right|Bottom|Left|Inline|Block)?|padding(?:Top|Right|Bottom|Left|Inline|Block)?|gap|rowGap|columnGap)"
        r"\s*:\s*(?:[1-9]\d*(?:\.\d+)?|['\"][^'\"]*(?:px|rem)[^'\"]*['\"])",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        add_match(
            results,
            code="SPACING-INLINE-STYLE",
            severity="low",
            path=path,
            text=text,
            match=match,
            check="inline-style",
            note="Verify this is stable layout spacing rather than a dynamic/third-party calculation before migrating to scoped styles or tokens.",
        )


def scan_file(path: Path, checks: set[str]) -> list[Candidate]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    results: list[Candidate] = []
    if path.suffix.lower() in STYLE_EXTENSIONS:
        if "hardcode" in checks:
            scan_hardcodes(path, text, results)
        if "layout-margin" in checks:
            scan_layout_margins(path, text, results)
        if "gap" in checks:
            scan_gap_context(path, text, results)
        if "breakpoint" in checks:
            scan_breakpoints(path, text, results)
        if "custom-token" in checks:
            scan_custom_tokens(path, text, results)
    if "safe-area" in checks:
        scan_safe_area(path, text, results)
    if path.suffix.lower() in {".ts", ".tsx", ".js", ".jsx"} and "inline-style" in checks:
        scan_inline_styles(path, text, results)
    return results


def parse_checks(value: str) -> set[str]:
    if value == "all":
        return set(CHECKS)
    requested = {part.strip() for part in value.split(",") if part.strip()}
    unknown = requested - CHECKS
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown checks: {', '.join(sorted(unknown))}")
    return requested


def render_markdown(root: Path, files_scanned: int, results: Sequence[Candidate]) -> str:
    counts: dict[str, int] = {}
    for item in results:
        counts[item.code] = counts.get(item.code, 0) + 1
    lines = [
        "# Spacing scanner candidates",
        "",
        f"- Root: `{root}`",
        f"- Files scanned: {files_scanned}",
        f"- Candidate matches: {len(results)}",
        "- Warning: every match requires DOM/CSS/token semantic confirmation.",
        "",
        "## Candidate counts",
        "",
    ]
    lines.extend(f"- `{code}`: {count}" for code, count in sorted(counts.items()))
    lines.extend(["", "## Candidates", ""])
    for index, item in enumerate(results, start=1):
        lines.extend(
            [
                f"### {index}. `{item.code}` candidate",
                "",
                f"- Severity hint: {item.severity}",
                f"- File: `{item.file}:{item.line}`",
                f"- Check: `{item.check}`",
                f"- Snippet: `{item.snippet.replace('`', '\\`')}`",
                f"- Follow-up: {item.note}",
                "",
            ]
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".", help="File or directory to scan")
    parser.add_argument(
        "--checks",
        default="all",
        type=parse_checks,
        help="all or comma-separated: " + ",".join(sorted(CHECKS)),
    )
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", help="Write output to this file instead of stdout")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Additional directory basename to exclude (repeatable)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).resolve()
    if not root.exists():
        raise SystemExit(f"path does not exist: {root}")
    excludes = DEFAULT_EXCLUDES | set(args.exclude)
    files = sorted(iter_files(root, excludes))
    results = [candidate for path in files for candidate in scan_file(path, args.checks)]
    results.sort(key=lambda item: (item.file, item.line, item.code))
    if args.format == "json":
        payload = {
            "root": str(root),
            "files_scanned": len(files),
            "candidate_count": len(results),
            "semantic_confirmation_required": True,
            "candidates": [asdict(item) for item in results],
        }
        output = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        output = render_markdown(root, len(files), results)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
