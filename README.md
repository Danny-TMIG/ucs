# Aether Sovereign Fabric (ASF)

**Aether is a three-component sovereign intelligence fabric with a working command-line demonstration.** The CLI is the smallest complete path through the system; the three specifications define the full architecture it is a slice of.

\`\`\`
            ┌─────────────────────────────────────────────────────┐
            │  Aether Cognition           21 components           │
            └─────────────────────────────────────────────────────┘
                                    │ proposes
                                    ▼
            ┌─────────────────────────────────────────────────────┐
            │  Aether Govern              24 components           │
            └─────────────────────────────────────────────────────┘
                                    │ ExecutionOrder
                                    ▼
            ┌─────────────────────────────────────────────────────┐
            │  Aether Compute             30 components           │
            └─────────────────────────────────────────────────────┘
\`\`\`

**The invariant that defines the product:** Cognition proposes. Govern authorizes and coordinates. Compute qualifies and realizes. No component may grant itself the authority owned by another.

The three specification documents are normative at the functional-architecture level:

| Layer | Document | Component count |
|---|---|---|
| Cognition | \`ASF-COG-FAS-001 v1.0\` | 21 |
| Govern | \`ASF-GOV-FAS-001 v1.0\` | 24 |
| Compute | \`ASF-CMP-FAS-001 v1.0\` | 30 |

Language, database, model family, cloud, hardware vendor, and deployment packaging are **not prescribed**.

---

## Start with the CLI (five minutes)

The \`aether\` CLI is a working demonstration of the Cognition-to-Evidence path: one intent produces code, execution, and a signed trace that anyone can verify without your model, your network, or your machine.

\`\`\`bash
git clone <your-fork-url> aether
cd aether
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e tools

aether run "count the words in postgres"
aether verify-trace .ai/trace/<file>.json
maintained attest
\`\`\`

**What the CLI is:** a vertical-slice reference implementation of the Cognition evidence path (\`COG-ASSUR-001\`, \`COG-ASSUR-002\`). A trace is a simplified projection of what the full spec calls cognitive evidence.

**What the CLI is not:** ASF. It does not implement Govern. It does not implement Compute. Its \`.ai/trace/\` file is not the cross-layer \`EvidenceEnvelope\`. Anyone comparing the CLI to the specs should treat the CLI as a working excerpt, not as the architecture.

**Requirements:** macOS 14+ on Apple Silicon (M1–M4), Python 3.11/3.12, ≥16 GB RAM, ≥8 GB disk. \`verify-trace\` works on any platform.

Full CLI reference — all verbs, sandboxing, hosting patterns, non-Apple paths, troubleshooting — see [\`tools/README.md\`](tools/README.md).

---

## Read the specs in this order

Each layer has its own responsibilities, failure model, and evidence obligations. Read in lifecycle order.

### 1. Aether Cognition — \`ASF-COG-FAS-001 v1.0\`

Sovereign intelligence. Preserves cognitive continuity across interactions and substrate change. Assimilates authorized knowledge into typed cognitive state. Composes reasoning and planning. Proposes responses and actions. Learns only through controlled, attributable adaptation.

21 components across five families:
- Interaction and Human Control (3): \`COG-INT-001\` – \`003\`
- Cognitive Runtime, State and Memory (3): \`COG-CORE-001\` – \`003\`
- Knowledge, Reasoning, Planning (6): \`COG-CORE-004\`, \`COG-REA-001\` – \`005\`
- Models, Skills, Cognitive Composition (5): \`COG-CMP-001\` – \`005\`
- Assurance, Security, Performance (4): \`COG-ASSUR-001\` – \`004\`

**Boundary:** Cognition owns cognitive identity continuity, cognitive state, memory, representations, deliberation, proposals, cognitive evidence, and controlled adaptation. It does not own authentication, authorization, constitutional policy, information-flow permission, capability eligibility, physical resource qualification, scheduling, attestation, or execution.

### 2. Aether Govern — \`ASF-GOV-FAS-001 v1.0\`

Coordination and governance. Determines whether proposed use of identity, information, capabilities, and consequential action is permitted. Attaches enforceable obligations. Coordinates approved action with Compute. Reconciles returned evidence into a governed outcome.

24 components across eight groups:
- Governance Kernel (3): \`GOV-KRN-001\` – \`003\`
- Identity and Authority (4): \`GOV-IAM-001\` – \`004\`
- Policy (3): \`GOV-POL-001\` – \`003\`
- Information Governance (5): \`GOV-INF-001\` – \`005\`
- Capability Coordination (3): \`GOV-CAP-001\` – \`003\`
- Evidence and Assurance (3): \`GOV-EVD-001\` – \`003\`
- Administration and Operations (2): \`GOV-ADM-001\` – \`002\`
- Federation and Domain Exchange (1): \`GOV-FED-001\`

**Boundary:** Govern owns permission to know or act. It cannot reason, plan, learn, or execute. It cannot represent scheduling as authority. It cannot broaden Cognition's proposals; it can only allow, deny, condition, escalate, or return indeterminate.

### 3. Aether Compute — \`ASF-CMP-FAS-001 v1.0\`

Trusted computational realization. Accepts bounded execution orders issued through Govern. Qualifies hardware. Resolves topology. Reserves resources. Realizes workloads through controlled native systems. Observes and recovers execution. Returns evidence sufficient for Govern to verify and close the governed outcome.

30 components across seven families:
- Contract and Control (4): \`CMP-CTL-001\` – \`004\`
- Trust and Security (6): \`CMP-TRU-001\` – \`006\`
- Topology and Resources (7): \`CMP-RES-001\` – \`007\`
- Workload and Execution (7): \`CMP-EXE-001\` – \`007\`
- Data and Connectivity (2): \`CMP-DAT-001\` – \`002\`
- Observation and Evidence (3): \`CMP-EVD-001\` – \`003\`
- Economics (1): \`CMP-ECO-001\` (validation-gated)

**Boundary:** Compute owns eligibility and realization. It cannot broaden authority, relax policy, alter information flow, or substitute a capability outside the governed set. Mandatory conditions are conjunctive.

---

## The canonical end-to-end lifecycle

1. **Cognition** receives authenticated session context and validates the request envelope
2. **Cognition** represents intent: source, scope, classification, constraints
3. **Cognition** resolves exact cognitive-state and memory versions
4. **Cognition** obtains authorized governed knowledge references (via Govern, via \`KnowledgeAccessRequest\`)
5. **Cognition** filters candidate cognitive approaches by eligibility and ranks them
6. **Cognition** executes and composes bounded cognitive transformations
7. **Cognition** constructs bounded plans, dependencies, capabilities, budgets
8. **Cognition** evaluates quality, uncertainty, evidence, verification, escalation
9. **Cognition** presents a nonconsequential response, or…
10. **Cognition** creates a typed capability request (via Govern, via \`CapabilityRequest\`)
11. **Govern** resolves identity, authority, classification, policy, information flow, capability eligibility
12. **Govern** obtains human decision where required
13. **Govern** issues a signed, bounded, time-limited \`ExecutionOrder\` to Compute
14. **Compute** validates, qualifies hardware, resolves topology, reserves, schedules, executes
15. **Compute** observes, recovers if needed, and returns evidence to Govern
16. **Govern** verifies the result against the order
17. **Govern** emits \`GovernedOutcome\` and \`CognitiveStateUpdateDirective\`
18. **Cognition** commits the authorized state update
19. **Evidence** is sealed on both sides; the full chain is reconstructible

**No step can be skipped. No layer can perform another layer's step.**

---

## The canonical boundary contracts

Defined in \`40_CROSS_STACK_INTEGRATION/05_Canonical_Schemas\`. These have precedence over any internal naming when an object crosses a layer boundary.

| Boundary | Cognition sends | Govern sends | Compute sends |
|---|---|---|---|
| Knowledge | \`KnowledgeAccessRequest\` | \`GovernedKnowledgeResult\` | — |
| Authority | — | \`AuthorizationRequest\` / \`AuthorizationDecision\` | — |
| Capabilities | \`CapabilityRequest\` | \`GovernedCapabilitySet\` | — |
| Execution | — | \`ExecutionOrder\` | \`ExecutionStatus\`, \`ExecutionResult\`, \`ExecutionEvidence\` |
| Human control | \`HumanControlPresentation\` | \`ApprovalRequest\` / \`HumanDecisionSubmission\` | — |
| Closure | \`CognitiveStateUpdateDirective\` | \`GovernedOutcome\` | — |
| Control | \`CancellationRevocationDirective\`, \`ASFError\` | same | same |

**Every boundary object carries:** schema version, correlation, causation, sovereign-domain, purpose, classification, integrity, evidence context.

**Every retry uses a stable idempotency key.** Duplicate delivery may not duplicate authority, state mutation, execution, or evidence commitment.

**Every expired, revoked, malformed, unsupported, unsigned, or context-inconsistent object fails closed** for consequential action.

---

## The v1 reference vertical slice

1. One authenticated user and workspace with a stable cognitive identity binding
2. One versioned cognitive-state store and working, episodic, and semantic memory with provenance
3. One governed knowledge source accessed through Govern
4. At least two heterogeneous cognitive substrates behind one adapter contract
5. One bounded reasoning and planning path with evaluation and uncertainty
6. One informational response **and** one consequential capability requiring human + Govern authorization
7. One Compute execution with execution evidence returned through Govern
8. One state update, one injected failure, one recovery or terminal failure, one replay/evaluation record
9. One complete evidence chain from intent to governed outcome and cognitive-state update

**Where the CLI fits:** bullets 1, 2, 5, 6 (informational half only), and 9 (simplified). Bullets 3, 4, 6 (consequential half), 7, and 8 are not in the CLI.

---

## What is normative, what is research

**Research-gated, non-normative in v1:**
- Swarms (\`COG-CMP-004\`)
- Genesis-derived weighted ethics grammar (\`GOV-DEC-013\`)
- 48-dimensional topology (\`CMP-DEC-006\`)
- Trust-gradient / graded arity thresholds (\`CMP-DEC-007\`)
- SHGP and novel secure execution (\`CMP-DEC-019\`)
- QPU / hybrid execution (\`CMP-DEC-018\`)
- Economic optimizer production calibration (\`CMP-DEC-015\`)
- All \`COG-MATH-*\`, \`GOV-MATH-*\`, \`CMP-MATH-*\` claims below their stated M-gate

**Normative and required in v1:** every component marked \`Core v1\` in the three specifications' appendices, plus every boundary contract and invariant listed above.

---

## Open decisions block v1 scope

22 open decisions. Release gates, not TODOs.

**Cognition:** \`002\` identity lifecycle, \`003\` consistency, \`004\` memory consolidation, \`005\` memory deletion, \`017\` performance targets, \`018\` calibration targets.

**Govern:** \`001\` transport/serialization, \`002\` persistence, \`003\` credentials, \`004\` policy language, \`005\` classification lattice, \`006\` Liquid Aperture assurance, \`007\` evidence storage, \`008\` revocation latency, \`009\` SLO/scale, \`010\` reference domain.

**Compute:** \`001\` serialization, \`002\` control-plane consistency, \`003\` deployment topology, \`004\` workload formats, \`005\` platform support, \`008\` confidential compute, \`009\` artifact formats, \`010\` secret provider, \`011\` storage/networking, \`012\` quota policy, \`013\` checkpoint portability, \`014\` evidence store, \`016\` SLO targets.

**Deferred out of v1:** \`GOV-DEC-011\` federation wire protocol, \`GOV-DEC-012\` marketplace, \`CMP-DEC-017\` direct cross-domain execution, \`CMP-DEC-018\` QPU.

No implementation may resolve an open decision without the closure vehicle named in the corresponding spec.

---

## Contributing

1. **Read the layer spec for the component you are touching.** The unit of work is the component ID (\`GOV-INF-003\`, \`CMP-EXE-005\`, \`COG-REA-002\`).
2. **Do not cross layers.** If your change makes Cognition authorize, Govern execute, or Compute reinterpret policy, it fails conformance.
3. **Fulfill the boundary contract.** Every object you emit across a layer boundary carries the full envelope. Every consequential action is fail-closed. Every terminal outcome has reconstructible evidence.
4. **Respect the gates.** Research mechanisms are non-normative. Open decisions are open. Math claims have maturity gates.
5. **Match the vertical slice.** If your work does not advance one of the nine bullets, it is not in v1.
6. **Do not describe the CLI as ASF.** If you are working on \`tools/\`, you are working on a demonstration. Say so.

---

## What is not in scope for v1

- Direct cross-domain resource execution (\`CMP-DEC-017\`)
- Production Global ASF federation wire protocol (\`GOV-DEC-011\`)
- Capability marketplace (\`GOV-DEC-012\`)
- A validated universal ethics calculus (\`GOV-DEC-013\`)
- A mandatory CAPSTONE ledger or consensus claim (Compute §14)
- QPU and hybrid execution (\`CMP-DEC-018\`)
- Swarms (\`COG-CMP-004\`)

---

## Links

**Normative specifications:**
- \`ASF-COG-FAS-001 v1.0\` — Aether Cognition
- \`ASF-GOV-FAS-001 v1.0\` — Aether Govern
- \`ASF-CMP-FAS-001 v1.0\` — Aether Compute

**Cross-layer contracts:**
- \`40_CROSS_STACK_INTEGRATION/05_Canonical_Schemas/\`
- Component Assignment Matrix

**Mathematics program:**
- \`COG-MATH-*\`, \`GOV-MATH-*\`, \`CMP-MATH-*\` work packages

**The CLI:**
- \`tools/\` — installable demo package
- \`tools/README.md\` — scoped CLI reference
