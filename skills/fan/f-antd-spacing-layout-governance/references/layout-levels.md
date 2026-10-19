# Layout levels

```text
Page
├── Hero | OverlapLayer | FixedHeaderContent (when contracted)
└── PageSectionList
    ├── ContentSectionList
    │   └── Section
    └── SurfaceSection
        └── Section | ModuleList | ModuleGrid
            └── Module
                └── Content | ContentStack | StateStack
                    └── Element
```

- **Page**: overall route/page structure.
- **PageContainer**: page-root content safety and outer padding.
- **ContentContainer**: lightweight local horizontal/optional vertical padding.
- **Section**: primary business grouping; does not normally own the distance to the next Section.
- **PageSectionList**: owns normal page boundaries and direct ordinary Section/Surface relationships.
- **ContentSectionList**: owns inline content safety and gaps among same-background peer Sections.
- **SurfaceSection**: owns a full-width background boundary and its block padding.
- **Module**: independently reusable business unit.
- **ModuleList/ModuleGrid**: owns direct Module gaps.
- **ContentStack/StateStack**: owns direct internal or state-sibling gaps.
- **FixedHeaderContent/OverlapLayer**: explicit offset/overlap contracts, not ordinary lists.
- **Content**: internal Module region such as toolbar, filter, actions, body, or metadata.
- **Element**: icon, text, button, tag, field, and similar primitive.

Infer roles from DOM, backgrounds, positioning, and business semantics, never names alone. A ProductCard or OrderTable may be a Module; Toolbar/Filter/Table/Pagination often form Content regions inside one TableModule. Outer layout gap does not reach inner modules, and ordinary Section flow does not override Surface, fixed-header, Hero, or overlap contracts.
