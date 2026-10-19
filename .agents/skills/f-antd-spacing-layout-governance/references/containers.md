# Containers

## Responsibilities

- **PageContainer**: true page-root content safe area, page padding, optional centralized max-width.
- **ContentContainer**: local horizontal and optional vertical padding only.
- **MobilePageContainer**: mobile page boundary and safe-area policy.
- **MobilePageContainerWithBottomNav**: bottom-nav content offset plus the project's single safe-area policy.
- **StickyActionBar**: owns its fixed/sticky action padding and safe area when designated.
- **PageSectionList**: owns ordinary page block boundaries and direct Section relationships.
- **ContentSectionList**: owns inline content safety and same-background peer Section gaps.
- **SurfaceSection**: owns full-width background and block padding; its inner content may be constrained separately.
- **FixedHeaderContent**: owns exactly one offset below a fixed solid Header.

ContentContainer must not own Header, BottomNav, full-page height, global safe area, or Section gap.

## Audit padding chains

Search existing PageContainer, Content, Container, Layout, MainContent, and PageContent before creating a primitive. Trace final visual padding through Layout → Drawer/Modal/Tabs/Card body → local container. Flag nested PageContainer and duplicate padding. Do not put a complete PageContainer inside Drawer, Modal, Tabs panel, Card body, Collapse, expanded row, or Popover unless it is genuinely a page root.

Use a lightweight ContentContainer only when the host does not already provide the intended local padding. Preserve intentionally full-bleed modules.

Do not place a full-width Surface inside an inline-padded content container. Do not use PageSectionList to offset transparent Hero or intentional overlap. Add no wrapper unless it establishes a real boundary or direct-child relationship.

## Audit padding by responsibility

For every PageContainer, `FixedHeaderContent`, ContentSection/List, `SurfaceSection`, and Drawer DetailPane, expand authored shorthand and record browser-computed values separately:

| Axis | Required evidence | Typical responsibility |
| --- | --- | --- |
| `padding-block-start` | declaration, computed value, element top, first-child top | Page start, Surface start, or internal start |
| `padding-inline-start/end` | declaration, computed values, content left/right bounds | Content inset or component-internal inset |
| `padding-block-end` | declaration, computed value, last-child/page bottom, navigation bounds | Page end, Surface end, or safe-area/navigation reserve |

Do not approve `padding`, including four-value syntax, as a single semantic unit. If its axes carry different responsibilities, report them separately and use `COMPOSITE-PADDING-001` when the ownership is obscured. Prefer explicit logical-axis properties in a recommended fix; do not rewrite merely for style when all responsibilities are already clear and contract-consistent.

Token provenance never waives this audit. A declaration such as `padding-block-start: var(--ant-padding-xs)` may use a valid installed Token and still violate the fixed-workflow page-start contract. Until the project contract, comparable page evidence, and geometry verify the role, use `TOKEN-VALID-CONTRACT-UNVERIFIED`.

For each fixed solid Header page, collect browser evidence for:

- computed Header `position`, top/bottom coordinates, and actual height;
- first business module top/left/right coordinates;
- `firstModule.top - header.bottom` and the declaration(s) producing it;
- whether that distance is owned by `FixedHeaderContent`/page content, module-internal padding, child margin, or an explicit exception;
- the same contract slot on structurally comparable pages.

Use `PAGE-START-BOUNDARY-001` when the distance lacks an explicit page-level owner or conflicts with the recorded same-family contract. Keep block-end navigation/safe-area reserve separate from block-start. Treat Drawer, iframe, rich-text, and Card internal padding as independent semantics unless the DOM shows that they actually own the page boundary.
