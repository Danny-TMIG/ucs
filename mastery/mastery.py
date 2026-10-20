"""mastery.py — the finite set of callables every taxonomy attaches to."""

# The eleven primitives. Every behavior in G, C, R, D, B, K taxonomies is a
# composition of these. Nothing in any taxonomy names a behavior that is not.
PRIMITIVES = {
    "read":     "acquire bytes/state from a source",
    "write":    "emit bytes/state to a sink",
    "parse":    "bytes -> typed structure",
    "resolve":  "typed structure -> typed structure with references bound",
    "validate": "typed structure -> [] | [error]",
    "transform": "typed structure -> typed structure",
    "execute":  "typed structure -> result",
    "observe":  "result -> evidence",
    "decide":   "evidence + policy -> verdict",
    "persist":  "typed structure -> durable state",
    "publish":  "durable state -> external sink",
}

# The nine taxonomies. Each is a list of behaviors.
TAXONOMIES = {
    "generator": [
        "bootstrap","parse","analyze","transform","synthesize","emit",
        "validate","execute","coordinate","observe","persist","publish",
        "self-evolve",
    ],
    "compiler": [
        "bootstrap","frontend","semantic","ir","analyze","optimize",
        "transform","backend","link","verify","artifact","runtime-prep",
        "incremental","distributed","diagnostics","publication","self-host",
    ],
    "resolver": [
        "bootstrap","identity","namespace","type","symbol","dependency",
        "constraint","semantic","graph","reference","resource","environment",
        "version","execution","conflict","validation","publication","self",
    ],
    "daemon": [
        "bootstrap","filesystem","build","registry","dependency","compiler",
        "generator","validation","conformance","runtime","scheduler","cache",
        "index","logging","metrics","publication","synchronization","security",
        "orchestration","self-hosting",
    ],
    "binary": [
        "bootstrap","executable","object","library","intermediate","loader",
        "linker","runtime","service","generator","compiler","validation",
        "packaging","deployment","inspection","security","monitoring","storage",
        "network","self-hosting",
    ],
    "kernel": [
        "bootstrap","process","thread","memory","scheduling","synchronization",
        "ipc","filesystem","device","network","security","resource","execution",
        "compiler","generator","build","conformance","publication",
        "orchestration","self-hosting",
    ],
    "agent": [
        "intent-intake","discovery","analysis","planning","architecture",
        "specification","implementation","transformation","review","verification",
        "debugging","security","operations","observability","governance",
        "coordination","evidence","documentation","stewardship",
    ],
    "skill": [
        "intent","context","requirements","search","repository","planning",
        "architecture","modeling","formal","coding","language","paradigm",
        "algorithm","structure","api","database","data","ai-ml","tensor",
        "distributed","concurrency","os","firmware","hardware","network",
        "web","mobile","desktop","cli","build","package","vcs","ci","cd",
        "container","orchestration","iac","cloud","edge","identity","crypto",
        "appsec","sectest","threat","zero-trust","sandbox","testing",
        "performance","reliability","observability","debugging","compatibility",
        "migration","config","secrets","policy","standards","governance",
        "evidence","provenance","qualification","artifact","documentation",
        "knowledge","memory","tooling","capability","skill","agent",
        "coordination","model","execution","runtime","environment","resource",
        "cost","scheduling","messaging","integration","interoperability",
        "file","serialization","media","spatial","scientific","statistics",
        "optimization","simulation","ui","accessibility","localization",
        "quality","lifecycle","change","incident","operations","product",
        "project","business","legal","privacy","supply-chain","audit",
        "recovery","learning",
    ],
    "atlas": [
        "software-engineering","systems-engineering","security-engineering",
        "data-engineering","ml-ai-engineering","devops-sre","platform-engineering",
        "quality-engineering","compliance-engineering","observability-engineering",
        "finops","governance","risk-engineering","privacy-engineering",
        "accessibility","internationalization","documentation","api-design",
        "database","network","supply-chain","release-engineering",
        "chaos-engineering","performance-engineering","capacity-engineering",
        "business-continuity","support-engineering","legal-contract",
    ],
}

