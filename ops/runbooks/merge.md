---
id: ops.merge
tier: 6
owner: "@Danny-TMIG"
not_about:
  - Policy design
---

# Merge to main with an active ruleset

The ruleset `block-signing-material` (id 25452273) requires signatures and a PR.
`gh pr merge --squash --delete-branch --admin` bypasses it. The three-step
disable→merge→re-enable pattern does NOT work: `gh api -X PATCH ... -f
enforcement=disabled` returns 404 because the ruleset endpoint requires the
full payload.

## Correct sequence

1. `gh api -X PATCH "repos/Danny-TMIG/ucs/rulesets/25452273" --input <full-payload-with-enforcement-disabled>`
2. Verify: `gh api repos/Danny-TMIG/ucs/rulesets/25452273 --jq '.enforcement'` must print `disabled`.
3. `gh pr merge --squash --delete-branch`
4. `gh api -X PATCH "repos/Danny-TMIG/ucs/rulesets/25452273" --input <full-payload-with-enforcement-active>`
5. Verify: `.enforcement` must print `active`.

## If step 1 fails

Use `--admin` and record the bypass in the PR body. The ruleset remains active
throughout; the merge happened because admin bypass, not because the ruleset was
disabled.

## Verify

`gh api repos/Danny-TMIG/ucs/rulesets/25452273 --jq '.enforcement'` — must match
intent (active after merge).
