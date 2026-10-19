#!/usr/bin/env python3
"""Small deterministic checks for the candidate scanner."""

from __future__ import annotations

import tempfile
from pathlib import Path

from scan_spacing import CHECKS, scan_file


FIXTURE = """
.mixedParent {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mixedChild {
  margin-bottom: 16px;
}

.noLayout {
  gap: 16px;
}

.alignment {
  margin-left: auto;
}

.validGrid {
  display: grid;
  gap: var(--ant-margin-lg);
}

.mobile {
  padding-bottom: calc(56px + 16px + env(safe-area-inset-bottom));
}

@media (min-width: 768px) {
  .responsive { padding: 24px; }
}
"""


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="spacing-scan-") as directory:
        path = Path(directory) / "fixture.module.css"
        path.write_text(FIXTURE, encoding="utf-8")
        results = scan_file(path, set(CHECKS))

    codes = [item.code for item in results]
    no_layout = [item for item in results if item.code == "SPACING-GAP-NO-LAYOUT"]
    assert len(no_layout) == 1 and ".noLayout" in no_layout[0].note
    assert "SPACING-HARDCODE" in codes
    assert "SPACING-MODULE-MARGIN" in codes
    assert "SPACING-SAFE-AREA-DUPLICATE" in codes
    assert "SPACING-BREAKPOINT-DUPLICATION" in codes
    assert all(".validGrid" not in item.note for item in no_layout)
    assert all("margin-left: auto" not in item.snippet for item in results)

    skill_root = Path(__file__).resolve().parent.parent
    rules = (skill_root / "references" / "audit-rules.md").read_text(encoding="utf-8")
    acceptance = (skill_root / "references" / "acceptance-scenarios.md").read_text(encoding="utf-8")
    report = (skill_root / "templates" / "spacing-audit-report.md").read_text(encoding="utf-8")
    for code in (
        "PAGE-START-BOUNDARY-001",
        "COMPOSITE-PADDING-001",
        "TOKEN-VALID-CONTRACT-UNVERIFIED",
    ):
        assert code in rules
        assert code in acceptance
    for evidence in ("Computed block-start", "Header bottom", "first-module top/left/right"):
        assert evidence in report

    print(f"PASS: {len(results)} scanner candidates; directional-contract rules and report evidence are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
