# AGENTS.md

## Project Overview

`fan-skills` is a **skills catalog** for Fan projects. Other repos copy skills by stack from the classified tree. It is **not** an application: there is no app server, package.json app build, or test suite for product code.

| Path | Role |
| --- | --- |
| `.agents/skills/` | **Source of truth** (installed/updated via `skills-lock.json`) |
| `skills-lock.json` | Upstream install lock for third-party skills |
| `skills-catalog.json` | Category mapping + links only (**no** Chinese copy) |
| `skills/` | **Derived, read-only** classified copies (wipe-and-rebuild) |
| `spec/` | Local OpenSpec notes only — **gitignored** (`/spec`) |

This repo keeps the **content library only** (`.agents/skills` + derived `skills/`). Ops live in parent workspace `fan-skills-dir`:

| Path / command | Role |
| --- | --- |
| `fan-skills-dir/.agents/skills/f-skills-catalog/scripts/sync.py` | catalog status / render / validate |
| `fan-skills-dir/.agents/skills/f-skills-sync/scripts/sync.py` | global install / uninstall / pull |
| `fan-skills-dir/.fan-skills/` | library path + roster (machine/selection local-only) |
| `…/f-skills-catalog/generated/skill-docs.json` | AI Chinese docs cache (content-hash keyed) |

## Hard Rules (do not violate)

1. **Never hand-edit** anything under `skills/`. Always regenerate via catalog script.
2. **Never put Chinese blurbs** (`descriptionZh`, `detailsZh`, etc.) in `skills-catalog.json`.
3. **Never add** workspace ops skills (`f-skills-catalog` / `f-skills-sync`) to `skills-catalog.json` or copy them into `skills/`.
4. Catalog skill set **must equal** directory names in `.agents/skills/` (sync validates this).
5. Fan-authored skills use the `f-` prefix and belong in category `fan` (may also keep a tech category).
6. Phase 1: **no presets** packages.
7. Prefer **Chinese commit messages** matching recent history (imperative, why-focused).

## Setup Commands

Run catalog / sync commands from **`fan-skills-dir`** (library resolved via `.fan-skills` / `FAN_SKILLS_LIBRARY`):

```bash
# Optional: refresh locked third-party skills (from this library root)
npx skills update -y

python3 .agents/skills/f-skills-catalog/scripts/sync.py status
python3 .agents/skills/f-skills-catalog/scripts/sync.py render
python3 .agents/skills/f-skills-catalog/scripts/sync.py validate

python3 .agents/skills/f-skills-sync/scripts/sync.py status
python3 .agents/skills/f-skills-sync/scripts/sync.py apply --skill NAME
```

## Development Workflow

### Add a third-party skill

```bash
npx skills add <owner/repo>            # or owner/repo/skill-name
# Ensure skills-lock.json updated
# Add entry to skills-catalog.json: categories[], skillsShUrl, githubUrl (nullable)
# Run catalog status → generate docs for NEED_GENERATE → render → validate
```

### Add a Fan-authored skill

1. Create `.agents/skills/f-<name>/` with `SKILL.md` (and optional references).
2. In `skills-catalog.json`: include `"fan"` (+ tech categories); `skillsShUrl`/`githubUrl` as appropriate; keys will be sorted by status/render/validate.
3. Generate Chinese docs + catalog `render` + `validate`.

### Sync / Chinese README pipeline

1. catalog `status` → `NEED_GENERATE`
2. Update workspace `f-skills-catalog/generated/skill-docs.json` per its generation protocol
3. catalog `render` then `validate` (expect `VALIDATE_OK`)

## Categories

Defined in `skills-catalog.json` → `categories` (web/react, web/vue, web/design, java, spec, docs, workflow, mcp, testing, fan, openspec-legacy, opsx/*, …). A skill may list **multiple** categories.

## Copying skills into another project

1. Browse `skills/<category>/README.md`.
2. Copy the skill folder into the target’s `.agents/skills/`.
3. Do not treat `skills/` as editable source.

## Testing Instructions

```bash
python3 .agents/skills/f-skills-catalog/scripts/sync.py validate
```

- Multi-category skills appear in every listed category with identical content.
- Ops skills do **not** appear under `skills/`.

## Pull Request / Commit Guidelines

- Commit messages: concise Chinese, focus on why.
- Before commit: catalog `validate` if catalog/skills/docs changed.
- Include source (`.agents/skills`, catalog, lock) and derived `skills/**` when sync output changes.
- Ask before amending or force-pushing; do not update git config.

## Additional Notes

- Overview: [README.md](README.md). Prefer this file + `skills/README.md` for agent truth.
- Reuse unchanged `contentHash` entries in `skill-docs.json` to avoid noisy diffs.
