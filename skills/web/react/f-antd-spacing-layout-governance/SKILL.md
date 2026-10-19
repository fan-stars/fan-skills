---
name: f-antd-spacing-layout-governance
description: Audit, review, migrate, and continuously govern spacing and cross-page layout contracts in real React projects that use Ant Design 6, including page-family classification, spacing ownership, full-width surfaces, intentional overlap, fixed or transparent headers, state layouts, safe areas, and CSS-variable scope. Use for whole-project, page, component, PR, token, gap, margin, container, responsive, mobile, header, Hero, or breakpoint audits; gradual remediation; layout generation; and new feature development across PC and H5. Default audits to read-only and modify source only when the user explicitly authorizes implementation.
---

# Govern Ant Design spacing and layout

Treat this as an execution skill, not a document generator. Discover the project, reconstruct layout semantics, report traceable findings, and make only authorized, scoped changes.

## Enforce the invariant

Apply these rules in priority order:

1. Use `padding` for container boundaries.
2. Use parent `gap` for spacing between direct siblings.
3. Use Ant Design component tokens for Ant component internals.
4. Use `padding` plus internal parent `gap` inside custom business components.
5. Keep reusable Section/Module roots free of page-layout `margin-top`, `margin-bottom`, and `margin-block` by default.
6. Never control one sibling relationship with both parent gap and child layout margin.
7. Treat Ant Design tokens from the installed version as the only design-value source. Do not create a duplicate spacing scale.

Reuse an Ant margin token as a **size** for CSS `gap` when no dedicated gap token exists. Do not confuse the token name with the CSS property.

## Start with repository instructions

Before analyzing or changing a repository:

1. Read every applicable `AGENTS.md`, starting at the workspace root and ending with the closest file for the target.
2. Respect writable/read-only directory boundaries, required approval gates, framework-version rules, and validation commands.
3. Inspect the current implementation before reading reference projects. Never use reference code as a pixel-copy target.
4. If the repository requires user confirmation before UI changes, stop after the proposed component/layout strategy and wait for that confirmation.

Repository instructions override generic templates in this skill.

## Map intent to a mode

Map natural-language requests to one or more modes:

- `init`: discover the project and create/update a spacing profile.
- `audit`: whole-scope, read-only audit.
- `audit-page`, `audit-component`: reconstruct semantic hierarchy and audit the target.
- `audit-spacing`, `audit-gap`, `audit-margin`, `audit-container`, `audit-responsive`, `audit-mobile`, `audit-token`: focused audits.
- `review`: inspect only the changed lines/diff for newly introduced issues.
- `migrate`, `migrate-page`, `migrate-module`: make authorized, incremental changes and regress them.
- `generate-layout`: design or implement reusable layout primitives after checking existing equivalents.
- `explain`: explain a rule or finding without changing files.

Default every audit and review to read-only. Treat words such as “检查、审计、review、看看、分析” as read-only. Treat “修复、整改、修改、实现、开发” as implementation authorization only for the named scope; still obey repository-specific confirmation gates.

## Discover the project

On first use, inspect:

- package manager, `package.json`, installed Ant Design and React versions, framework/build tool, and existing validation scripts;
- all applicable agent/repository instructions;
- CSS Modules, Less/Sass/PostCSS, Tailwind, CSS-in-JS, global CSS, `ConfigProvider`, `theme`, and `cssVar` configuration;
- page/layout/container/header/footer/bottom-nav/sticky-action implementations;
- Card, Form, Table, Modal, Drawer, Tabs, responsive utilities, breakpoint sources, spacing utilities, and legacy adapters;
- existing project documentation and spacing audits.

Verify installed Ant APIs/tokens using the repository's required local commands or local package sources. Never rely on a remembered token such as a fictional `marginMD`.

When authorized to initialize documentation, create or update the repository-approved equivalent of:

```text
.spacing-governance/
├── profile.md
├── decisions.md
└── audit-baseline.md
```

Record how the project uses Ant tokens; do not redefine token values. Start from `templates/spacing-profile.md`.

