---
id: commentary.boundaries
tier: 4
owner: "@Danny-TMIG"
spec: [ASF-COG-FAS-001, ASF-GOV-FAS-001, ASF-CMP-FAS-001]
not_about:
  - New invariants
---

# Boundaries

Every boundary object carries envelope, idempotency key, classification, and evidence context. The system fails closed. Cancellation and revocation are observable state transitions. Producers own semantic validity at emission; consumers re-validate.
