# Audit rules

## Stable finding codes

| Code | Typical severity | Meaning |
| --- | --- | --- |
| `SPACING-HARDCODE` | medium | Design spacing is a literal instead of a verified token. |
| `SPACING-ROOT-MARGIN` | medium | Reusable root decides external placement. |
| `SPACING-SECTION-MARGIN` | medium | Section-to-Section distance is child margin. |
| `SPACING-MODULE-MARGIN` | medium | Module-to-Module distance is child margin. |
| `SPACING-MIXED-GAP-MARGIN` | medium | One sibling relationship has parent gap and child margin. |
| `SPACING-GAP-NO-LAYOUT` | high | Gap has no flex/grid layout context. |
| `SPACING-DUPLICATE-PADDING` | medium | Multiple containers duplicate boundary padding. |
| `SPACING-NESTED-PAGE-CONTAINER` | high | Page container is used inside a nested host. |
| `SPACING-SAFE-AREA-MISSING` | high | Fixed UI can obscure content. |
| `SPACING-SAFE-AREA-DUPLICATE` | high | Multiple owners add the same safe area. |
| `SPACING-BOTTOM-NAV-OFFSET` | high | Bottom-nav dimension/offset is missing or inconsistent. |
| `SPACING-INLINE-STYLE` | low | Stable layout spacing is repeatedly inline. |
| `SPACING-TOKEN-MISUSE` | medium | Invalid or semantically incorrect Ant token. |
| `SPACING-CUSTOM-TOKEN-DUPLICATION` | medium | Custom scale duplicates Ant spacing. |
| `SPACING-BREAKPOINT-DUPLICATION` | medium | Breakpoint source is repeated. |
| `SPACING-BREAKPOINT-DRIFT` | high | Breakpoint values/semantics diverge. |
| `SPACING-MAX-WIDTH-INCONSISTENT` | medium | Page-local content widths conflict. |
| `SPACING-SPACE-FLEX-MISUSE` | low | Layout tool conflicts with responsibility. |
| `SPACING-LEGACY-ESCAPE` | medium | Compatibility hack leaks into business code. |
| `SPACING-DEEP-GAP-ASSUMPTION` | medium | Outer gap is expected to affect descendants. |
| `SPACING-COMPONENT-TOKEN-OVERRIDE` | medium | Ant internals are overridden without need/public API. |
| `HEADER-OVERLAY-001` | high | Page top padding displaces a first-screen Hero from beneath an initially transparent fixed/sticky Header and exposes an unintended background band. |
| `LAYOUT-CONTRACT-MISMATCH` | medium | A page uses a primitive or ownership model that conflicts with its evidenced page family. |
| `LAYOUT-OWNERSHIP-CONFLICT` | medium | A boundary, sibling gap, offset, or state relationship has duplicate or missing owners. |
| `LAYOUT-SURFACE-BOUNDARY` | high | A full-width Surface background is clipped or double-padded by a content boundary. |
| `LAYOUT-OVERLAP-REGRESSION` | high | Ordinary flow/gap removes or distorts an intentional overlap contract. |
| `LAYOUT-FIXED-HEADER-OFFSET` | high | Content below a fixed solid Header has a missing or duplicated offset. |
| `LAYOUT-STATE-STACK` | medium | State siblings rely on scattered child margins or inconsistent owners. |
| `LAYOUT-WRAPPER-WITHOUT-ROLE` | low | A wrapper owns no layout, background, accessibility, or state-group responsibility. |
| `LAYOUT-UNIVERSAL-PAGE-API` | medium | A universal page component mixes mutually exclusive contracts through boolean modes. |
| `PAGE-START-BOUNDARY-001` | high | A fixed-Header page's first business-module boundary is implicit, owned by the wrong layer, or conflicts with the same-family project contract. |
| `COMPOSITE-PADDING-001` | medium | A shorthand/four-value padding hides multiple semantic responsibilities and prevents reliable ownership tracing. |
| `TOKEN-VALID-CONTRACT-UNVERIFIED` | medium | The installed Ant Token is valid, but its fitness for the node's page-role contract has not been proven. |

Adjust severity to actual impact: `critical`, `high`, `medium`, `low`, or `info`.

For `HEADER-OVERLAY-001`, do not report an explicitly solid/in-flow Header or padding owned by a separate non-Hero content region. Record the exception and evidence in the audit.

Do not report different page values by themselves. First prove that they implement the same semantic responsibility in comparable page families. For layout-contract findings, include classification evidence, current owner, target owner, shared-primitive suitability, affected interactions, and regression checkpoints.

For PageContainer, `FixedHeaderContent`, ContentSection/List, `SurfaceSection`, and Drawer DetailPane findings, include authored declaration plus computed `padding-block-start`, both inline sides, and `padding-block-end`. When the declaration is composite, list the visual and semantic result of each axis; passing requires explicit ownership and a matching project contract, not merely a valid Token.

For fixed-Header findings, also include computed Header position/height, `header.bottom`, first-business-module top/left/right, their measured distance, the CSS owner of that distance, its semantic classification, and the same-family comparison. Keep bottom-navigation/safe-area reserve and Drawer/iframe/rich-text/Card internals out of page-start comparisons unless evidence proves shared responsibility.

## Required finding fields

Provide Issue ID, Severity, Rule, File, Line, Current Code, Problem, Impact, Recommended Fix, Current Owner, Target Owner, source declaration/computed value, relevant geometry, Auto-fix Safety (`safe`, `review-required`, `unsafe`), and Auto-fix Scope.

## Required summary

Report files scanned, total confirmed issues, counts by severity, safe-fix count, manual-review count, top issue types, top affected directories, and recommended remediation sequence. A scanner match count is not a confirmed issue count.