# The mapping: every taxonomy behavior -> the primitive sequence it composes to.
MAPPING = {
    "generator.bootstrap":     ["read","parse","execute","validate"],
    "generator.parse":         ["read","parse"],
    "generator.analyze":       ["parse","transform","validate"],
    "generator.transform":     ["transform"],
    "generator.synthesize":    ["transform","write"],
    "generator.emit":          ["write"],
    "generator.validate":      ["validate"],
    "generator.execute":       ["execute"],
    "generator.coordinate":    ["execute","observe"],
    "generator.observe":       ["observe"],
    "generator.persist":       ["persist"],
    "generator.publish":       ["publish"],
    "generator.self-evolve":   ["read","parse","transform","execute","write"],

    "compiler.bootstrap":      ["read","parse","execute"],
    "compiler.frontend":       ["read","parse","validate"],
    "compiler.semantic":       ["parse","resolve","validate"],
    "compiler.ir":             ["transform","write"],
    "compiler.analyze":        ["parse","transform"],
    "compiler.optimize":       ["transform"],
    "compiler.transform":      ["transform"],
    "compiler.backend":        ["transform","write"],
    "compiler.link":           ["read","write"],
    "compiler.verify":         ["validate"],
    "compiler.artifact":       ["write","persist"],
    "compiler.runtime-prep":   ["transform","write"],
    "compiler.incremental":    ["persist","read"],
    "compiler.distributed":    ["execute","coordinate"] if False else ["execute","observe"],
    "compiler.diagnostics":    ["observe","write"],
    "compiler.publication":    ["publish","write"],
    "compiler.self-host":      ["read","parse","execute","write"],

    "resolver.bootstrap":      ["read","parse","persist"],
    "resolver.identity":       ["resolve"],
    "resolver.namespace":      ["resolve"],
    "resolver.type":           ["resolve","validate"],
    "resolver.symbol":         ["resolve"],
    "resolver.dependency":     ["resolve","validate"],
    "resolver.constraint":     ["resolve","validate"],
    "resolver.semantic":       ["resolve","validate"],
    "resolver.graph":          ["resolve","transform"],
    "resolver.reference":      ["resolve"],
    "resolver.resource":       ["resolve"],
    "resolver.environment":    ["read","resolve"],
    "resolver.version":        ["resolve","validate"],
    "resolver.execution":      ["resolve","execute"],
    "resolver.conflict":       ["validate","decide"],
    "resolver.validation":     ["validate"],
    "resolver.publication":    ["resolve","write"],
    "resolver.self":           ["read","resolve","validate"],

    "daemon.bootstrap":        ["read","execute","persist"],
    "daemon.filesystem":       ["observe","execute"],
    "daemon.build":            ["execute","persist"],
    "daemon.registry":         ["read","validate","write"],
    "daemon.dependency":       ["read","validate","persist"],
    "daemon.compiler":         ["execute","observe"],
    "daemon.generator":        ["observe","execute","write"],
    "daemon.validation":       ["validate","observe"],
    "daemon.conformance":      ["execute","observe"],
    "daemon.runtime":          ["execute","observe","persist"],
    "daemon.scheduler":        ["decide","execute"],
    "daemon.cache":            ["persist","read"],
    "daemon.index":            ["transform","persist"],
    "daemon.logging":          ["observe","write"],
    "daemon.metrics":          ["observe","write"],
    "daemon.publication":      ["publish","write"],
    "daemon.synchronization":  ["read","write","resolve"],
    "daemon.security":         ["validate","decide"],
    "daemon.orchestration":    ["decide","execute","observe"],
    "daemon.self-hosting":     ["execute","validate","persist"],

    "binary.bootstrap":        ["read","execute"],
    "binary.executable":       ["write"],
    "binary.object":           ["write"],
    "binary.library":          ["write"],
    "binary.intermediate":     ["write"],
    "binary.loader":           ["read","execute"],
    "binary.linker":           ["read","write"],
    "binary.runtime":          ["execute"],
    "binary.service":          ["execute","observe"],
    "binary.generator":        ["transform","write"],
    "binary.compiler":         ["read","parse","transform","write"],
    "binary.validation":       ["validate"],
    "binary.packaging":        ["write","persist"],
    "binary.deployment":       ["publish"],
    "binary.inspection":       ["read","parse","observe"],
    "binary.security":         ["validate","write"],
    "binary.monitoring":       ["observe","write"],
    "binary.storage":          ["read","write","persist"],
    "binary.network":          ["read","write","execute"],
    "binary.self-hosting":     ["read","execute","validate"],

    "kernel.bootstrap":        ["read","execute","persist"],
    "kernel.process":          ["execute","decide"],
    "kernel.thread":           ["execute","decide"],
    "kernel.memory":           ["read","write","persist"],
    "kernel.scheduling":       ["decide","execute"],
    "kernel.synchronization":  ["execute","observe"],
    "kernel.ipc":              ["read","write","observe"],
    "kernel.filesystem":       ["read","write","persist"],
    "kernel.device":           ["read","write","execute"],
    "kernel.network":          ["read","write","execute"],
    "kernel.security":         ["validate","decide"],
    "kernel.resource":         ["decide","persist"],
    "kernel.execution":        ["execute","observe"],
    "kernel.compiler":         ["read","parse","transform","write"],
    "kernel.generator":        ["execute","write"],
    "kernel.build":            ["execute","persist"],
    "kernel.conformance":      ["execute","observe","validate"],
    "kernel.publication":      ["publish","write"],
    "kernel.orchestration":    ["decide","execute","observe"],
    "kernel.self-hosting":     ["read","execute","validate","persist"],

    "agent.intent-intake":     ["read","parse","transform"],
    "agent.discovery":         ["read","observe"],
    "agent.analysis":          ["parse","transform","validate"],
    "agent.planning":          ["transform","write"],
    "agent.architecture":      ["transform","write"],
    "agent.specification":     ["transform","write","validate"],
    "agent.implementation":    ["transform","write"],
    "agent.transformation":    ["transform"],
    "agent.review":            ["read","validate"],
    "agent.verification":      ["validate"],
    "agent.debugging":         ["read","observe","transform"],
    "agent.security":          ["validate","decide"],
    "agent.operations":        ["execute","observe"],
    "agent.observability":     ["observe","write"],
    "agent.governance":        ["validate","decide"],
    "agent.coordination":      ["decide","execute"],
    "agent.evidence":          ["observe","write","persist"],
    "agent.documentation":     ["transform","write"],
    "agent.stewardship":       ["read","validate","write"],

    "skill.intent":            ["read","parse","transform"],
    "skill.context":           ["read","transform","persist"],
    "skill.requirements":      ["parse","transform","validate"],
    "skill.search":            ["read","resolve"],
    "skill.repository":        ["read","parse","transform"],
    "skill.planning":          ["transform","write"],
    "skill.architecture":      ["transform","write"],
    "skill.modeling":          ["transform","write"],
    "skill.formal":            ["transform","validate"],
    "skill.coding":            ["transform","write"],
    "skill.language":          ["parse","transform"],
    "skill.paradigm":          ["read","transform","write"],

    "skill.algorithm":         ["transform"],
    "skill.structure":         ["transform"],
    "skill.api":               ["read","write"],
    "skill.database":          ["read","write","persist"],
    "skill.data":              ["read","transform","write"],
    "skill.ai-ml":             ["read","transform","execute"],
    "skill.tensor":            ["transform","execute"],
    "skill.distributed":       ["decide","execute","observe"],
    "skill.concurrency":       ["execute","observe"],
    "skill.os":                ["execute","persist"],
    "skill.firmware":          ["read","write","execute"],
    "skill.hardware":          ["read","write"],
    "skill.network":           ["read","write","execute"],
    "skill.web":               ["read","write","execute"],
    "skill.mobile":            ["read","write","execute"],
    "skill.desktop":           ["read","write","execute"],
    "skill.cli":               ["read","write","execute"],
    "skill.build":             ["execute","persist"],
    "skill.package":           ["read","write","persist"],
    "skill.vcs":               ["read","write","persist"],
    "skill.ci":                ["execute","observe"],
    "skill.cd":                ["execute","publish"],
    "skill.container":         ["write","execute"],
    "skill.orchestration":     ["decide","execute"],
    "skill.iac":               ["transform","execute"],
    "skill.cloud":             ["read","write","execute"],
    "skill.edge":              ["read","execute"],
    "skill.identity":          ["validate","decide"],
    "skill.crypto":            ["read","write","validate"],
    "skill.appsec":            ["validate","decide"],
    "skill.sectest":           ["execute","validate"],
    "skill.threat":            ["read","validate"],
    "skill.zero-trust":        ["validate","decide"],
    "skill.sandbox":           ["execute","observe"],
    "skill.testing":           ["execute","observe"],
    "skill.performance":       ["execute","observe"],
    "skill.reliability":       ["execute","observe"],
    "skill.observability":     ["observe","write"],
    "skill.debugging":         ["read","observe","transform"],
    "skill.compatibility":     ["validate"],
    "skill.migration":         ["transform","write"],
    "skill.config":            ["read","write"],
    "skill.secrets":           ["write","persist"],
    "skill.policy":            ["read","validate","decide"],
    "skill.standards":         ["read","validate"],
    "skill.governance":        ["validate","decide"],
    "skill.evidence":          ["observe","write","persist"],
    "skill.provenance":        ["read","observe","persist"],
    "skill.qualification":     ["validate","decide"],
    "skill.artifact":          ["read","write","persist"],
    "skill.documentation":     ["transform","write"],
    "skill.knowledge":         ["read","transform","persist"],
    "skill.memory":            ["read","write","persist"],
    "skill.tooling":           ["read","execute","observe"],
    "skill.capability":        ["read","validate","execute"],
    "skill.skill":             ["read","validate","write"],
    "skill.agent":             ["decide","execute"],
    "skill.coordination":      ["decide","execute"],
    "skill.model":             ["read","execute","observe"],
    "skill.execution":         ["execute","observe"],
    "skill.runtime":           ["execute","observe"],
    "skill.environment":       ["read","write","execute"],
    "skill.resource":          ["decide","persist"],
    "skill.cost":              ["observe","decide"],
    "skill.scheduling":        ["decide","execute"],
    "skill.messaging":         ["read","write","execute"],
    "skill.integration":       ["read","write"],
    "skill.interoperability":  ["read","transform","validate"],
    "skill.file":              ["read","write"],
    "skill.serialization":     ["parse","transform","write"],
    "skill.media":             ["read","transform","write"],
    "skill.spatial":           ["read","transform","write"],
    "skill.scientific":        ["execute","observe","write"],
    "skill.statistics":        ["observe","decide"],
    "skill.optimization":      ["transform","decide"],
    "skill.simulation":        ["execute","observe"],
    "skill.ui":                ["read","write"],
    "skill.accessibility":     ["validate"],
    "skill.localization":      ["read","transform","write"],
    "skill.quality":           ["observe","validate"],
    "skill.lifecycle":         ["decide","execute"],
    "skill.change":            ["read","validate","write"],
    "skill.incident":          ["observe","decide","write"],
    "skill.operations":        ["execute","observe","persist"],
    "skill.product":           ["read","decide","write"],
    "skill.project":           ["decide","execute"],
    "skill.business":          ["read","observe","decide"],
    "skill.legal":             ["read","validate"],
    "skill.privacy":           ["validate","decide"],
    "skill.supply-chain":      ["read","validate","persist"],
    "skill.audit":             ["observe","write","persist"],
    "skill.recovery":          ["read","execute","persist"],
    "skill.learning":          ["observe","transform","persist"],

    "atlas.software-engineering":        ["read","parse","write","validate"],
    "atlas.systems-engineering":         ["read","write","validate"],
    "atlas.security-engineering":        ["validate","decide"],
    "atlas.data-engineering":            ["read","transform","write"],
    "atlas.ml-ai-engineering":           ["read","execute","observe"],
    "atlas.devops-sre":                  ["execute","observe","persist"],
    "atlas.platform-engineering":        ["read","write","execute"],
    "atlas.quality-engineering":         ["validate","observe"],
    "atlas.compliance-engineering":      ["validate","decide","write"],
    "atlas.observability-engineering":   ["observe","write"],
    "atlas.finops":                      ["observe","decide"],
    "atlas.governance":                  ["validate","decide"],
    "atlas.risk-engineering":            ["observe","decide"],
    "atlas.privacy-engineering":         ["validate","decide"],
    "atlas.accessibility":               ["validate"],
    "atlas.internationalization":        ["transform","write"],
    "atlas.documentation":               ["transform","write"],
    "atlas.api-design":                  ["read","write"],
    "atlas.database":                    ["read","write","persist"],
    "atlas.network":                     ["read","write","execute"],
    "atlas.supply-chain":                ["read","validate","persist"],
    "atlas.release-engineering":         ["write","publish","persist"],
    "atlas.chaos-engineering":           ["execute","observe"],
    "atlas.performance-engineering":     ["execute","observe"],
    "atlas.capacity-engineering":        ["observe","decide","persist"],
    "atlas.business-continuity":         ["read","execute","persist"],
    "atlas.support-engineering":         ["observe","write"],
    "atlas.legal-contract":              ["read","validate"],
}