## Reconstruct semantics before judging CSS

Classify by role, not filename:

```text
Page → Section → Module → Content → Element
```

Identify PageContainer/ContentContainer, SectionList, ModuleList/ModuleGrid, nested containers, and direct-sibling relationships. A ProductCard or Table may be a Module; a Toolbar is often Content. Outer gap never governs nested descendants.

For a page with a Header and first-screen Hero, also reconstruct `Header → Page → Hero`: determine whether the Header participates in flow or overlays content and whether the Hero is intended to begin at the viewport top.

## Classify pages before sharing layout

Inspect DOM order, background boundaries, positioning, Header behavior, and interaction before classifying a page as `MarketingHeroPage`, `SectionedContentPage`, `SurfaceTransitionPage`, `OverlapLandingPage`, or `FixedHeaderWorkflowPage`. Leave unmatched pages unclassified until evidence resolves them; never guess from route or component names.

Define consistency by responsibility, not identical values or DOM. Record which layer owns page boundaries, same-background Section gaps, full-width surfaces, internal content stacks, fixed-header offsets, state relationships, and intentional overlap. PC and H5 may select different installed Ant tokens while preserving the same semantic mapping.

Share a primitive only when the same responsibility and boundary recur. Prefer small composable `PageSectionList`, `ContentSectionList`, `SurfaceSection`, `ContentStack`, `FixedHeaderContent`, `StateStack`, and `OverlapLayer` roles implemented as React components or shared scoped styles according to the repository. Do not create a universal PageLayout with mutually exclusive boolean modes, and do not add a wrapper unless it owns a real layout relationship, background boundary, accessibility grouping, or state group.

Read [references/cross-page-layout-contracts.md](references/cross-page-layout-contracts.md), [references/layout-levels.md](references/layout-levels.md), [references/containers.md](references/containers.md), [references/header-overlay-hero.md](references/header-overlay-hero.md), and the relevant PC/mobile reference before drawing conclusions.

## Run an audit

1. Establish scope and remain read-only.
2. Classify each page from structural evidence and record its layout contract before comparing pages or proposing shared primitives.
3. Reconstruct `Page → SectionList → Section/Surface → ModuleList → Module → Content`; trace the Padding Chain, background chain, direct-sibling gap owner, and Header/Hero, fixed-header, safe-area, overlap, full-width Surface, Drawer, iframe, or other exception.
4. For every PageContainer, `FixedHeaderContent`, ContentSection/List, `SurfaceSection`, and Drawer DetailPane, decompose padding into computed `block-start`, both inline sides, and `block-end`. Record the source declaration, current owner, visual effect, semantic role, and project-contract mapping; never approve a shorthand or four-value declaration as one indivisible value.
5. Treat installed-Ant Token validity and layout-contract fitness as separate claims. A valid Token does not prove the value belongs to the node's page role; report `TOKEN-VALID-CONTRACT-UNVERIFIED` until the Profile/Layout Contract and geometry establish that relationship.
6. On every fixed-Header page, use browser geometry to record Header position and height, `header.bottom`, the first business module's top/inline bounds, their actual distance, the CSS owner of that distance, whether it is a page-start boundary, internal padding, or child margin, and the comparison with structurally comparable pages.
7. Compare values only for the same responsibility. Keep H5 content inline inset, fixed-workflow page start, block-end navigation/safe-area reserve, and Drawer/iframe/rich-text/Card internal padding as separate contract slots. Read exact Token mappings from the project Profile/Layout Contract rather than hard-coding a universal baseline.
8. When one composite padding declaration hides several responsibilities, report `COMPOSITE-PADDING-001`, list every axis and semantic result, and recommend explicit `padding-inline`, `padding-block-start`, and `padding-block-end`. Pass it only when each responsibility is explicit and contract-consistent.
9. Run `scripts/scan-spacing.py` as a candidate finder when useful. Do not equate regex output with a finding.
10. Inspect the matching JSX/DOM, parent CSS, Ant component boundary, responsive branch, and project token setup; classify each confirmed issue using [references/audit-rules.md](references/audit-rules.md).
11. Distinguish alignment margin, internal typography margin, layout margin, and legacy/third-party margin. Verify `gap` has a flex/inline-flex/grid context, owns the intended direct children, and is not duplicated by child layout margin.
12. Trace padding, backgrounds, header offsets, and safe-area calculations through every nested container. Treat different values as a finding only after proving they represent the same semantic responsibility.
13. Identify Header `position`, initial transparent state/class, scrolled solid state, and transition trigger; reconstruct `Header → Page → Hero` stacking and decide whether the Hero should start at `y = 0`.
14. Trace every top-offset, header-height, and safe-area custom property from definition selector and scope to consumer and fallback. When `var(--x)` is unresolved without fallback, record the declaration as invalid at computed-value time and the property's resulting initial/inherited value; never treat it as an ordinary numeric value.
15. Do not bridge a component-scoped custom property onto a page root merely because two variables appear numerically equal. First prove that the old variable resolved at the actual consumer.
16. Report `HEADER-OVERLAY-001` as high when a transparent fixed/sticky Header with a first-screen Hero gains page-root `padding-top`, moving the Hero below the Header and exposing an unintended page-background band. Document exceptions for an explicitly solid Header or padding owned by a separate non-Hero content region.
17. For every H5 page audit, browser-record computed directional padding and gap plus Header bottom, first-module top/left/right, sibling geometry, background boundary, and bottom-navigation/safe-area geometry. If a browser is unavailable, mark those conclusions blocked/provisional; static source and scanner candidates are not visual verification.
18. Produce a report using `templates/spacing-audit-report.md`.

