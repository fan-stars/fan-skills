# Reference — f-openspec-profile-switch

## Fixed membership

### legacy skills

- `openspec-archiving`
- `openspec-context-loading`
- `openspec-implementation`
- `openspec-proposal-creation`
- `openspec-proposal-creation-cn`

### opsx skills

- `openspec-apply-change`
- `openspec-archive-change`
- `openspec-bulk-archive-change`
- `openspec-continue-change`
- `openspec-explore`
- `openspec-ff-change`
- `openspec-new-change`
- `openspec-onboard`
- `openspec-propose`
- `openspec-sync-specs`
- `openspec-update-change`
- `openspec-verify-change`
- all folders matching `superpowers-*`

### Never park / always online

- `f-openspec-profile-switch`

## Candidate scan roots

User skills: `~/.cursor/skills`, `~/.agents/skills`, `~/.codex/skills`, `~/.qoder/skills`, `~/.claude/skills`

User commands: `~/.cursor/commands`, `~/.agents/commands`, `~/.codex/commands`, `~/.qoder/commands`

Repo skills: `<repo>/.cursor/skills`, `<repo>/.agents/skills`, `<repo>/.codex/skills`, `<repo>/.qoder/skills`, `<repo>/.claude/skills`

Repo commands: `<repo>/.cursor/commands`, `<repo>/.qoder/commands`

**Managed set**: on `init`, skill **deploy** roots are **user-global only** (`~/.cursor|agents|codex|qoder/skills`). Project skill dirs may be scanned to park/scrub leftovers but are not deploy targets for opsx/superpowers. Command roots still follow discovery (may include repo `.cursor/commands`).

## Vault layout

```text
~/.openspec-profiles/
  ACTIVE                 # legacy | opsx | empty
  managed-roots.json
  LAST-SWITCH.log
  legacy/
    skills/<name>/
    commands/            # canonical nested: opsx/*.md, superpowers/*.md
  opsx/
    skills/<name>/
    commands/
```

## Command projection

| Tool | Layout when deploying |
|------|------------------------|
| Qoder (`**/.qoder/commands`) | Nested: `opsx/<cmd>.md`, `superpowers/<cmd>.md` |
| Cursor / others | Flat: `opsx-<cmd>.md`, `superpowers-<cmd>.md` |

Vault always stores **nested** canonical form.

## Spec roots (per profile — not the same directory)

| Profile | Live root | Parked at |
|---------|-----------|-----------|
| `legacy` | `<repo>/spec/` | `openspec-ref/legacy/` |
| `opsx` | `<repo>/openspec/` | `openspec-ref/opsx/` |

On switch to target T: park every non-T live root that exists; restore `openspec-ref/T/` → T’s live root when present.

Use `--specs-only` to run only this sync (no global skills / ACTIVE changes). Useful when another repo already set the global profile.

## Switch semantics

1. Dry-run unless `--apply`.
2. Park: **Move** any live legacy/opsx membership from managed roots → vault (duplicates already in vault are **Remove**d from scan roots).
3. Spec roots: **Move** inactive profile live dirs → `openspec-ref/<profile>/`, write READMEs; **Move** `openspec-ref/<target>/` → target live root when parked content exists.
4. Deploy: **Copy** vault `<target>/skills|commands` → each managed root (commands shaped per tool). Vault keeps the canonical tree.
5. Write `ACTIVE`, append `LAST-SWITCH.log` (skipped with `--specs-only`).
6. **Copy** `f-openspec-profile-switch` to managed user skill roots (skipped with `--specs-only`).
7. Implementation: `scripts/switch.py` only (cross-platform; no `.ps1` wrapper).