def validate_mapping(taxonomy):
    """Every behavior in the taxonomy must have a mapping; every mapped
    primitive must be a real primitive."""
    if taxonomy not in TAXONOMIES:
        return [f"unknown taxonomy {taxonomy!r}"]
    errs = []
    for b in TAXONOMIES[taxonomy]:
        key = f"{taxonomy}.{b}"
        if key not in MAPPING:
            errs.append(f"{key}: no mapping")
            continue
        for prim in MAPPING[key]:
            if prim not in PRIMITIVES:
                errs.append(f"{key}: unknown primitive {prim!r}")
    return errs


def validate_all():
    errs = []
    for t in TAXONOMIES:
        errs.extend(validate_mapping(t))
    return errs


def callable_for(taxonomy, behavior):
    """Return the primitive sequence that composes to the behavior."""
    key = f"{taxonomy}.{behavior}"
    if key not in MAPPING:
        raise KeyError(key)
    return list(MAPPING[key])


if __name__ == "__main__":
    errs = validate_all()
    assert errs == [], errs[:10]
    total = sum(len(v) for v in TAXONOMIES.values())
    mapped = len(MAPPING)
    print(f"mastery OK: {len(PRIMITIVES)} primitives, {len(TAXONOMIES)} taxonomies, "
          f"{total} behaviors, {mapped} mapped, 0 gaps")
    assert callable_for("generator","parse") == ["read","parse"]
    assert callable_for("compiler","self-host") == ["read","parse","execute","write"]
    assert callable_for("resolver","conflict") == ["validate","decide"]
    assert callable_for("daemon","scheduler") == ["decide","execute"]
    assert callable_for("binary","runtime") == ["execute"]
    assert callable_for("kernel","memory") == ["read","write","persist"]
    assert callable_for("agent","governance") == ["validate","decide"]
    assert callable_for("skill","crypto") == ["read","write","validate"]
    assert callable_for("atlas","security-engineering") == ["validate","decide"]
    print("mapping spot-checks OK")
