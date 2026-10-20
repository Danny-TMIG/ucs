"""derive.py — derive systemhood from the corpus, anchored to the glossary.

Sources:
  - the 546 artifacts already on disk (from orders.json)
  - the AI glossary (1000+ terms in ~/glossary.md)
  - the enterprise registry (102 files, labeled)

Output: systemhood.json — every artifact classified by which glossary
system it belongs to, plus a derivation of what "system" means across
the corpus.

A "system" is defined here as a triple (boundary, components, coupling)
where:
  boundary   = what is inside vs outside (input/output interface)
  components = the parts (files, modules, subsystems)
  coupling   = how components interact (imports, calls, data flow)

For each anchor term in the glossary, we derive: does a system exist on
disk that instantiates it?
"""

from __future__ import annotations
import hashlib, json, re, sys, time
from collections import defaultdict, Counter
from pathlib import Path
from dataclasses import dataclass, asdict, field

HOME = Path.home()
OUT = HOME / "ucs"
sys.path.insert(0, str(OUT))


# ── corpus ────────────────────────────────────────────────────────────
def load_corpus() -> list:
    """Load the artifact list from orders.json."""
    p = OUT / "orders.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text())
    return d.get("level0", {}).get("kinds", {})


def load_orders() -> dict:
    p = OUT / "orders.json"
    return json.loads(p.read_text()) if p.exists() else {}


def load_enterprise() -> dict:
    p = OUT / "enterprise" / "enterprise_registry.json"
    return json.loads(p.read_text()) if p.exists() else {}