Each finding must include Issue ID, severity, rule, file, line, current code, problem, impact, recommended fix, current owner, target owner, shared-primitive suitability, auto-fix safety, scope, affected interactions, and regression points. Include summary counts, top issue types/directories, and remediation order.

For PR review, report only issues introduced by the diff. Separate Blocking, Non-blocking, and Suggestions.

## Assign fix safety

- `safe`: clearly equivalent token substitution; remove a proven duplicate child margin when the parent already provides the intended gap; replace hardcoded gap on an existing flex/grid; remove a proven duplicate safe-area term.
- `review-required`: add/change layout context; restructure DOM; change PageContainer, component tokens, breakpoint, max-width, or third-party wrapper; remove margin with uncertain visual intent.
- `unsafe`: business intent is unclear or a change may affect animation, positioning, virtualization, drag/drop, or coupled selectors/logic.

Never auto-fix from scanner output alone.

## Migrate incrementally

Before editing, read the project profile and latest audit when present, inspect the target, list files to change, and run a migration-risk audit. Then:

1. Establish the project Layout Contract in the repository-approved `.spacing-governance/profile.md` or `decisions.md`; keep project cases out of this Skill.
2. Select two structurally similar pages as baselines and establish or reuse only the primitives their shared responsibilities justify.
3. Migrate ordinary same-background Section ownership before pages with full-width surfaces.
4. Migrate `SurfaceTransitionPage` backgrounds and content boundaries without clipping them inside inline-padded containers.
5. Handle overlapping first screens, fixed headers, Drawers, iframes, virtual lists, and other exception pages last.
6. Migrate one page or one explicit layout level at a time, then consolidate safe-area, breakpoint, legacy, and lint protections as needed.

Before implementation, show the proposed DOM changes, primitive composition, installed-Ant Token mapping, responsive strategy, interaction risks, and regression plan; wait for explicit user confirmation.

Before changing page `padding-top`, Header offsets/heights, or their custom properties, capture the existing Header state machine, `Header → Page → Hero` geometry, and the complete custom-property scope chain. Do not convert an unresolved declaration into a concrete offset without confirming the intended visual contract.

Prefer one page, module, or directory per migration. Preserve business logic, naming, CSS technology, and unrelated formatting. Do not upgrade dependencies.

After every migration:

