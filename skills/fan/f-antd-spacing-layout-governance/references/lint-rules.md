# Lint governance

Use lint as candidate detection, not semantic proof. Introduce rules gradually and measure false positives before making them blocking.

Candidate patterns:

- hardcoded `margin`, `padding`, `gap`, `row-gap`, or `column-gap`;
- component-root block margins;
- parent gap plus child layout margin;
- gap without flex/grid;
- duplicate custom spacing tokens;
- repeated breakpoints or safe-area calculations;
- stable layout spacing in large inline style objects.

Allow dimensions (`height: 56px`), max-width, borders, graphics, legitimate breakpoints, third-party requirements, `env()`, and valid `calc()`. Still flag a hardcoded term inside `calc()` when that term is semantically spacing. Prefer review checklists or narrow custom checks over a broad no-px rule.
