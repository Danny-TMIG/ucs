Genesis — the enumeration

Every failure class, sin, commandment, control, and authority in this repo is enumerated here.
Genesis is the ground truth. Bodies are the abstraction. Books are the narrative. Atlases are the index.

Failure classes

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

Ten commandments (control and authority)

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

Enumerated objects

| id | kind | file | body |
|----|------|------|------|
| ucs.spec_arch | module | spec/arch.py | body.loop |
| ucs.spec_atlas | module | spec/atlas.py | body.loop |
| ucs.spec_callable | contract | spec/callable.yaml | body.loop |
| ucs.spec_compile | module | spec/compile.py | body.loop |
| ucs.spec_decide | module | spec/decide.py | body.loop |
| ucs.spec_decompose | module | spec/decompose.py | body.loop |
| ucs.spec_desk | module | spec/desk.py | body.loop |
| ucs.spec_execute | module | spec/execute.py | body.loop |
| ucs.spec_artifact | module | spec/experts/artifact.py | body.loop |
| ucs.spec_constraint | module | spec/experts/constraint.py | body.loop |
| ucs.spec_domain | module | spec/experts/domain.py | body.loop |
| ucs.spec_evidence | module | spec/experts/evidence.py | body.loop |
| ucs.spec_interface | module | spec/interface.py | body.loop |
| ucs.spec_invariants | module | spec/invariants.py | body.loop |
| ucs.spec_llama_expert | module | spec/llama_expert.py | body.loop |
| ucs.spec_loop | module | spec/loop.py | body.loop |
| ucs.spec_memo | module | spec/memo.py | body.loop |
| ucs.spec_mesh | module | spec/mesh.py | body.loop |
| ucs.spec_migrate | module | spec/migrate.py | body.loop |
| ucs.spec_mimc | module | spec/mimc.py | body.loop |
| ucs.spec_mip | module | spec/mip.py | body.loop |
| ucs.spec_murmur | module | spec/murmur.py | body.loop |
| ucs.spec_nature | module | spec/nature.py | body.loop |
| ucs.spec_parallel_check | module | spec/parallel_check.py | body.loop |
| ucs.spec_payload | module | spec/payload.py | body.loop |
| ucs.spec_post_verify | tool | spec/post-verify.sh | body.loop |
| ucs.spec_reason | module | spec/reason.py | body.loop |
| ucs.spec_revise | module | spec/revise.py | body.loop |
| ucs.spec_rotate_issuer | tool | spec/rotate-issuer.sh | body.loop |
| ucs.spec_run | tool | spec/run.sh | body.loop |
| ucs.spec_serve | module | spec/serve.py | body.loop |
| ucs.spec_state | module | spec/state.py | body.loop |
| ucs.spec_swarm | module | spec/swarm.py | body.loop |
| ucs.spec_toy_model | module | spec/toy_model.py | body.loop |
| ucs.spec_validate | module | spec/validate.py | body.loop |
| ucs.spec_verify | tool | spec/verify.sh | body.loop |
| ucs.spec_verify_boundary | module | spec/verify_boundary.py | body.loop |
| ucs.spec_version | module | spec/version.py | body.loop |
| ucs.spec_experts_artifact | module | spec/experts/artifact.py | body.desk |
| ucs.spec_experts_constraint | module | spec/experts/constraint.py | body.desk |
| ucs.spec_experts_domain | module | spec/experts/domain.py | body.desk |
| ucs.spec_experts_evidence | module | spec/experts/evidence.py | body.desk |
| ucs.auth_approval | module | auth/approval.py | body.sdlc |
| ucs.auth_member | module | auth/member.py | body.sdlc |
| ucs.enterprise_classify | module | enterprise/classify.py | body.enterprise |
| ucs.enterprise_enterprise_registry | schema | enterprise/enterprise_registry.json | body.enterprise |
| ucs.enterprise_frameworks | module | enterprise/frameworks.py | body.enterprise |
| ucs.enterprise_score | module | enterprise/score.py | body.enterprise |
| ucs.enterprise_scored | schema | enterprise/scored.json | body.enterprise |
| ucs.bench_bound | module | bench/bound.py | body.bound |
| ucs.bench_kaleidogami | module | bench/kaleidogami.py | body.bound |
| ucs.bench_ledger | module | bench/ledger.py | body.bound |
| ucs.ci_arch_check | module | ci/arch-check.py | body.sdlc |
| ucs.ci_content_checks | module | ci/content-checks.py | body.sdlc |
| ucs.ci_correlate | module | ci/correlate.py | body.sdlc |
| ucs.ci_docs_checks | module | ci/docs-checks.py | body.sdlc |
| ucs.tools_getgguf | module | tools/getgguf.py | body.sdlc |
| ucs.tools_sdlc | tool | tools/sdlc.sh | body.sdlc |
| ucs.body_body_arch | schema | standards/bodies/body.arch.json | body.sdlc |
| ucs.body_body_atlas | schema | standards/bodies/body.atlas.json | body.sdlc |
| ucs.body_body_bound | schema | standards/bodies/body.bound.json | body.sdlc |
| ucs.body_body_decide | schema | standards/bodies/body.decide.json | body.sdlc |
| ucs.body_body_desk | schema | standards/bodies/body.desk.json | body.sdlc |
| ucs.body_body_enterprise | schema | standards/bodies/body.enterprise.json | body.sdlc |
| ucs.body_body_interface | schema | standards/bodies/body.interface.json | body.sdlc |
| ucs.body_body_invariants | schema | standards/bodies/body.invariants.json | body.sdlc |
| ucs.body_body_loop | schema | standards/bodies/body.loop.json | body.sdlc |
| ucs.body_body_mesh | schema | standards/bodies/body.mesh.json | body.sdlc |
| ucs.body_body_mimc | schema | standards/bodies/body.mimc.json | body.sdlc |
| ucs.body_body_mip | schema | standards/bodies/body.mip.json | body.sdlc |
| ucs.body_body_murmur | schema | standards/bodies/body.murmur.json | body.sdlc |
| ucs.body_body_nature | schema | standards/bodies/body.nature.json | body.sdlc |
| ucs.body_body_payload | schema | standards/bodies/body.payload.json | body.sdlc |
| ucs.body_body_reason | schema | standards/bodies/body.reason.json | body.sdlc |
| ucs.body_body_revise | schema | standards/bodies/body.revise.json | body.sdlc |
| ucs.body_body_sdlc | schema | standards/bodies/body.sdlc.json | body.sdlc |
| ucs.body_body_serve | schema | standards/bodies/body.serve.json | body.sdlc |
| ucs.body_body_state | schema | standards/bodies/body.state.json | body.sdlc |
| ucs.body_body_swarm | schema | standards/bodies/body.swarm.json | body.sdlc |
| ucs.body_body_version | schema | standards/bodies/body.version.json | body.sdlc |
| ucs.book_arch | contract | standards/books/arch.md | body.sdlc |
| ucs.book_bound | contract | standards/books/bound.md | body.sdlc |
| ucs.book_controls | contract | standards/books/controls.md | body.sdlc |
| ucs.book_desk | contract | standards/books/desk.md | body.sdlc |
| ucs.book_enterprise | contract | standards/books/enterprise.md | body.sdlc |
| ucs.book_loop | contract | standards/books/loop.md | body.sdlc |
| ucs.book_nature | contract | standards/books/nature.md | body.sdlc |
| ucs.book_payload | contract | standards/books/payload.md | body.sdlc |
| ucs.book_sdlc | contract | standards/books/sdlc.md | body.sdlc |
| ucs.book_the_fabric | contract | standards/books/the-fabric.md | body.sdlc |
| ucs.atlas_atlas_core | schema | standards/atlases/atlas.core.json | body.sdlc |
| ucs.specs_intent_intent_schema | schema | specs/intent/intent.schema.json | body.payload |
| ucs.specs_contract_approval_request_schema | schema | specs/contracts/approval-request.schema.json | body.payload |
| ucs.specs_contract_asf_error_schema | schema | specs/contracts/asf-error.schema.json | body.payload |
| ucs.specs_contract_authorization_decision_schema | schema | specs/contracts/authorization-decision.schema.json | body.payload |
| ucs.specs_contract_authorization_request_schema | schema | specs/contracts/authorization-request.schema.json | body.payload |
| ucs.specs_contract_cancellation_revocation_directive_schema | schema | specs/contracts/cancellation-revocation-directive.schema.json | body.payload |
| ucs.specs_contract_capability_request_schema | schema | specs/contracts/capability-request.schema.json | body.payload |
| ucs.specs_contract_cognitive_state_update_directive_schema | schema | specs/contracts/cognitive-state-update-directive.schema.json | body.payload |
| ucs.specs_contract_execution_evidence_schema | schema | specs/contracts/execution-evidence.schema.json | body.payload |
| ucs.specs_contract_execution_order_schema | schema | specs/contracts/execution-order.schema.json | body.payload |
| ucs.specs_contract_execution_result_schema | schema | specs/contracts/execution-result.schema.json | body.payload |
| ucs.specs_contract_execution_status_schema | schema | specs/contracts/execution-status.schema.json | body.payload |
| ucs.specs_contract_governed_capability_set_schema | schema | specs/contracts/governed-capability-set.schema.json | body.payload |
| ucs.specs_contract_governed_outcome_schema | schema | specs/contracts/governed-outcome.schema.json | body.payload |
| ucs.specs_contract_human_decision_submission_schema | schema | specs/contracts/human-decision-submission.schema.json | body.payload |
| ucs.specs_contract_index | contract | specs/contracts/index.md | body.payload |
| ucs.specs_contract_information_flow_decision_schema | schema | specs/contracts/information-flow-decision.schema.json | body.payload |
| ucs.specs_contract_information_flow_request_schema | schema | specs/contracts/information-flow-request.schema.json | body.payload |
| ucs.specs_contract_payload_schema | schema | specs/contracts/payload.schema.json | body.payload |
| ucs.specs_contract_policy_evaluation_request_schema | schema | specs/contracts/policy-evaluation-request.schema.json | body.payload |
| ucs.specs_contract_representation_request_schema | schema | specs/contracts/representation-request.schema.json | body.payload |
| ucs.specs_asf_cog | contract | specs/ASF-COG-FAS-001.md | body.loop |
| ucs.specs_asf_gov | contract | specs/ASF-GOV-FAS-001.md | body.sdlc |
| ucs.specs_asf_cmp | contract | specs/ASF-CMP-FAS-001.md | body.arch |
| ucs.nature_catalog | data | data/nature.txt | body.nature |
| ucs.decision_asf_local_001 | decision | decisions/closed/ASF-LOCAL-001.md | body.sdlc |
| ucs.decision_gov_local_001 | decision | decisions/closed/GOV-LOCAL-001.md | body.sdlc |
| ucs.decision_gov_local_003 | decision | decisions/closed/GOV-LOCAL-003.md | body.sdlc |
| ucs.decision_gov_local_004 | decision | decisions/closed/GOV-LOCAL-004.md | body.sdlc |
| ucs.decision_gov_local_005 | decision | decisions/closed/GOV-LOCAL-005.md | body.sdlc |
| ucs.decision_gov_dec_001 | decision | decisions/open/GOV-DEC-001.md | body.sdlc |
| ucs.genesis | contract | genesis.md | body.sdlc |
| ucs.runtime_contract | contract | runtime.json | body.sdlc |