1. Re-run the focused scanner and semantic audit.
2. Confirm no new mixed gap/margin, double padding, safe-area loss/duplication, or breakpoint drift.
3. At one PC and one H5 target, record computed directional page/section padding, display/gap, direct-sibling geometry, background boundaries, Header/Hero or fixed-header geometry, and key anchor, Drawer, state, overlap, and scrolling interactions in scope.
4. For Header/Hero scopes, record the initial Header state class and computed background. When a transparent Header is intended to overlay the Banner, require `hero.top ≈ 0` and no purposeless band below the Header.
5. If a browser is unavailable, report visual verification as blocked and support only a provisional conclusion with the DOM/CSS custom-property scope chain; never claim static scanner output is visual verification.
6. Run repository-required lint, typecheck, tests, build, Ant lint, and browser checks in proportion to risk.
7. Report changed files, rule changes, validation results, residual review-required issues, and any visual risk.

Read [references/migration-strategy.md](references/migration-strategy.md) before changing source.

## Develop new features under governance

Before implementing a new page or module, classify the page, declare its layout contract and Page/Section/Surface/Module/Content tree, then choose PC/H5 page padding, Section gap, Module gap, internal gap, full-width regions, ContentContainer, safe-area owner, bottom-nav offset, max-width, breakpoint source, and Space/Flex/CSS layout responsibilities.

Search for existing primitives before using `templates/`. Templates are examples, not mandatory architecture. New Module roots must not decide their distance from siblings. Run a diff-scoped spacing review after implementation and fix safe findings.

## Choose layout tools deliberately

- Use Ant `Space` for small local inline groups.
- Use `Space.Compact` for connected controls.
- Use Ant `Flex` for business-component internal layout where its API is helpful.
- Use CSS Flex/Grid plus the repository's module/style system for stable page, SectionList, ModuleList, ModuleGrid, and container infrastructure.
- Do not mechanically convert between CSS Flex, Ant Flex, and Space.

Read [references/space-flex-grid.md](references/space-flex-grid.md) for exceptions.

## Prevent destructive normalization

Never:

- replace every `16px`, delete every margin, or add flex to every element;
- convert every `div`, `Space`, or CSS flex implementation mechanically;
- override every Card/Form/Table internal spacing;
- create wrappers solely to satisfy a rule;
- treat component dimensions, borders, max-width, breakpoints, or graphics sizes as spacing;
- use `--breakpoint-*` custom properties inside ordinary media-query thresholds;
- modify business/API logic or unrelated code;
- damage layout merely to achieve zero lint warnings.

## Load references as needed

- Core model: [references/spacing-principles.md](references/spacing-principles.md), [references/layout-levels.md](references/layout-levels.md)
- Tokens and hardcodes: [references/ant-design-token-rules.md](references/ant-design-token-rules.md), [references/lint-rules.md](references/lint-rules.md)
- PC/H5: [references/pc-spacing.md](references/pc-spacing.md), [references/mobile-spacing.md](references/mobile-spacing.md)
- CSS relationships: [references/gap-vs-margin.md](references/gap-vs-margin.md), [references/space-flex-grid.md](references/space-flex-grid.md)
- Containers/responsive/mobile: [references/containers.md](references/containers.md), [references/responsive.md](references/responsive.md), [references/safe-area.md](references/safe-area.md)
- Cross-page contracts and primitive roles: [references/cross-page-layout-contracts.md](references/cross-page-layout-contracts.md)
- Header/Hero overlays and variable scope: [references/header-overlay-hero.md](references/header-overlay-hero.md)
- Compatibility and delivery: [references/legacy.md](references/legacy.md), [references/audit-rules.md](references/audit-rules.md), [references/migration-strategy.md](references/migration-strategy.md)
- Forward-testing: [references/acceptance-scenarios.md](references/acceptance-scenarios.md)

Use prompts under `prompts/` as reusable invocations. Use templates only after project discovery. Use scripts only for candidate discovery; inspect source before reporting or changing anything.
