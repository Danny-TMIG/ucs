# Incident close checklist — ucs signing material

## A. Code surface
- [x] Old SHAs `a20b6dd`, `c75dd26` 404 via REST API
- [x] Five leaked paths 404 on main
- [x] Hook blocks the five paths (BLOCKED-allwares/KEY)
- [x] CI `secret-scan.yml`, `pre-commit.yml` active
- [x] `.gitignore` covers `**/KEY`, `**/*.sig`, `archives/`
- [x] `UCS_CHAIN_DIR` honored; worktree leak check empty

## B. GitHub settings
- [x] secret_scanning: enabled
- [x] secret_scanning_push_protection: enabled
- [x] ruleset 25452273 active on refs/heads/main
- [x] branch protection: force_push=false, deletions=false
- [ ] enforce_admins=true (blocked: free plan)

## C. Issuer-side
- [ ] Key revoked at issuer (attach receipt)
- [ ] New key issued (attach key id)
- [ ] `UCS_ISSUER=kms|vault|hsm make rotate-issuer` succeeds
- [ ] `spec/verify.sh` passes against new key

## D. GitHub Support
- [ ] `make support-ticket` submitted
- [ ] Ticket number: ______
- [ ] Support confirms object purge for `a20b6dd` and `c75dd26`
- [ ] Support confirms no remaining PR/tag/fork refs

## E. Notification
- [x] No downstream consumers, forks, PRs, tags, releases
- [ ] `docs/notification-template.md` published or recorded as no-op

## F. Post-close
- [ ] `docs/rotation-runbook.md` "Last rotation" replaced with real timestamp
- [ ] Checklist closed with date + signer