# ── glossary ──────────────────────────────────────────────────────────
def extract_glossary_terms() -> list:
    """Read the pasted glossary text if available; otherwise use a
    compact hardcoded subset of the anchor terms."""
    p = HOME / "glossary.txt"
    if p.exists():
        text = p.read_text()
        # glossary entries look like: term\n  description
        terms = re.findall(r"^([a-zA-Z][a-zA-Z0-9 \-()/&]{2,60})$", text, re.MULTILINE)
        return sorted(set(t.strip() for t in terms if len(t.strip()) > 2))
    # fallback: the anchor terms from the pasted glossary
    return [
        "abductive reasoning",
        "ablation",
        "activation function",
        "adaptive algorithm",
        "agent architecture",
        "AI accelerator",
        "algorithm",
        "algorithmic efficiency",
        "answer set programming",
        "attention mechanism",
        "autoencoder",
        "automata theory",
        "automated planning",
        "automated reasoning",
        "autonomic computing",
        "backpropagation",
        "backward chaining",
        "bag-of-words",
        "batch normalization",
        "Bayesian programming",
        "behavior tree",
        "belief-desire-intention",
        "bias-variance tradeoff",
        "big data",
        "blackboard system",
        "Boltzmann machine",
        "boosting",
        "branching factor",
        "brute-force search",
        "capsule neural network",
        "case-based reasoning",
        "chatbot",
        "cloud robotics",
        "cluster analysis",
        "cognitive architecture",
        "cognitive computing",
        "combinatorial optimization",
        "committee machine",
        "commonsense reasoning",
        "computational complexity",
        "computational creativity",
        "computational intelligence",
        "computational learning theory",
        "computational linguistics",
        "computational neuroscience",
        "computer vision",
        "concept drift",
        "connectionism",
        "constraint logic programming",
        "constraint programming",
        "control theory",
        "convolutional neural network",
        "crossover",
        "Dartmouth workshop",
        "data augmentation",
        "data fusion",
        "data integration",
        "data mining",
        "data science",
        "data warehouse",
        "Datalog",
        "decision boundary",
        "decision support system",
        "decision theory",
        "decision tree learning",
        "declarative programming",
        "deductive classifier",
        "deep learning",
        "default logic",
        "description logic",
        "diffusion model",
        "dimensionality reduction",
        "discrete system",
        "distributed artificial intelligence",
        "double descent",
        "dropout",
        "dynamic epistemic logic",
        "eager learning",
        "early stopping",
        "echo state network",
        "embodied agent",
        "embodied cognitive science",
        "ensemble learning",
        "epoch",
        "evolutionary algorithm",
        "evolutionary computation",
        "expert system",
        "fast-and-frugal trees",
        "feature extraction",
        "feature learning",
        "feature selection",
        "federated learning",
        "first-order logic",
        "formal language",
        "forward chaining",
        "frame language",
        "frame problem",
        "fuzzy control system",
        "fuzzy logic",
        "fuzzy set",
        "game theory",
        "general game playing",
        "generalization",
        "generative adversarial network",
        "generative artificial intelligence",
        "genetic algorithm",
        "genetic operator",
        "gradient boosting",
        "graph database",
        "graph theory",
        "graph traversal",
        "hallucination",
        "heuristic",
        "hidden layer",
        "hyper-heuristic",
        "hyperparameter",
        "incremental learning",
        "inference engine",
        "information integration",
        "intelligent agent",
        "intelligent control",
        "intrinsic motivation",
        "junction tree algorithm",
        "kernel method",
        "KL-ONE",
        "k-nearest neighbors",
        "knowledge acquisition",
        "knowledge-based system",
        "knowledge distillation",
        "knowledge engineering",
        "knowledge extraction",
        "knowledge representation",
        "k-means clustering",
        "language model",
        "large language model",
        "lazy learning",
        "logic programming",
        "long short-term memory",
        "machine vision",
        "Markov chain",
        "Markov decision process",
        "mathematical optimization",
        "machine learning",
        "machine listening",
        "machine perception",
        "mechanism design",
        "mechatronics",
        "metaheuristic",
        "model checking",
        "modus ponens",
        "modus tollens",
        "Monte Carlo tree search",
        "multi-agent system",
        "multilayer perceptron",
        "multi-swarm optimization",
        "mutation",
        "naive Bayes classifier",
        "naive semantics",
        "name binding",
        "named-entity recognition",
        "named graph",
        "natural language generation",
        "natural language processing",
        "natural language programming",
        "network motif",
        "neural machine translation",
        "neural network",
        "neural Turing machine",
        "neuro-fuzzy",
        "neurocybernetics",
        "neuromorphic engineering",
        "node",
        "nondeterministic algorithm",
        "nouvelle AI",
        "NP",
        "NP-completeness",
        "NP-hardness",
        "Occam's razor",
        "offline learning",
        "online machine learning",
        "ontology learning",
        "OpenAI",
        "OpenCog",
        "Open Mind Common Sense",
        "open-source software",
        "overfitting",
        "partial order reduction",
        "partially observable Markov decision process",
        "particle swarm optimization",
        "pathfinding",
        "pattern recognition",
        "perceptron",
        "predicate logic",
        "predictive analytics",
        "principal component analysis",
        "principle of rationality",
        "probabilistic programming",
        "production system",
        "programming language",
        "Prolog",
        "propositional calculus",
        "proximal policy optimization",
        "Python",
        "PyTorch",
        "Q-learning",
        "qualification problem",
        "quantifier",
        "quantum computing",
        "query language",
        "R programming language",
        "radial basis function network",
        "random forest",
        "reasoning system",
        "recurrent neural network",
        "regression analysis",
        "regularization",
        "reinforcement learning",
        "reinforcement learning from human feedback",
        "reservoir computing",
        "Resource Description Framework",
        "restricted Boltzmann machine",
        "Rete algorithm",
        "robotics",
        "rule-based system",
        "satisfiability",
        "search algorithm",
        "selection",
        "self-management",
        "semantic network",
        "semantic reasoner",
        "semantic query",
        "semantics",
        "semi-supervised learning",
        "sensor fusion",
        "separation logic",
        "similarity learning",
        "simulated annealing",
        "situated approach",
        "situation calculus",
        "SLD resolution",
        "software",
        "software engineering",
        "spatial-temporal reasoning",
        "SPARQL",
        "sparse dictionary learning",
        "speech recognition",
        "spiking neural network",
        "state",
        "statistical classification",
        "SARSA",
        "statistical relational learning",
        "stochastic optimization",
        "stochastic semantic analysis",
        "STRIPS",
        "subject-matter expert",
        "superintelligence",
        "supervised learning",
        "support vector machines",
        "swarm intelligence",
        "symbolic artificial intelligence",
        "synthetic intelligence",
        "systems neuroscience",
        "technological singularity",
        "temporal difference learning",
        "tensor network theory",
        "TensorFlow",
        "theoretical computer science",
        "theory of computation",
        "Thompson sampling",
        "time complexity",
        "transfer learning",
        "transformer",
        "transhumanism",
        "transition system",
        "tree traversal",
        "true quantified Boolean formula",
        "Turing machine",
        "Turing test",
        "type system",
        "unsupervised learning",
        "vision processing unit",
        "Watson",
        "weak AI",
        "word embedding",
        "XGBoost",
    ]


