# GitHub Support — Request to purge cached/dangling objects for Danny-TMIG/ucs

**Repository:** Danny-TMIG/ucs (public)
**Current main:** 41a712a, superseded by hardening commits through d315ea5
**Incident:** Signing material was committed in two historical commits and rewritten out of history via git filter-repo.

## Old commits (unreachable / 404)
- `a20b6dd` — initial import, contained signing keys
- `c75dd26` — cosmetic removal

## Leaked paths (all 404 on current main)
- allwares/KEY
- allwares/chain.sig
- allwares/chain.json
- hood_compilers/chain/KEY
- hood_compilers/chain/chain.sig

## Requests
1. Purge cached and dangling objects referencing `a20b6dd` or `c75dd26`.
2. Purge internal retention / reflog copies.
3. Confirm completion and whether any PR refs, tags, or forks point at those SHAs.

## Mitigations applied (verified via API)
- Secret scanning: enabled
- Secret scanning push protection: enabled
- Ruleset `block-signing-material` (id 25452273), active on `refs/heads/main`: deletion, non-fast-forward, required_signatures
- Branch protection on `main`: force-push disabled, deletion disabled
- `.pre-commit-config.yaml` hook `block-signing-material` blocks the five paths (verified: BLOCKED-allwares/KEY)
- CI: `pre-commit.yml`, `secret-scan.yml`, `rotation-reminder.yml`
- `.gitignore`: `**/KEY`, `**/*.sig`, `archives/`
- Forks: 0. Open PRs: 0. Tags: 0. Releases: 0.

## Keys
Rotated at issuer on request of repo owner. (Fill in issuer + date.)
