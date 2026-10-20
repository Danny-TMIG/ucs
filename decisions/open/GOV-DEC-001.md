---
id: GOV-DEC-001
tier: 7
status: open
owner: "@Danny-TMIG"
closure_vehicle: "cross-component interface specification (Tier 5 contracts revision)"
opened: 2026-10-20
spec_refs: [ASF-GOV-FAS-001, ASF-CMP-FAS-001]
---

# GOV-DEC-001 — Canonical transport and serialization

## Question

What is the canonical transport and serialization for boundary objects between
Cognition, Govern, and Compute?

Candidates under consideration:

- JSON Schema over HTTP/1.1 + TLS
- Protobuf over gRPC
- Dual representation (JSON Schema as normative, Protobuf as optional wire)

## Why it is open

The three specs name the boundary objects but do not prescribe the wire format.
`specs/contracts/*.schema.json` are JSON Schema today because JSON Schema is
the most portable normative representation. That is not the same as choosing a
transport.

The choice has consequences for:

- Idempotency-key handling at the transport layer
- Envelope signing (canonicalization is serialization-dependent)
- Error propagation (`ASFError` shape across transports)
- Federation wire protocol (`GOV-DEC-011`, deferred)

## What a resolution must satisfy

1. Canonical bytes for signing. Two conforming implementations must produce the
   same signature for the same object.
2. Streaming support for `ExecutionStatus` (Compute -> Govern).
3. No silent field dropping on decode.
4. Backward-compatible schema evolution.

## What is not decided by resolving this

- The schema shape (Tier 5).
- The envelope fields (Tier 3 + Tier 5).
- The set of boundary objects.

## Provisional direction (not a resolution)

JSON Schema as normative, with a canonical JSON serialization (RFC 8785 JCS)
for signature inputs. Protobuf may be added later as a lossless projection,
per the spec's "internal projections may add implementation detail but may not
expand authority" rule.

This is a candidate, not a closure. The decision remains open until a Tier 5
contracts revision lands.

## Consequences of deferring

No Cross-layer object can be signed and verified by a third party until this is
resolved. The reference vertical slice (bullet 9, "one complete evidence chain")
cannot be demonstrated end to end.
