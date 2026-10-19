# Acceptance scenarios

Use these scenarios to forward-test semantic reasoning. Scanner output alone is insufficient.

1. Parent flex column with `gap: 16px`; direct child has `margin-bottom: 16px` → confirm `SPACING-MIXED-GAP-MARGIN` and prefer parent gap.
2. Parent has `gap: 16px` without flex/grid → candidate `SPACING-GAP-NO-LAYOUT`; inspect cascade and DOM before adding layout.
3. `.card { margin-bottom: 16px; }` → inspect parent and role before deciding whether it is layout margin.
4. `.action { margin-left: auto; }` → classify as valid alignment margin when used for flex alignment.
5. Drawer → PageContainer → Content → flag potential nested/double padding and trace the actual padding chain.
6. Mobile `calc(56px + 16px + env(...))` → centralize 56px as BottomNav dimension, replace semantic 16px with a verified Ant token, preserve `env()`, and ensure safe area is counted once.
7. Grid ModuleList with `gap: var(--ant-margin-lg)` → valid when the variable exists; the margin token supplies a size, not a margin property.
8. Outer ModuleList → Module → inner modules → outer gap cannot govern inner module siblings; require an inner layout owner.
9. Ant Form.Item default margin → do not mechanically flag; prefer installed component-token behavior for Form internals.
10. Card component token differs from global baseline → do not force an override solely for numeric uniformity.
11. A transparent H5 Header overlays a Contact Hero. Replacing an unresolved `--ant-layout-header-height` declaration with a page-local inline `64px` offset creates a blank first-screen band of the same height → confirm `HEADER-OVERLAY-001`; preserve the failed declaration's original computed-value semantics instead of treating the edit as an equivalent substitution.

## Cross-page layout contracts

12. A transparent Header overlays the first-screen Hero → classify the page contract before applying ordinary Section flow; accept `hero.top ≈ 0` and preserve the existing Header/Hero checks.
13. Several peer Sections share one background → let their SectionList parent own the only inter-Section gap; child roots must not add external block margins.
14. A full-width colored Surface alternates with constrained content → keep the Surface background outside the inline-safe-area boundary and constrain only its inner content.
15. A Hero and quick-entry region intentionally overlap → record an `OverlapLayer`; do not let SectionList flow or gap remove the overlap.
16. A fixed solid Header precedes workflow content → use one `FixedHeaderContent` owner and verify the content receives exactly one offset.
17. Loading, ready, empty, and notice content are direct state siblings → let `StateStack` own their relationship and remove state-root layout margins only after confirming equivalence.
18. Validate every migrated contract at one PC and one H5 target → record computed padding, direct-sibling gap, background boundaries, Header/Hero or fixed-header geometry, critical anchors, and Drawer/overlap/state interactions in scope.

## Directional padding and page-start contracts

19. A project Profile maps H5 content inline inset to `--ant-padding` (`16px`) and fixed-workflow page start to `--ant-padding-lg` (`24px`). A fixed solid Header ends at `y = 64`, while the first business module begins at `y = 72` because page `padding-block-start` uses valid `--ant-padding-xs` → report `PAGE-START-BOUNDARY-001`; also report `TOKEN-VALID-CONTRACT-UNVERIFIED` until the Token-to-role contract is checked. Do not compare the 8px page-start value with the 16px inline inset merely because both are padding.
20. A mobile page declares `padding: var(--ant-padding-xs) var(--ant-padding) var(--ant-padding-xl)`: block start is the fixed-Header page boundary, inline is content inset, and block end reserves navigation/safe area → report `COMPOSITE-PADDING-001`, show every computed axis and geometry, and recommend explicit logical-axis declarations with separate owners.
21. A Drawer DetailPane and ordinary page content both compute to `16px` inline padding → do not infer shared ownership or a common primitive; the Drawer value is an internal contract and the page value is a content-boundary contract.
22. An H5 audit has only source declarations and scanner candidates, with no browser session → mark Header bottom, first-module bounds, computed padding/gap, background, and safe-area conclusions blocked/provisional; do not report visual validation as passed.
