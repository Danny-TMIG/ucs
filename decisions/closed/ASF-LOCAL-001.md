---
id: ASF-LOCAL-001
tier: 7
status: closed
owner: "@Danny-TMIG"
opened: 2026-10-20
closed: 2026-10-20
spec_refs: [ASF-COG-FAS-001, ASF-GOV-FAS-001, ASF-CMP-FAS-001]
---

# ASF-LOCAL-001 — Repository state versus described architecture

## Question

The README describes a three-layer fabric with 75 components, three normative
specifications, a mathematics program, and a nine-bullet reference slice. The
repository contains three 26-line spec stubs, eighteen 7-line schema
skeletons, no implemented Govern or Compute components, and one CLI demo that
exercises the Cognition evidence path only. What is the honest relationship
between the README and the repository?

## Resolution

The README describes intended architecture. The repository implements one
narrow vertical slice of that architecture (the CLI demo). Every component
outside `tools/` is a stub. This is recorded so that no reader — including
the maintainer after a gap — mistakes the README for a description of the
current state.

## State at closure

- `specs/ASF-COG-FAS-001.md`, `specs/ASF-GOV-FAS-001.md`,
  `specs/ASF-CMP-FAS-001.md`: 26 lines each. Name the three layers, the
  invariants, and the boundary alignment. Do not enumerate 75 components, do
  not define the nine requirements per component, do not list the mathematics
  index.
- `specs/contracts/*.schema.json`: 18 files, 7 lines each. Assert
  envelope fields only. Do not constrain payload, do not define enums, do not
  validate cross-field invariants.
- `decisions/open/`: one decision (`GOV-DEC-001`). Twenty-one of the 22 named
  open decisions in the specs are not yet recorded as files.
- `decisions/closed/`: this file and `GOV-LOCAL-001`.
- `ops/runbooks/`: rotation, incident, merge. `merge.md` records that the
  ruleset cannot be toggled with the current token.
- `ci/docs-checks.py`: 15 checks, all passing. Checks assert structure; they
  do not assert that a spec is complete or a component is implemented.
- `tools/`: CLI demo of the Cognition evidence path. Not ASF. Not Govern.
  Not Compute.
- No tag, no release, no fork, one collaborator.

## Spec change carrying the resolution

`README.md` — added a "Current state" section immediately after the layer
diagram stating that the repository contains architectural stubs and one CLI
demo, and that the nine-bullet reference slice is not implemented. Added a
link to this decision.

## Evidence

- `wc -l specs/ASF-*-FAS-001.md` -> 26 each (recorded 2026-10-20).
- `wc -l specs/contracts/*.schema.json | tail -1` -> 18 files, 7 lines each.
- `ls decisions/open/*.md | wc -l` -> 1.
- `git ls-remote origin 'refs/tags/*'` -> empty.
- `gh api repos/Danny-TMIG/ucs/forks --jq 'length'` -> 0.

## What this decision does not say

It does not say the architecture is wrong. It says the architecture is
described and the implementation is not done. Those are different statements.

It does not say the CLI is not useful. It says the CLI is one slice.

It does not say the specs are worthless. It says the specs are stubs.

## Reopening conditions

This decision reopens and requires a follow-up when any of the following
becomes true:

- Any spec file grows beyond its stub content (component tables populated,
  nine requirements per component enumerated, mathematics index present).
- Any schema asserts more than the envelope.
- Any component outside `tools/` has a working implementation.
- Any of the nine vertical-slice bullets is implemented beyond the current
  subset (bullets 1, 2, 5, 6-informational, 9-simplified).

At that point this decision is superseded by a new closed decision naming
which component is implemented and which bullet it advances.

## Residual risk

A reader who opens the README but not the specs will believe the fabric
exists. This decision does not prevent that; only the README's "Current
state" section reduces the chance. No CI check enforces the correspondence
between README claims and spec length, because no such check exists yet.
