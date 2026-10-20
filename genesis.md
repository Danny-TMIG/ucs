# Genesis — the enumeration

Every failure class, sin, commandment, control, and authority in this repo is enumerated here.
Genesis is the ground truth. Bodies are the abstraction. Books are the narrative. Atlases are the index.

## Failure classes

| class | sin | risk (cost of failure) | reward (value of prevention) |
|-------|-----|------------------------|------------------------------|
| F1 stub-as-reasoning | Sloth | plan looks reasoned but is a stub; downstream build is wasted | every plan states source=model|stub |
| F2 capability-claim | Pride | substrate invokes without model; silent empty output | ModelUnavailable raised; caller decides |
| F3 content-laxity | Greed | code lands that passes tests but violates discipline | content gate rejects before merge |
| F4 arch-assertion | Wrath | "nine families" claimed by prose, never checked | arch-check proves each family exists |
| F5 recovery-arcana | Envy | incident response depends on knowing flags | one command for rollback |
| F6 gate-divergence | Gluttony | CI passes, local fails, or vice versa | CI sources the same file as local |
| F7 measurement-loss | Lust | compile-time measurements vanish after the run | ledger records every measurement |
| F8 infinite-partition | Idle worship | measurements with no regime partition | kaleidogami folds into 5 regimes |

## Ten commandments (control and authority)

| # | commandment | authority | control |
|---|-------------|-----------|---------|
| 1 | One command for undo | body.sdlc | ops/runbooks/rollback.md |
| 2 | Same gate local and CI | body.sdlc | .github/workflows/sdlc.yml |
| 3 | Refuse when incapable | body.reason, body.serve | ModelUnavailable, source=stub |
| 4 | Record every measurement | body.bound | bench/ledger.py |
| 5 | Partition the infinite | body.bound | bench/kaleidogami.py |
| 6 | Gate content, not tests | body.sdlc | ci/content-checks.py |
| 7 | Prove before claiming | body.sdlc | ci/arch-check.py |
| 8 | State the source of every answer | body.reason | reason() returns source |
| 9 | Reject bare except | body.sdlc | R3 in content-checks |
| 10 | Exact value, not membership | body.sdlc | R5 in content-checks |

## Enumerated objects

| id | kind | file | body | sin prevented |
|----|------|------|------|---------------|
| ucs.loop | module | spec/loop.py | body.loop | — |
| ucs.intent_schema | schema | specs/intent/intent.schema.json | body.payload | — |
| ucs.decide | module | spec/decide.py | body.decide | — |
| ucs.atlas | module | spec/atlas.py | body.atlas | — |
| ucs.invariants | module | spec/invariants.py | body.invariants | — |
| ucs.revise | module | spec/revise.py | body.revise | — |
| ucs.swarm | module | spec/swarm.py | body.swarm | — |
| ucs.desk | module | spec/desk.py | body.desk | — |
| ucs.nature | module | spec/nature.py | body.nature | — |
| ucs.mip | module | spec/mip.py | body.mip | — |
| ucs.mimc | module | spec/mimc.py | body.mimc | — |
| ucs.interface | module | spec/interface.py | body.interface | — |
| ucs.arch | module | spec/arch.py | body.arch | — |
| ucs.toy_model | module | spec/toy_model.py | body.arch | — |
| ucs.serve | module | spec/serve.py | body.serve | F2 Pride |
| ucs.llama_expert | module | spec/llama_expert.py | body.serve | F2 Pride |
| ucs.getgguf | tool | tools/getgguf.py | body.serve | — |
| ucs.reason | module | spec/reason.py | body.reason | F1 Sloth |
| ucs.murmur | module | spec/murmur.py | body.murmur | — |
| ucs.mesh | module | spec/mesh.py | body.mesh | — |
| ucs.payload | module | spec/payload.py | body.payload | — |
| ucs.payload_schema | schema | specs/contracts/payload.schema.json | body.payload | — |
| ucs.state | module | spec/state.py | body.state | — |
| ucs.version | module | spec/version.py | body.version | — |
| ucs.migrate | module | spec/migrate.py | body.version | — |
| ucs.bound | module | bench/bound.py | body.bound | — |
| ucs.ledger | module | bench/ledger.py | body.bound | F7 Lust |
| ucs.kaleidogami | module | bench/kaleidogami.py | body.bound | F8 Idle worship |
| ucs.sdlc | tool | tools/sdlc.sh | body.sdlc | F5 Envy |
| ucs.content_checks | tool | ci/content-checks.py | body.sdlc | F3 Greed |
| ucs.arch_check | tool | ci/arch-check.py | body.sdlc | F4 Wrath |
| ucs.correlate | tool | ci/correlate.py | body.sdlc | F6 Gluttony |
| ucs.runtime | contract | runtime.json | body.sdlc | — |
| ucs.rollback | runbook | ops/runbooks/rollback.md | body.sdlc | F5 Envy |
| ucs.ci_workflow | pipeline | .github/workflows/sdlc.yml | body.sdlc | F6 Gluttony |
