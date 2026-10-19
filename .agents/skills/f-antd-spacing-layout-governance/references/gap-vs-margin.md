# Gap versus margin

## Decision process

1. Identify the direct sibling set.
2. Confirm the parent uses `flex`, `inline-flex`, or `grid` before accepting gap.
3. Check each direct child for layout margins that duplicate the same relationship.
4. Check nested children separately; outer gap cannot govern them.
5. Preserve alignment margin and justified internal typography margin.

## Findings

- `SPACING-GAP-NO-LAYOUT`: gap exists without a supported layout context. Severity is normally high, but inspect DOM before adding flex/grid.
- `SPACING-MIXED-GAP-MARGIN`: parent gap and direct-child layout margin both control the same axis.
- `SPACING-DEEP-GAP-ASSUMPTION`: code or structure relies on an outer gap to space nested descendants.
- `SPACING-ROOT-MARGIN`: a reusable component root decides page placement.

Do not declare `.card { margin-bottom: ... }` invalid until the parent and role are known. Do not declare `gap: var(--ant-margin-lg)` invalid: it reuses a token size while using the correct property.
