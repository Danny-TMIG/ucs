---
id: ops.incident
tier: 6
owner: "@Danny-TMIG"
not_about:
  - Root-cause analysis
---

# Incident playbook

1. Freeze: revoke referenced keys.
2. Contain: disable push to main if integrity is in doubt.
3. Preserve: snapshot evidence before remediating.
4. Ticket: open GitHub Support.
5. Record: write evidence file with ticket, revocation date, revoking account.

## Verify

`ops/verification/verify-incident.sh <id>`. Exit 0 = closure recorded.
