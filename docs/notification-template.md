# Notification — ucs signing material disclosure

**Date:** 2026-10-20
**Repo:** github.com/Danny-TMIG/ucs
**Status:** Closed pending issuer-side revocation confirmation

## What happened
Historical commits `a20b6dd` and `c75dd26` contained HMAC signing keys and
signature files for two chain manifests (allwares, hood_compilers/chain).
These were rewritten out of history. Current `main` does not contain them and
all five paths return 404.

## Who is affected
No downstream consumers. No forks. No open PRs. No releases. No tags.
If you cloned ucs before <date> and hold a ref to `a20b6dd` or `c75dd26`,
delete that ref and re-clone.

## What was done
- History rewritten to remove the five paths
- Secret scanning + push protection enabled
- Pre-commit hook and CI check block the five paths
- GitHub Support request filed to purge server-side cached objects
- Keys rotated at issuer (confirm date)

## What you should do
- Delete any local ref to `a20b6dd` or `c75dd26`
- Re-clone from `main` if you hold an old checkout
- No action needed if you never had a copy

## Contact
Danny (Danny-TMIG) — danny@themarkintelligencegroup.com
