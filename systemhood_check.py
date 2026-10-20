"""systemhood_check.py — derive systemhood against the -Hood taxonomy,
excluding the taxonomy files themselves from evidence.
"""

from __future__ import annotations
import json, re, sys, time
from pathlib import Path

HOME = Path.home()
OUT = HOME / "ucs"

HOODS = {
    "Thinghood": ("Being an entity", "Every generated artifact"),
    "Relationhood": ("Being between entities", "Every connection"),
    "Processhood": ("Unfolding over time", "The generative loop"),
    "Eventhood": ("A discrete occurrence", "Each observation"),
    "Boundaryhood": ("Distinguishing inside from outside", "Every scale boundary"),
    "Scalehood": ("Magnitude or level", "Powers of ten, layers"),
    "Directionhood": ("Orientation in space", "Up, down, in, out"),
    "Connectionhood": ("Linkage", "All connections"),
    "Bridgehood": ("Crossing between domains", "Translators, adapters"),
    "Interfacehood": ("Point of interaction", "APIs, boundaries"),
    "Adapterhood": ("Transforming while connecting", "CSV->Parquet"),
    "Invarianthood": ("Persisting across transformation", "The invariants"),
    "Changehood": ("Difference over time", "Learning, evolving"),
    "Memoryhood": ("Persisting state", "Content-addressed cache"),
    "Intenthood": ("Directedness toward future", "Goals"),
    "Attentionhood": ("Focused presence", "What we observe"),
    "Silencehood": ("The ground before generation", "Rest, pause"),
    "Sparkhood": ("The persistent curiosity", "What asks next?"),
    "Regrethood": ("The felt weight of cycles", "Honesty about cost"),
    "Trusthood": ("Confidence without proof", "Peer verification"),
    "Riskhood": ("Uncertainty with consequence", "Proto-solver precompute"),
    "Valuehood": ("Worth in context", "Per transaction"),
    "Meaninghood": ("Significance beyond utility", "Why we want"),
    "Questionhood": ("The act of asking", "The only thing that doesn't stop"),
    "Answerhood": ("Temporary closure", "What dissolves"),
    "Patternhood": ("Recurring structure", "The cycle observed"),
    "Instancehood": ("A specific occurrence", "Each tool, each dependency"),
    "Codehood": ("Executable text", "The medium"),
    "Datahood": ("Observed fact", "What we hash and cache"),
    "Algorithmhood": ("Step-by-step transformation", "The loop as procedure"),
    "Runtimehood": ("Execution environment", "The kernel, the process"),
    "Peerhood": ("Equal participant", "Every node, every user"),
    "Narrativehood": ("Story over time", "The ten-year observation"),
    "Metahood": ("Self-reference", "The loop observing itself"),
    "Dissolutionhood": ("The end of fixed points", "What makes it generative"),
}

EXCLUDE = (
    "systemhood.json",
    "systemhood_check.py",
    "derive.py",
    "glossary",
    "orders.json",
    "registry.json",
    "manifest.json",
)


def read_artifact(p: Path, n: int = 16384) -> str:
    try:
        return p.read_text(errors="ignore")[:n]
    except OSError:
        return ""


def collect_artifacts() -> dict:
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
            sp = str(p)
            if any(
                x in sp
                for x in ("__pycache__", "/vem/store/objects/", "/site-packages/")
            ):
                continue
            if not p.is_file():
                continue
            if any(x in sp for x in EXCLUDE):
                continue
            if p.suffix not in {".py", ".md", ".txt", ".sh", ".json"}:
                continue
            try:
                texts[str(p.relative_to(HOME))] = read_artifact(p)
            except OSError:
                pass
    return texts


def classify_hood(name: str, definition: str, texts: dict) -> dict:
    lower = name.lower()
    evidence = []
    for path, text in texts.items():
        t = text.lower()
        if lower in t:
            in_ident = bool(re.search(r"\b" + re.escape(lower) + r"\b\s*[=(:]", t))
            evidence.append({"path": path, "in_identifier": in_ident})
    anchored = len(evidence) >= 2 or any(e["in_identifier"] for e in evidence)
    return {
        "hood": name,
        "definition": definition,
        "anchored": anchored,
        "evidence_count": len(evidence),
        "identifier_uses": sum(1 for e in evidence if e["in_identifier"]),
        "sample": [e["path"] for e in evidence[:5]],
    }


def main():
    print("== systemhood check (against the -Hood taxonomy) ==")
    texts = collect_artifacts()
    print(f"artifacts scanned: {len(texts)}")
    print(f"hood terms:        {len(HOODS)}")
    print()

    results = []
    for name, (definition, _) in HOODS.items():
        results.append(classify_hood(name, definition, texts))

    anchored = [r for r in results if r["anchored"]]
    absent = [r for r in results if not r["anchored"]]

    print(f"anchored (achieved):  {len(anchored)}")
    print(f"absent   (not yet):   {len(absent)}")
    print()

    print("== anchored hoods ==")
    for r in sorted(anchored, key=lambda x: -x["evidence_count"]):
        print(
            f"  {r['hood']:20s} {r['evidence_count']:4d} refs, "
            f"{r['identifier_uses']} as identifier"
        )

    print()
    print("== absent hoods ==")
    for r in absent:
        print(f"  {r['hood']:20s}  {r['definition']}")

    out = OUT / "systemhood_hoods.json"
    out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "artifacts_scanned": len(texts),
                "hoods_total": len(HOODS),
                "anchored": len(anchored),
                "absent": len(absent),
                "results": results,
            },
            indent=2,
        )
    )
    print()
    print(f"wrote: {out}")


if __name__ == "__main__":
    main()
