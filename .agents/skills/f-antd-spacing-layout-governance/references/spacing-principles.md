# Spacing principles

## Governing formula

```text
boundary                         → padding
direct sibling relationship      → parent gap
Ant component internals          → component token
custom business component inside → padding + internal gap
```

Use parent padding for first/last space and parent gap for siblings. Keep Page, Section, and Module ownership distinct. A reusable child should not encode its placement through block margins.

## Invariants

- Never combine parent gap and child layout margin for the same sibling relationship.
- Gap affects direct children only and does not collapse like vertical margins.
- Give nested lists their own layout container and gap.
- Treat Card, Panel, Banner, address block, order card, and product block as Module implementations, not separate global spacing systems.
- Permit alignment margins such as `margin-inline: auto` or `margin-left: auto`.
- Preserve justified typography/algorithmic margins and isolate legacy exceptions.
- Treat Ant Design tokens as the only design-value source.

## Scope boundary

Govern layout and spacing without redesigning the UI, changing business/API logic, switching CSS technology, or performing unrelated cleanup.
