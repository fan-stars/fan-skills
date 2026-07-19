---
name: next-browser
description: >-
  CLI that gives agents what humans get from React DevTools and the Next.js dev
  overlay — component trees, props, hooks, PPR shells, errors, network — as
  shell commands that return structured text. Use when debugging Next.js apps,
  inspecting React component state, diagnosing hydration errors, or optimizing
  route/render performance.
---

# next-browser

If `next-browser` is not already on PATH, install `@vercel/next-browser`
globally with the user's package manager, then `playwright install chromium`.

If `next-browser` is already installed, it may be outdated. Run
`next-browser --version` and compare against the latest on npm
(`npm view @vercel/next-browser version`). If the installed version is
behind, upgrade it (`npm install -g @vercel/next-browser@latest` or the
equivalent for the user's package manager) before proceeding.

---

## Next.js docs awareness

If the project's Next.js version is v16.2.0-canary.37 or later, bundled
docs live at `node_modules/next/dist/docs/`. Before doing PPR work, Cache
Components work, or any non-trivial Next.js task, read the relevant doc there
— your training data may be outdated. The bundled docs are the source of truth.
