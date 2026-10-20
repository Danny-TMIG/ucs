---
id: orientation.reading-paths
tier: 2
owner: "@Danny-TMIG"
not_about:
  - Content of the paths (that lives in each target document)
---

Reading paths

Path A - First contributor (30 minutes)

1. `README.md`
2. `docs/orientation/overview.md`
3. `docs/orientation/glossary.md`
4. `specs/ASF-COG-FAS-001.md` section 1-3
5. `specs/ASF-COG-FAS-001.md` section 17 (vertical slice)
6. `decisions/open/`

You can now name the three layers, the invariant, the v1 target, and the open decisions.

Path B - First implementer (2 hours)

1. Path A
2. `specs/ASF-GOV-FAS-001.md` section 3-8
3. `specs/ASF-CMP-FAS-001.md` section 3-10
4. `docs/commentary/boundaries.md`
5. `specs/contracts/index.md`
6. `decisions/closed/`

You can now name every mandatory boundary object and begin implementing any component against its contract.

Path C - Auditor (1 hour)

1. Path A
2. `specs/ASF-GOV-FAS-001.md` section 3
3. `specs/ASF-CMP-FAS-001.md` section 3
4. `specs/ASF-COG-FAS-001.md` section 10
5. `evidence/`
6. `decisions/closed/`

You can now reconstruct incident history, name mitigations, cite evidence.

Path D - Operator (45 minutes)

1. `docs/orientation/overview.md`
2. `ops/runbooks/rotation.md`
3. `ops/runbooks/incident.md`
4. `specs/ASF-CMP-FAS-001.md` section 12
5. `ops/verification/`

You can now rotate material, respond to an incident, and cancel an order.

Path E - Integrator (1 hour)

1. Path A
2. `specs/contracts/index.md`
3. `specs/ASF-GOV-FAS-001.md` section 6
4. `specs/ASF-GOV-FAS-001.md` Boundary Contract Alignment
5. `specs/ASF-CMP-FAS-001.md` Boundary Contract Alignment
6. `docs/commentary/boundaries.md`

You can now implement the boundary contracts for one object end to end.
