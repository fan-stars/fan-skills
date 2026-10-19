# Space, Flex, and Grid responsibilities

| Need | Preferred tool |
| --- | --- |
| Small inline group: buttons, tags, icon + text, status | Ant `Space` |
| Connected controls | `Space.Compact` |
| Business-component internal layout with useful responsive/wrap/alignment props | Ant `Flex` |
| Stable Page/SectionList/ModuleList/ContentContainer | CSS Flex + scoped project styles |
| Two-dimensional module collection | CSS Grid + scoped project styles |

Do not mechanically convert CSS Flex to Ant Flex or Space to Flex. Consider semantics, DOM output, responsive behavior, server rendering, accessibility, and repository conventions. Use `theme.useToken()` for JS calculations, charts/canvas, third-party APIs, or Ant component props; keep stable layout in classes and Ant CSS variables when available.