# ── systemhood definition ─────────────────────────────────────────────
@dataclass
class Systemhood:
    term: str
    boundary: str  # does a file implement an interface for this?
    components: list  # which files instantiate it
    coupling: str  # how tightly coupled (0 = none, 3 = strong)
    evidence: list  # which files contain this term


def classify(term: str, artifacts: list, texts: dict) -> Systemhood:
    """For a glossary term, check if any artifact instantiates it."""
    lower = term.lower()
    hits = []
    for path in artifacts:
        text = texts.get(path, "")
        if lower in text.lower() or lower.replace(" ", "_") in path.lower():
            hits.append(path)
    boundary = "present" if hits else "absent"
    # coupling heuristic: multiple hits across different top-level dirs
    dirs = set(Path(h).parts[0] for h in hits if len(Path(h).parts) > 0)
    if len(dirs) >= 3:
        coupling = 3
    elif len(dirs) >= 2:
        coupling = 2
    elif len(dirs) == 1:
        coupling = 1
    else:
        coupling = 0
    return Systemhood(
        term=term,
        boundary=boundary,
        components=hits[:10],
        coupling=coupling,
        evidence=hits[:5],
    )


# ── main ──────────────────────────────────────────────────────────────
def main():
    print("== derive systemhood ==")
    print()

    orders = load_orders()
    ent = load_enterprise()

    # all artifacts from orders + enterprise
    artifacts = set()
    for f in ent.get("per_file", []):
        artifacts.add(f["path"])
    for d, files in orders.get("level1", {}).get("dir_groups", {}).items():
        # orders.json didn't store the file list; use enterprise paths
        pass

    # read artifact texts
    texts = {}
    roots = [
        "foundations",
        "swarm",
        "gen",
        "kaleido",
        "ucs",
        "vem-index",
        "polyglot",
        "cs-partitions",
        "enterprise",
        "systems",
    ]
    for root in roots:
        r = HOME / root
        if not r.exists():
            continue
        for p in sorted(r.rglob("*")):
            if "__pycache__" in str(p) or not p.is_file():
                continue
            if p.suffix not in {".py", ".md", ".txt", ".sh", ".json"}:
                continue
            try:
                text = p.read_text(errors="ignore")[:16384]
                rel = str(p.relative_to(HOME))
                texts[rel] = text
                artifacts.add(rel)
            except OSError:
                pass

    print(f"artifacts scanned: {len(artifacts)}")

    terms = extract_glossary_terms()
    print(f"glossary terms:    {len(terms)}")
    print()

    # derive systemhood for each term
    derivations = []
    for t in terms:
        sh = classify(t, list(artifacts), texts)
        derivations.append(asdict(sh))

    present = [d for d in derivations if d["boundary"] == "present"]
    absent = [d for d in derivations if d["boundary"] == "absent"]
    strong = [d for d in derivations if d["coupling"] >= 2]

    print(f"terms with system on disk:  {len(present)}")
    print(f"terms without:              {len(absent)}")
    print(f"strongly coupled systems:   {len(strong)}")
    print()

    print("== terms instantiated by a system on disk (top 30) ==")
    for d in sorted(present, key=lambda x: -x["coupling"])[:30]:
        print(f"  {d['coupling']}  {d['term']:40s} {len(d['components'])} files")

    # write the derivation
    out = OUT / "systemhood.json"
    out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "artifacts_scanned": len(artifacts),
                "terms_analyzed": len(terms),
                "terms_present": len(present),
                "terms_absent": len(absent),
                "strongly_coupled": len(strong),
                "derivations": derivations,
            },
            indent=2,
        )
    )
    print()
    print(f"wrote: {out}")
    print(
        f"  {len(derivations)} derivations, {len(present)} present, "
        f"{len(absent)} absent, {len(strong)} strong"
    )


if __name__ == "__main__":
    main()
