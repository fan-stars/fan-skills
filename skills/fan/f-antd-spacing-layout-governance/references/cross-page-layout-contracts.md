# Cross-page layout contracts

Unify ownership and semantic Token mapping across pages, not every value or DOM tree. Classify from evidence before selecting shared primitives.

## Page families

| Family | Evidence | Contract boundary |
| --- | --- | --- |
| `MarketingHeroPage` | Transparent/overlay Header, first-screen Hero, then ordinary content | Preserve Header/Hero overlay; apply ordinary Section ownership only below the Hero. |
| `SectionedContentPage` | Multiple peer business Sections on one background | Use one owner for page boundary and one parent gap for peer Sections. |
| `SurfaceTransitionPage` | Ordinary content alternates with full-width background surfaces | Let each Surface own its full-width background and block padding; constrain only its inner content. |
| `OverlapLandingPage` | Hero and another first-screen region intentionally overlap | Isolate overlap geometry in an explicit exception owner; do not normalize it into ordinary list flow. |
| `FixedHeaderWorkflowPage` | Fixed solid Header with states, forms, drawers, or transaction/workflow content | Apply exactly one content offset and preserve state and interaction boundaries. |

If evidence does not fit, record the page as unclassified and inspect DOM, backgrounds, positioning, scrolling, and interactions. Never infer a family from route or component names.

## Primitive family

Implement a role as a React component or shared scoped style according to project conventions. Do not require every role to create a DOM element.

| Role | Owns | Use when | Must not |
| --- | --- | --- | --- |
| `PageSectionList` | Ordinary page block boundary and relationships among direct page Sections | A page has a normal-flow Section region | Override Hero, Surface, fixed-header, or overlap geometry |
| `ContentSectionList` | Inline content safe area and gap among same-background peer Sections | Sections share one constrained content/background context | Contain a full-width Surface background |
| `SurfaceSection` | Full-width background and its block padding; optional constrained inner content | Background or surface type changes at this boundary | Inherit clipping inline padding from an outer content container |
| `ContentStack` | Gap among direct internal items such as title, Tabs, modules, and actions | Items belong to one component/content region | Decide external placement of its Module |
| `FixedHeaderContent` | The single content offset below a fixed solid Header | Header is intentionally solid and outside flow | Offset a transparent overlay Hero or duplicate a Layout offset |
| `StateStack` | Direct relationships among loading, ready, empty, notice, and related state content | State branches share one content boundary | Put external layout margins on individual states |
| `OverlapLayer` | Documented overlap geometry, stacking, and responsive behavior | Visual overlap is intentional and verified | Be replaced by ordinary Section gap or leak as a default pattern |

## Contract rules

- Let `PageSectionList` own ordinary page boundaries and `ContentSectionList` own peer same-background Section gaps. Keep Section and Module roots free of external layout margin by default.
- Let `SurfaceSection` own background and block padding. Place its constrained content inside it; never place the Surface itself inside a parent whose inline padding clips the background.
- Separate same-background Sections with parent gap. Add a divider only for a documented information hierarchy or content-type transition, never to hide double padding.
- Treat Hero, `OverlapLayer`, and `FixedHeaderContent` as explicit page contracts. Do not apply ordinary PageSectionList offsets or flow assumptions across them.
- Keep PC and H5 on the same responsibility-to-token mapping while allowing different installed Ant token choices and density.
- Prefer small composable roles. Reject a universal layout API driven by many `hasHero`, `fixedHeader`, `overlap`, `surface`, or similar mutually exclusive booleans.
- Add a wrapper only when it owns a direct layout relationship, background boundary, accessibility grouping, or state grouping. A class on an existing semantic element or shared CSS Module may be sufficient.
- Compare different numeric values only after determining whether both represent the same responsibility in the same page family.

## Directional boundary contracts

Audit boundary responsibilities by logical axis, not as one `padding` value. For every PageContainer, `FixedHeaderContent`, ContentSection/List, `SurfaceSection`, and Drawer DetailPane, record the source declaration and computed `padding-block-start`, `padding-inline-start`, `padding-inline-end`, and `padding-block-end`.

Keep these contract slots independent:

| Contract slot | Expected owner | Must not be compared directly with |
| --- | --- | --- |
| H5 content inline inset | ContentSection or ContentSectionList | Page start, bottom safe area, Drawer/Card internals |
| Fixed-workflow page start | `FixedHeaderContent` or the page content container | Header height, module-internal padding, child margin |
| Page block end | The designated page/bottom-navigation/safe-area owner | Page block start |
| Full-width Surface padding | `SurfaceSection` and its inner content boundary | Ordinary content-container inset without checking background intent |
| Detail/internal padding | Drawer DetailPane, iframe adapter, rich-text host, or Card internals | Page-family boundaries |

Exact values and installed-Ant Token names belong in the project Profile/Layout Contract. For example, a project may contract H5 content inline inset to `--ant-padding` (`16px`) and a fixed-workflow page-start boundary to `--ant-padding-lg` (`24px`). Enforce those mappings only when the project contract records them; they are not universal Skill defaults.

A valid installed Ant Token proves value provenance, not semantic ownership. If the Token is valid but the responsible contract slot, comparable page family, or browser geometry has not been established, record `TOKEN-VALID-CONTRACT-UNVERIFIED` rather than passing the declaration.

If one shorthand or four-value declaration simultaneously carries page start, content inline inset, and page end/safe-area responsibilities, record `COMPOSITE-PADDING-001`. List each axis, computed value, visual result, and intended owner; recommend explicit logical-axis declarations. A composite declaration passes only when every axis has a clear owner and matches the recorded contract.

For a fixed solid Header, browser-measure Header positioning and height, `header.bottom`, the first business module's top and inline bounds, and the actual distance between them. Trace that distance through the Padding Chain to its CSS owner, classify it as page-start boundary, module-internal padding, child margin, or another documented role, and compare it only with the same responsibility on structurally comparable pages. Report `PAGE-START-BOUNDARY-001` when the boundary is absent, implicit, owned by the wrong layer, or conflicts with the project contract.

## Required contract output

For each audited page, record:

- classification and evidence;
- `Page → SectionList → Section/Surface → ModuleList → Module → Content` tree;
- Padding Chain and background chain;
- directional padding table with source and computed values, semantic owner, and contract status;
- owner of each direct-sibling gap;
- on fixed-Header pages, measured Header height/position, Header-bottom-to-first-module distance, distance owner, and same-family comparison;
- Header/Hero, fixed Header, safe area, overlap, full-width Surface, Drawer, iframe, virtual list, or other exception;
- current and target ownership;
- shared-primitive suitability and implementation form;
- installed-Ant Token mapping for PC and H5;
- migration safety, affected interactions, and regression checkpoints.
