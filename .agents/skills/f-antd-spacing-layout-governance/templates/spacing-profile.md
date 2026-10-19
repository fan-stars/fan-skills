# Project spacing profile

This file records how the project consumes Ant Design tokens. It does not define a second token system.

## Runtime and styling

- Ant Design version:
- React/framework version:
- Build tool:
- CSS strategy:
- Ant `cssVar` enabled/prefix:
- Repository instructions:
- Validation commands:

## Layout infrastructure

- PC PageContainer:
- MobilePageContainer:
- ContentContainer:
- SectionList:
- ModuleList/ModuleGrid:
- BottomNav height owner:
- StickyActionBar:
- Safe-area owner:
- Header initial/scrolled state and trigger:
- Transparent Header/Hero overlay policy:
- Header top/height variable scope:
- PC constrained max-width policy:
- Breakpoint source:

## Project Layout Contract

- Contract document/location:
- Page-family inventory:
- Two structurally similar baseline pages:
- PageSectionList implementation:
- ContentSectionList implementation:
- SurfaceSection implementation:
- ContentStack implementation:
- FixedHeaderContent implementation:
- StateStack implementation:
- OverlapLayer implementation:
- Unclassified pages and missing evidence:

### Directional boundary contracts

- H5 content inline inset owner and installed Ant Token:
- Fixed-workflow page-start owner and installed Ant Token:
- Page block-end/navigation reserve owner and installed Ant Token:
- Safe-area owner and composition rule:
- Surface block/inline boundary rule:
- Drawer DetailPane/iframe/rich-text/Card internal-padding exceptions:

Record computed values observed at named PC/H5 baselines. Example only: a project may map H5 content inline inset to `--ant-padding` (`16px`) and fixed-workflow page start to `--ant-padding-lg` (`24px`); do not treat these as universal defaults.

## Token usage decisions

- PC page padding:
- H5 page padding:
- Section gap:
- Module gap:
- Internal gap:
- Element/micro gap:

Record semantic responsibility → installed Ant token mappings for PC and H5. Different values are acceptable when density differs; do not copy token values into a new scale.

## Exceptions

- Legacy/third-party adapters:
- Full-bleed regions:
- Full-width Surface boundaries:
- Fixed-header offsets:
- Intentional overlap contracts:
- Drawer/iframe/virtual-list interactions:
- Page-specific density:
- Known risks/debt:

## Evidence

List source files and line references supporting every decision.
