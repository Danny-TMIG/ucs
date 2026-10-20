---
id: GOV-LOCAL-001
tier: 7
status: closed
owner: "@Danny-TMIG"
opened: 2026-10-19
closed: 2026-10-20
spec_refs: [ASF-GOV-FAS-001]
---

# GOV-LOCAL-001 — Single maintainer, self-approval, no downstream

## Question

Under what approval and notification configuration does v1 operate, given that
the repository has one maintainer, zero forks, zero downstream consumers, zero
releases, and zero tags?

## Resolution

The v1 reference domain is the sole maintainer, self-approving, with no
downstream notification obligation. This is recorded, not assumed.

## Spec change carrying the resolution

`specs/ASF-GOV-FAS-001.md` — the boundary alignment section now states that
approval and notification configuration are properties of the deployment
profile, not of the contract. Single-maintainer self-approval is a valid v1
profile; it would not be valid for any profile with additional principals.

## Evidence

- `gh api repos/Danny-TMIG/ucs/forks` returns `[]` (recorded at closure).
- `gh api repos/Danny-TMIG/ucs/collaborators` returns only `Danny-TMIG`.
- `gh api repos/Danny-TMIG/ucs/tags` returns `[]`.
- No `docs/notification-template.md` recipient list has ever been published.

## Residual risk

The self-approval path means an incident response that requires "two people"
cannot be executed as written. The `ops/runbooks/incident.md` playbook is
therefore single-operator by design. If a second maintainer is ever added,
this decision must be reopened and the runbook rewritten.

## Reopening conditions

- A second collaborator is added.
- A fork appears.
- A release is tagged.
- Any consumer outside the repository is identified.

Any of the above reopens this decision.
