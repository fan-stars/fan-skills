# Migration strategy

## Before editing

Read repository instructions, spacing profile, Layout Contract, decisions, baseline/latest audit, target JSX/CSS, and related layout parents. Classify pages from DOM, background, positioning, and interaction evidence. Identify virtualized lists, drag/drop, animation, absolute/fixed/sticky positioning, scroll/overflow containers, global/inherited styles, margin-collapsing dependencies, selector coupling, Drawers, iframes, and third-party code. For Header/Hero scopes, capture the Header state machine, overlay geometry, and every top-offset/header-height/safe-area variable's definition selector, consumer, inheritance path, fallback, and computed result. Classify candidates as SAFE, REVIEW REQUIRED, or DO NOT AUTO FIX.

Before implementation, present proposed DOM changes, primitive composition, installed-Ant Token mapping, PC/H5 responsive strategy, interaction impact, and regression plan. Wait for explicit user confirmation.

## Sequence

1. Write the project-level Layout Contract to the repository-approved `.spacing-governance/profile.md` or `decisions.md`.
2. Select two structurally similar pages as baselines and establish only justified shared primitives.
3. Migrate normal same-background Section ownership and internal stacks.
4. Migrate pages with full-width Surface transitions while preserving background boundaries.
5. Handle Hero overlap, fixed headers, Drawers, iframes, virtual lists, and other exceptions last.
6. Consolidate safe-area, breakpoint, legacy, and narrowly useful lint protections after ownership is stable.

## Change discipline

Migrate one page or one explicit layout level at a time. Make the smallest explained change. Preserve business logic, DOM when possible, existing CSS technology, unrelated formatting, and dependency versions. Avoid repository-wide migration in one pass.

Do not bridge a component-scoped variable to the Page or replace an unresolved `var()` with a concrete offset based only on numeric equality. First determine the old declaration's real computed-value behavior and the intended Header/Hero contract.

## Regression

Re-audit the exact scope and inspect the diff. At one PC and one H5 target, capture computed page/section padding, direct-sibling gap, background boundaries, Header/Hero or fixed-header geometry, and key anchor, state, overlap, Drawer, and scrolling interactions in scope. For an intended transparent overlay, require `hero.top ≈ 0` and no purposeless background band. Confirm full-width Surfaces are not clipped and fixed solid Headers apply exactly one offset. If browser access is unavailable, mark visual validation blocked and provide only provisional DOM/CSS scope-chain evidence. Run repository lint, typecheck, tests, build, framework/Ant checks, and browser checks in proportion to risk. Report resolved, remaining, regressions, and validation results.
