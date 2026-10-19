# Mobile safe area and bottom navigation

Assign one owner:

- ordinary mobile page → `MobilePageContainer`;
- fixed BottomNav page → `MobilePageContainerWithBottomNav`;
- fixed/sticky action area → `StickyActionBar` when designated.

Audit `env(safe-area-inset-bottom)`, fixed/sticky elements, content obstruction, and every `calc()`. Determine whether BottomNav height already includes safe area before adding another term.

BottomNav height is a component dimension, not a spacing token. A centralized `--bottom-nav-height: 56px` is valid; repeated page-local 56px values are not. A valid offset may resemble:

```css
padding-bottom: calc(
  var(--bottom-nav-height) +
  var(--ant-padding) +
  env(safe-area-inset-bottom)
);
```

Replace hardcoded spacing terms with verified Ant variables, but preserve component dimensions and `env()`. Flag missing and duplicate responsibility separately.
