DOMAINS = [
    "software-engineering","systems-engineering","security-engineering","data-engineering",
    "ml-ai-engineering","devops-sre","platform-engineering","quality-engineering",
    "compliance-engineering","observability-engineering","finops","governance",
    "risk-engineering","privacy-engineering","accessibility","internationalization",
    "documentation","api-design","database","network","supply-chain","release-engineering",
    "chaos-engineering","performance-engineering","capacity-engineering",
    "business-continuity","support-engineering","legal-contract",
]

FUNCTION_CATEGORIES = [
    "intent-intake","discovery-research","analysis-reasoning","planning",
    "architecture-design","specification-formalization","implementation",
    "transformation","review","verification-validation","debugging-repair",
    "security","operations","observability","governance-authority",
    "coordination","evidence-qualification","documentation-knowledge","stewardship",
]

SKILL_FAMILIES = [
    "intent","context","requirements","search-retrieval","repository-intelligence",
    "planning","architecture","modeling","formal-methods","coding",
    "language-engineering","programming-paradigms","algorithms","data-structures",
    "api-engineering","database","data-engineering","ai-ml","tensor-numerical",
    "distributed-systems","concurrency","operating-systems","firmware-embedded",
    "hardware-hdl","networking","web","mobile","desktop","cli-terminal",
    "build-systems","package-management","source-control","ci","cd-release",
    "containers","orchestration","infrastructure-as-code","cloud","edge",
    "identity","cryptography","application-security","security-testing",
    "threat-defense","zero-trust","sandbox-isolation","testing","performance",
    "reliability","observability","debugging","compatibility","migration",
    "configuration","secrets","policy","standards-compliance","governance",
    "evidence","provenance","qualification","artifact-management","documentation",
    "knowledge","memory","tooling","capability-management","skill-management",
    "agent-management","multi-agent-coordination","model-management","execution",
    "runtime-control","environment-management","resource-management","cost",
    "scheduling","messaging-events","integration","interoperability",
    "file-format-processing","serialization","media","spatial-3d",
    "scientific-computing","statistics","optimization","simulation","ui-ux",
    "accessibility","localization","quality","lifecycle","change-management",
    "incident-management","operations-management","product","project-program",
    "business","legal-ip-support","privacy","supply-chain","audit","recovery",
    "optimization-learning",
]

EXECUTION_OPS = [
    "identify","advertise-capabilities","inspect-capabilities","admit","reject",
    "constrain","authorize","decompose","select-skills","compose-skills",
    "select-tools","select-models","plan","schedule","allocate","route",
    "delegate","execute","observe","measure","inspect","compare","diagnose",
    "repair","retry","rollback","verify","validate","qualify","attest",
    "record-evidence","report","checkpoint","suspend","resume","cancel",
    "terminate","release-resources","archive",
]

GRANULARITY = [
    "atomic","primitive","composite","procedure","workflow","pipeline",
    "role","profession","domain","system","system-of-systems",
]

CONTRACT_FIELDS = [
    "identifier","version","description","capability","domain","subdomain",
    "operation","intent-types","input-types","output-types","preconditions",
    "postconditions","invariants","parameters","defaults","dependencies",
    "required-skills","optional-skills","incompatible-skills","tools","engines",
    "runtimes","models","platforms","architectures","environments",
    "permissions","authorities","resource-limits","time-limits","cost-limits",
    "network-policy","filesystem-policy","secret-policy","data-policy",
    "procedures","branches","checkpoints","cancellation","retries","rollback",
    "recovery","expected-failures","known-failures","failure-classes",
    "diagnostics","tests","regression-tests","benchmarks","evidence-requirements",
    "evidence-produced","provenance","qualification","compatibility",
    "portability","determinism","idempotency","reversibility","observability",
    "security-properties","safety-properties","privacy-properties",
    "compliance-mappings","standards-mappings","known-successes","known-limitations",
    "deprecation-state","replacement","owner","maintainer","created-at",
    "updated-at","signature","checksum",
]

ROUTING_DIMENSIONS = [
    "intent","capability","skill","operation","domain","target","artifact-type",
    "input-type","output-type","language","framework","runtime","operating-system",
    "processor-architecture","accelerator","environment","locality","connectivity",
    "authority","permission","security-classification","trust-level","evidence-level",
    "qualification-level","compatibility","latency","throughput","cost","energy",
    "memory","storage","network","reliability","determinism","reversibility",
    "risk","availability","specialization","historical-success","current-load",
    "resource-fit",
]

RESULT_STATES = [
    "PASS","FAIL","PARTIAL","UNKNOWN","NOT_RUN","BLOCKED","NOT_AUTHORIZED",
    "UNSUPPORTED","INCOMPATIBLE","INSUFFICIENT_DATA","INSUFFICIENT_EVIDENCE",
    "TIMEOUT","CANCELLED","RESOURCE_EXHAUSTED","POLICY_DENIED","SECURITY_DENIED",
    "QUALIFICATION_DENIED","DEPENDENCY_FAILURE","ENVIRONMENT_FAILURE","TOOL_FAILURE",
    "MODEL_FAILURE","EXECUTION_FAILURE","VERIFICATION_FAILURE","EXPIRED","DEPRECATED",
]

FLOW = [
    "interpret","parse","normalize","reconcile","mirror","formalize","discover",
    "decompose","map","search","select","compose","plan","constrain","authorize",
    "allocate","execute","observe","diagnose","repair","test","verify","validate",
    "qualify","attest","evidence","release","deploy","operate","monitor","learn",
]

def validate_domain(name):
    return [] if name in DOMAINS else [f"unknown domain {name!r}"]

def validate_function_category(name):
    return [] if name in FUNCTION_CATEGORIES else [f"unknown function category {name!r}"]

def validate_skill_family(name):
    return [] if name in SKILL_FAMILIES else [f"unknown skill family {name!r}"]

def validate_execution_op(name):
    return [] if name in EXECUTION_OPS else [f"unknown execution op {name!r}"]

def validate_granularity(name):
    return [] if name in GRANULARITY else [f"unknown granularity {name!r}"]

def validate_contract(contract):
    return [f"contract missing {m}" for m in CONTRACT_FIELDS if m not in contract]

def validate_result(state):
    return [] if state in RESULT_STATES else [f"unknown result state {state!r}"]

def validate_flow_step(name):
    return [] if name in FLOW else [f"unknown flow step {name!r}"]

def validate_route(route):
    return [f"unknown routing dim {k!r}" for k in route if k not in ROUTING_DIMENSIONS]

if __name__ == "__main__":
    assert validate_domain("software-engineering") == []
    assert validate_domain("nonsense")
    assert validate_function_category("intent-intake") == []
    assert validate_skill_family("formal-methods") == []
    assert validate_execution_op("qualify") == []
    assert validate_granularity("composite") == []
    assert validate_result("PASS") == []
    assert validate_result("MAYBE")
    assert validate_flow_step("interpret") == []
    assert validate_flow_step("nope")
    assert validate_contract({f: "" for f in CONTRACT_FIELDS}) == []
    assert validate_route({"intent": "x"}) == []
    assert validate_route({"nonsense": 1})
    print(f"atlas OK: {len(DOMAINS)} domains, {len(FUNCTION_CATEGORIES)} fn cats, "
          f"{len(SKILL_FAMILIES)} skill families, {len(EXECUTION_OPS)} ops, "
          f"{len(GRANULARITY)} granularities, {len(CONTRACT_FIELDS)} contract fields, "
          f"{len(ROUTING_DIMENSIONS)} routing dims, {len(RESULT_STATES)} results, "
          f"{len(FLOW)} flow steps")
