# AGENTS.md

## Project Overview

`fan-skills` is a **skills catalog** for Fan projects. Other repos copy skills by stack from the classified tree. It is **not** an application: there is no app server, package.json app build, or test suite for product code.

| Path | Role |
| --- | --- |
| `.agents/skills/` | **Source of truth** (installed/updated via `skills-lock.json`) |
| `skills-lock.json` | Upstream install lock for third-party skills |
| `skills-catalog.json` | Category mapping + links only (**no** Chinese copy) |
| `skills/` | **Derived, read-only** classified copies (wipe-and-rebuild) |
| `.cursor/skills/sync-skills-catalog/` | Ops sync skill (**not** in catalog, **not** copied to `skills/`) |
| `.cursor/skills/sync-skills-catalog/generated/skill-docs.json` | AI-generated Chinese docs cache (content-hash keyed) |
| `spec/` | Local OpenSpec notes only — **gitignored** (`/spec`) |

Current scale (approx.): ~36 skills under `.agents/skills/`, multi-category copies under `skills/` (e.g. `frontend-design` in both `web/react` and `web/design`).

## Hard Rules (do not violate)

1. **Never hand-edit** anything under `skills/`. Always regenerate via sync.
2. **Never put Chinese blurbs** (`descriptionZh`, `detailsZh`, etc.) in `skills-catalog.json`.
3. **Never add** `sync-skills-catalog` to `skills-catalog.json` or copy it into `skills/`.
4. Catalog skill set **must equal** directory names in `.agents/skills/` (sync validates this).
5. Fan-authored skills use the `f-` prefix and belong in category `fan` (may also keep a tech category).
6. Phase 1: **no presets** packages.
7. Prefer **Chinese commit messages** matching recent history (imperative, why-focused).

## Setup Commands

No Node app install is required for catalog maintenance. You need:

- `python3` (sync scripts)
- Network + `npx` when installing/updating skills from GitHub / skills.sh

```bash
# Optional: refresh locked third-party skills
npx skills update -y

# See which skills need AI Chinese docs
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py status

# After skill-docs.json is complete: wipe skills/ and rebuild
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py render

# Validate catalog + docs + README consistency
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py validate
```

Default remote for this clone is often `origin1` (Gitee). Check with `git remote -v` before push.

## Development Workflow

### Add a third-party skill

```bash
npx skills add <owner/repo>            # or owner/repo/skill-name
# Ensure skills-lock.json updated
# Add entry to skills-catalog.json: categories[], skillsShUrl, githubUrl (nullable)
# Run status → generate docs for NEED_GENERATE → render → validate
```

If the upstream repo has **no** `SKILL.md` (e.g. some registry-only skills), manually place `.agents/skills/<name>/SKILL.md` from skills.sh content, set `githubUrl` to `null` if appropriate, then sync.

### Add a Fan-authored skill

1. Create `.agents/skills/f-<name>/` with `SKILL.md` (and optional references).
2. In `skills-catalog.json`:
   - categories: always include `"fan"`; add tech categories as needed (`java`, `workflow`, …)
   - `skillsShUrl`: `null`
   - `githubUrl`: `null` (README will link to this repo’s `.agents/skills/...`)
3. Generate Chinese docs + `render` + `validate`.

### Change categories only

Edit `skills-catalog.json` categories lists → `render` (no AI regen if content hashes unchanged).

### Sync / Chinese README pipeline (mandatory order)

1. `sync.py status` → read `NEED_GENERATE` (also written to `generated/status.json`).
2. For each listed skill: read `.agents/skills/<name>/SKILL.md` (and references if needed). **Do not invent** capabilities from the name alone.
3. Write/update `.cursor/skills/sync-skills-catalog/generated/skill-docs.json` per [GENERATION_PROTOCOL.md](.cursor/skills/sync-skills-catalog/docs/GENERATION_PROTOCOL.md):
   - Fields: `summary`, `capabilities`, `scenarios`, `coverage`, `notes`, `contentHash`
   - `contentHash` must match `status.json` hashes
   - Quality: Chinese (CJK), `summary` ≥ 24 chars and no `|`, other fields ≥ 40 chars
