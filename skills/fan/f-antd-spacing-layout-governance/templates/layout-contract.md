# Project layout contract

This contract records layout responsibilities and how the project maps them to installed Ant Design tokens. It does not define a second spacing scale or require identical page values/DOM.

## Evidence

- Contract owner/location:
- Ant Design version and CSS-variable prefix:
- Audited page scope:
- DOM/CSS/browser evidence:
- Last reviewed:

## Page classification

| Page/scope | Family | Structural evidence | Background/position evidence | Interactions | Exceptions |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |

Leave a page unclassified when evidence is incomplete.

## Primitive registry

| Semantic role | Existing implementation | React component / scoped style | Direct children | Owns | Must not own |
| --- | --- | --- | --- | --- | --- |
| PageSectionList |  |  |  |  |  |
| ContentSectionList |  |  |  |  |  |
| SurfaceSection |  |  |  |  |  |
| ContentStack |  |  |  |  |  |
| FixedHeaderContent |  |  |  |  |  |
| StateStack |  |  |  |  |  |
| OverlapLayer |  |  |  |  |  |

Do not create missing primitives unless at least two compatible consumers or a clear infrastructure need justify them.

## Semantic Token mapping

| Responsibility | PC installed Ant token | H5 installed Ant token | Owner | Evidence/exception |
| --- | --- | --- | --- | --- |
| Page boundary |  |  |  |  |
| Same-background Section gap |  |  |  |  |
| Surface block padding |  |  |  |  |
| Module gap |  |  |  |  |
| ContentStack gap |  |  |  |  |
| StateStack gap |  |  |  |  |
| Content inline inset |  |  | ContentSection/List |  |
| Fixed-workflow page start |  |  | FixedHeaderContent/page content |  |
| Page block end/navigation reserve |  |  |  |  |

## Directional boundary evidence

| Page/scope | Node/role | Source declaration | Computed block-start | Computed inline-start/end | Computed block-end | Current owner | Contract status |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |

For fixed-Header pages, record Header position/height, `header.bottom`, first-module top/left/right, the measured distance and CSS owner, its semantic role, and same-family baseline. Record bottom safe-area/navigation reserve separately. Drawer DetailPane, iframe, rich-text, and Card internals are independent contracts unless evidence proves otherwise.

## Exception registry

| Scope | Header/Hero, fixed header, safe area, overlap, Surface, Drawer, iframe, virtual list, or other | Owner | Geometry/interaction contract | Regression checks |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Baseline and migration decisions

- Two structurally similar baseline pages:
- Primitive decisions:
- Deferred Surface pages:
- Deferred exception pages:
- User approval record:
