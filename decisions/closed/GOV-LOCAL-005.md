# GOV-LOCAL-005 — versioning policy closure

**Status:** Closed
**Date:** 2026-10-20
**spec change:** `spec/version.py` (semver compat check), `spec/migrate.py` (forward/backward migration)

## Decision
Versions are `MAJOR.MINOR.PATCH`. Breaking = MAJOR bump, requires `has_removal or has_type_change`. Additive = MINOR bump, requires `has_addition`. Migrations are named by `(from, to)` pair, forward and reverse, and always back up before writing.

## closure_vehicle
`spec/version.py` and `spec/migrate.py` enforce the policy; both run in `sdlc_gate`.

## Residual risk
Only two migration pairs exist (v1→v2, v2→v3). A new schema version needs a new named migration entry before the release that ships it.
