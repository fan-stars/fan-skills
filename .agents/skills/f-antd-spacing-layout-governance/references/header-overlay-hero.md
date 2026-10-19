# Header overlay and first-screen Hero

## Reconstruct the contract

For every Header plus first-screen Hero relationship, determine:

- Header `position`: normal flow, `sticky`, `fixed`, or `absolute`;
- initial state/class and whether its background is transparent;
- scrolled state/class, solid background, and transition trigger;
- stacking context, z-index, and whether Header height occupies document flow;
- Page and Hero top coordinates and the intended first-screen composition.

When a transparent Header is intended to overlay a Banner/Hero, the Hero normally begins at the viewport top and supplies the visual surface behind the Header. Do not add Page `padding-top` merely because the Header has a measurable height.

## Trace custom-property scope

For every variable used by `top`, `padding-top`, Header height, or safe area, record:

1. declaration file and selector;
2. selector scope and inheritance path;
3. consuming element and property;
4. fallback, if any;
5. resolved/computed result at the consumer.

Do not infer availability from a declaration elsewhere in the stylesheet. A variable declared on a Header descendant or component root is not automatically visible to a sibling Page root.

If `var(--x)` is unresolved and has no fallback, the containing declaration becomes invalid at computed-value time. Record the resulting property behavior—initial value for a non-inherited property such as `padding-top`, or inherited/unset behavior where applicable. Do not reinterpret the failed declaration as a missing number that should be replaced.

Never bridge a component-scoped variable to a page root solely because its observed value equals another height or offset. First prove whether the old variable resolved at the consumer and whether introducing a concrete value changes existing geometry.

## `HEADER-OVERLAY-001`

Report a high-severity regression when all are true:

- a fixed or sticky Header is transparent in its initial state;
- the first screen contains a Hero intended to render beneath it;
- a Page/root `padding-top` is added or becomes effective;
- the Hero moves below the Header and an unintended page-background band appears.

Do not report the rule when the product explicitly requires a solid, in-flow Header or when the padding belongs to an independent non-Hero content region. State the exception and its evidence in the audit.

Treat changes to this relationship as `review-required` unless runtime geometry and visual intent make equivalence unambiguous.

## Regression verification

Verify at least one PC and one H5 first-screen width. Capture:

- initial Header state class;
- Header computed background;
- Header top coordinate;
- Hero top coordinate;
- Page computed `padding-top`;
- scrolled-state trigger and resulting Header background when in scope.

For an overlay design, accept `hero.top ≈ 0` within normal subpixel tolerance and reject any blank band without business purpose. If browser verification is unavailable, mark the visual check blocked and report only a provisional DOM/CSS scope-chain analysis.
