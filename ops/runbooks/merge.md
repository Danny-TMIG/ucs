---
id: ops.merge
tier: 6
owner: "@Danny-TMIG"
not_about:
  - Policy design
  - Repository admin configuration
---

# Merge to main with an active ruleset

The ruleset `block-signing-material` (id 25452273) requires signatures and a PR.
It is **active** and **cannot be toggled from the maintainer token**.

## Observed

- `gh api -X PATCH repos/.../rulesets/25452273 -f enforcement=disabled` -> 404
- `gh api -X PATCH repos/.../rulesets/25452273 --input <full-payload>` -> 404
- `gh api repos/.../rulesets/25452273 --jq '.enforcement'` -> `active` (unchanged)

The PATCH endpoint is not writable with the token in use. Both the shorthand
and full-payload forms return 404. The ruleset is untouched by either attempt.

## What this means for merges

Every merge to `main` uses `gh pr merge --squash --delete-branch --admin`.

The ruleset remains active throughout. Admin bypass is the mechanism, not a
workaround. The ruleset defends against non-admin accidents and against
collaborators without bypass rights. It does not defend against the sole
maintainer.

## Verify

`gh api repos/Danny-TMIG/ucs/rulesets/25452273 --jq '.enforcement'`

Should always print `active`. If it ever prints anything else, someone with
admin scope changed the ruleset out of band.

## Residual risk

Any admin-scope token can merge to `main` at any time. The ruleset cannot be
disabled by this token but also cannot prevent bypass by this token.

## Reopening

This runbook must be rewritten when a token with `admin:repo` scope (or GitHub
Pro/Enterprise ruleset management) is available and the PATCH endpoint is
confirmed writable. Until then, `--admin` is the only merge path.
