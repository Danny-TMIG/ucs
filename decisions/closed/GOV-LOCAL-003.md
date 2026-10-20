# GOV-LOCAL-003 — payload schema closure

**Status:** Closed
**Date:** 2026-10-20
**spec change:** adds `specs/contracts/payload.schema.json` ($defs for 6 message bodies); `spec/payload.py` validates them

## Decision
Every message body must validate against a `$defs` entry in `payload.schema.json`. Unknown body kinds are rejected. `additionalProperties: false` where the schema declares it.

## closure_vehicle
`spec/payload.py` enforces the schema; `sdlc_gate` runs `spec/payload.py` as part of the test suite.

## Residual risk
Fields with `additionalProperties: true` (execution_result, execution_order) permit extension by any writer. Lock them in a future decision.
