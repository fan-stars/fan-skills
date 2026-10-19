---
name: f-openspec-profile-switch
description: Switches between legacy and opsx OpenSpec skill profiles across Cursor/Agents/Codex/Qoder scan roots using a central vault, parks inactive openspec roots under openspec-ref with README. Use when the user asks to switch OpenSpec profiles, init openspec profiles, park legacy/opsx skills, or mentions f-openspec-profile-switch / 切换 openspec / openspec 双套切换 / specs-only.
disable-model-invocation: true
---

# OpenSpec Profile Switch

Keeps **only one** OpenSpec skill set visible to agents at a time.

| Profile | Members |
|---------|---------|
| `legacy` | `openspec-archiving`, `openspec-context-loading`, `openspec-implementation`, `openspec-proposal-creation`, `openspec-proposal-creation-cn` |
| `opsx` | 12× `openspec-*` (explore/propose/apply-change/…) + all `superpowers-*` + matching commands |

This skill directory (`f-openspec-profile-switch`) is **never** parked.

## Layout

| Path | Role |
|------|------|
| `~/.openspec-profiles/` | Central vault (skills/commands Move target), `ACTIVE`, `managed-roots.json`, `LAST-SWITCH.log` |
| `<repo>/spec/` | **legacy** live root (operable when ACTIVE=legacy) |
| `<repo>/openspec/` | **opsx** live root (operable when ACTIVE=opsx) |
| `<repo>/openspec-ref/<profile>/` | Parked root + README — **reference only, do not operate** |
| Scan roots | Projection of the **active** profile skills on **user-global** roots only (`~/.cursor|agents|codex|qoder/skills`). Project `.cursor` is not used for opsx/superpowers. |

## Agent workflow

Copy this checklist:

```
- [ ] 1. Resolve workspace root (git root or cwd)
- [ ] 2. Run scripts/switch.py with the user intent
- [ ] 3. Show dry-run plan unless user passed --apply / confirm
- [ ] 4. After --apply (full switch): remind user to fully quit Cursor and open a new Agent chat
```

### Commands (run `scripts/switch.py`; do not hand-move folders)

```bash
# Status
python scripts/switch.py status --repo-root <repo>

# First-time: discover roots, Move both profiles into vault — does NOT activate
python scripts/switch.py init --repo-root <repo>
python scripts/switch.py init --repo-root <repo> --apply

# Switch skills + this repo's spec roots (default dry-run)
python scripts/switch.py switch opsx --repo-root <repo>
python scripts/switch.py switch legacy --repo-root <repo> --apply

# Multi-repo: only sync this repo's spec/openspec/openspec-ref (global skills + ACTIVE unchanged)
python scripts/switch.py switch opsx --repo-root <repo-b> --specs-only --apply
```

On Windows, `python` / `py` / `python3` are fine. There is no PowerShell wrapper — use `switch.py` only.

### Rules

1. Default is **dry-run**. Only `--apply` (or user saying confirm after seeing the plan) performs file ops.
2. After apply, print paths touched and point at `~/.openspec-profiles/LAST-SWITCH.log`.
3. Never edit parked trees under `openspec-ref/` except via this script’s switch/init.
4. If `managed-roots.json` is missing, run `init` before full `switch` (not needed for `--specs-only`).
5. Spec roots (different dirs per profile):
   - `legacy` ↔ `spec/`
   - `opsx` ↔ `openspec/`
   - Inactive profile’s live root is Moved to `openspec-ref/<profile>/` with README.
6. Park into vault uses **Move**; deploy onto many scan roots uses **Copy** from vault.
7. Use `--specs-only` when global skills are already on the desired profile and only this repo’s spec tree should change.

## Additional resources

- Membership lists, root candidates, command layouts: [reference.md](reference.md)
