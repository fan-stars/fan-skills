# Ant Design token rules

## Source of truth

Verify tokens against the installed Ant Design version and repository tooling. Prefer real global tokens such as `marginXXS`, `marginXS`, `marginSM`, `margin`, `marginLG`, `marginXL`, `marginXXL`, `paddingXXS`, `paddingXS`, `paddingSM`, `padding`, `paddingLG`, and `paddingXL` when present.

`margin` is a real token commonly representing 16px. Do not invent `marginMD` or substitute a fictional name to avoid the word “margin.”

## CSS variables

When Ant CSS variables are enabled, use the project's actual prefix and emitted variable names. Do not assume `--ant-*` without checking `ConfigProvider` and rendered/local package behavior.

It is valid to use a margin token's size for gap:

```css
.moduleList {
  display: flex;
  flex-direction: column;
  /* Reuse Ant margin-lg as a size; the layout property remains gap. */
  gap: var(--ant-margin-lg);
}
```

## Prohibited duplicate systems

Flag `spacing.ts`, `space.ts`, `layoutSpacing.ts`, `designSpacing.ts`, or custom variables such as `--app-space-sm` only when they duplicate Ant spacing values/semantics. Do not flag component dimensions, safe-area terms, or centralized content-size constraints as spacing tokens.

## Component tokens

Use Card/Form/Table/Modal/Drawer component tokens for their internals. Do not normalize component internals to global page gaps merely because numeric values differ. Verify public APIs before overrides and prefer supported `styles`/`classNames`/theme configuration over internal `.ant-*` selectors.
