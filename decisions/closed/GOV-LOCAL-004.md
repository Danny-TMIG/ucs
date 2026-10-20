# GOV-LOCAL-004 — state model closure

**Status:** Closed
**Date:** 2026-10-20
**spec change:** `spec/state.py` defines writers, readers, hashing, snapshot

## Decision
State lives in `build/_state/<key>.json`. Writers are `{loop, swarm, revise}`; readers are `{loop, swarm, revise, atlas, desk}`. Every write records `prev_hash` for tamper evidence.

## closure_vehicle
`spec/state.py` raises `PermissionError` for unauthorized writers/readers. `sdlc_gate` runs `state.py` as part of the test suite.

## Residual risk
`build/` is not itself versioned. State is per-machine. A multi-machine swarm needs a state backend decision.