4. `sync.py render` then `sync.py validate` (expect `VALIDATE_OK`).

Ops skill entrypoint: `.cursor/skills/sync-skills-catalog/SKILL.md`.

## Categories

Defined in `skills-catalog.json` → `categories`:

| Key | Meaning |
| --- | --- |
| `web/react` | React / Next / Ant Design |
| `web/vue` | Vue / Nuxt / Vben |
| `web/design` | Visual design & UI guidelines |
| `java` | Spring Boot / Java refactor |
| `spec` | OpenSpec / specifications |
| `docs` | Office docs (docx/pdf/pptx/xlsx) |
| `workflow` | Planning, grilling, domain modeling, find-skills |
| `mcp` | MCP server building |
| `testing` | Web / browser automation testing |
| `fan` | Fan-authored, non-public-open-source skills |

A skill may list **multiple** categories; sync copies the full skill tree into each.

## Copying skills into another project

1. Browse `skills/<category>/README.md` (table + detailed sections).
2. Copy the skill folder into the target’s `.agents/skills/`.
3. If the target uses `skills-lock.json`, add lock entries as needed.
4. Do not treat `skills/` as editable source — edits belong in `.agents/skills/` of **this** repo, then sync.

## Testing Instructions

There is no unit/e2e suite. “Tests” for agents mean:

```bash
python3 .cursor/skills/sync-skills-catalog/scripts/sync.py validate
```

Additional checks after sync:

- Multi-category skills appear in every listed category with identical content.
- Fan skills show skills.sh as「暂无」and GitHub as「本仓库」link.
- `.cursor/skills/sync-skills-catalog` does **not** appear under `skills/`.
- Idempotency: second `render` with unchanged docs/source should not change meaningful content.
- Content change: touching a skill file → `status` lists only that skill under `NEED_GENERATE`.

## Code Style

- Catalog JSON: stable metadata only (`categories`, `skillsShUrl`, `githubUrl`). Keep skill keys sorted alphabetically when adding entries.
- AI docs: Chinese prose; follow GENERATION_PROTOCOL length/CJK rules.
- Derived READMEs: generated by `sync.py` — do not format by hand.
- `.gitignore`: `/spec` (repo-root only) and `.idea`. Do **not** use a bare `spec` pattern (it would ignore `skills/spec/`).

## Build and Deployment

No production build. “Publish” is:

1. Sync so `skills/` and generated docs are current.
2. Commit catalog, `.agents/skills`, lock, sync tooling, and regenerated `skills/`.
3. Push to the configured remote (`git push origin1 HEAD` if that is the tracking remote).

Do not commit secrets. Do not commit ignored `spec/` unless the user explicitly changes ignore policy.

## Pull Request / Commit Guidelines

- Commit messages: concise Chinese, focus on why (see `git log`).
- Before commit: `sync.py validate` if catalog/skills/docs changed.
- Include both source (`.agents/skills`, catalog, lock, `skill-docs.json`) and derived `skills/**` when sync output changes.
- Ask before amending or force-pushing; do not update git config.

## Debugging and Gotchas

- `status` exit code **2** when any skill needs generation — expected, not a crash.
- `render` fails hard if any skill lacks valid AI docs (no silent fallback to skill name).
- `npx skills add` may only install the first package when multiple are passed; install one-by-one.
- Some skills.sh entries have no GitHub `SKILL.md`; install/create manually then catalog with `githubUrl: null`.
- Tool-type skills (`agent-browser`, `next-browser`, `extract-design-system`) need extra CLI/browser installs at **use** time in consumer projects; this repo only stores the skill text.
- Local OpenSpec under `spec/` is for maintainers’ planning; it is not part of the published catalog tree.

## Additional Notes

- Human-oriented overview: [README.md](README.md) (may lag slightly; prefer this file + `skills/README.md` for agent truth).
- When regenerating Chinese docs, prefer reusing unchanged `contentHash` entries in `skill-docs.json` to avoid noisy diffs.
