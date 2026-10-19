# Responsive and breakpoints

Use Ant `screen*` semantics as the design source. Discover all sources: theme tokens, `Grid.useBreakpoint`, matchMedia, CSS media queries, Tailwind, Sass/Less/PostCSS/custom media, and handwritten thresholds.

Ordinary CSS custom properties cannot provide a media-query threshold:

```css
/* Invalid as a portable CSS media-query threshold. */
@media (min-width: var(--breakpoint-md)) { }
```

Prefer a build-time shared source when the stack supports it. For pure CSS Modules, allow a single centralized numeric mirror (for example 768px for `screenMD`) with an explicit sync comment; do not scatter copies through business code. Flag duplicate sources, numeric drift, and spacing/layout changes that do not switch coherently at the chosen breakpoint.
