# Spacing governance audit

## Executive summary

- Scope:
- Mode:
- Read-only:
- Files scanned:
- Confirmed issues:
- Severity: critical 0 / high 0 / medium 0 / low 0 / info 0
- Safe auto-fixes:
- Manual review:
- Top issue types:
- Top affected directories:
- Recommended remediation order:

## Spacing architecture

```text
Page
├── Hero / OverlapLayer / FixedHeaderContent (when contracted)
└── PageSectionList
    ├── ContentSectionList
    │   └── Section
    └── SurfaceSection
        └── ModuleList / ModuleGrid
            └── Module
                └── Content / ContentStack / StateStack
                    └── Element
```

Describe actual containers, padding ownership, direct-sibling gaps, responsive branches, and safe-area responsibility.

## Page layout contract

- Page classification and evidence:
- Current primitive composition:
- Target primitive composition:
- Padding Chain:
- Background chain:
- Direct-sibling gap owners:
- PC/H5 installed-Ant Token mapping:
- Header/Hero, fixed Header, safe area, overlap, Surface, Drawer, iframe, virtual-list, or other exceptions:

## Directional padding contract

| Page/scope | Node/role | Source declaration | Computed block-start | Computed inline-start/end | Computed block-end | Current owner/semantic | Target contract | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |

## Fixed Header page-start geometry

- Header computed position/top/bottom/height:
- First business module top/left/right:
- Header bottom → first module top distance:
- Distance CSS owner and semantic classification:
- Same-family Layout Contract baseline and result:
- Page block-end/navigation/safe-area owner (audited separately):

## Header overlay map

- Header position and stacking:
- Initial state class/background:
- Scrolled state and trigger:
- Page/Hero intended relationship:
- Top-offset/header-height/safe-area variable scope chain:
- Unresolved variables and resulting computed behavior:
- `HEADER-OVERLAY-001` exception, if any:

## Findings

### [SPACING-RULE-001]

- Severity:
- Rule:
- File:
- Line:
- Current code:
- Source declaration and browser-computed value:
- Actual geometry (previous bottom / next top / actual gap or relevant bounds):
- Problem:
- Impact:
- Recommended fix:
- Current owner:
- Target owner:
- Shared-primitive suitability and implementation form:
- Auto-fix safety: safe / review-required / unsafe
- Auto-fix scope:
- Affected interactions:
- Regression checkpoints:

## Validation and limitations

- Scanner commands:
- Semantic checks performed:
- PC first-screen geometry/background:
- H5 first-screen geometry/background:
- H5 Header bottom; Page/Content directional padding; first-module top/left/right:
- Computed display/gap and direct-sibling geometry:
- Full-width Surface/background continuity:
- Bottom navigation/safe-area bounds and owner:
- Critical anchors, overlap, states, Drawer, and scrolling interactions:
- Browser visual verification: passed / failed / blocked
- Files/paths excluded:
- Assumptions requiring confirmation:
