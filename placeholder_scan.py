#!/usr/bin/env python3
"""placeholder_scan.py - reads placeholder.gr, scans, reports."""

from __future__ import annotations
import ast, json, re, sys, time
from pathlib import Path

HOME = Path.home()
UC = HOME / "ucs"
GR = UC / "placeholder.gr"


def load_grammar(path):
    """Parse flat `name := value` lines into a dict."""
    g = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":=" not in line:
            continue
        name, val = line.split(":=", 1)
        g[name.strip()] = val.strip()
    return g


def build_matchers(g):
    """Turn grammar entries into (kind, regex) pairs."""
    out = []
    for name, pat in g.items():
        if name == "angle":
            out.append(("angle", re.compile(r"<([A-Za-z_][A-Za-z0-9_]*)>")))
        elif name == "bracket":
            out.append(("bracket", re.compile(r"\[([A-Za-z_][A-Za-z0-9_]*)\]")))
        elif name.startswith("holder_"):
            w = re.compile(r"\b" + re.escape(pat) + r"\b")
            out.append(("holder", w))
    return out


def scan_file(p, matchers):
    try:
        src = p.read_text(errors="ignore")
    except OSError:
        return {}
    counts = {}
    for kind, rx in matchers:
        n = len(rx.findall(src))
        if n:
            counts[kind] = counts.get(kind, 0) + n
    return counts


def main():
    g = load_grammar(GR)
    matchers = build_matchers(g)
    print("[grammar]")
    for name in g:
        print("  " + name)
    print("  matchers: " + str(len(matchers)))
    print()

    totals = {"angle": 0, "bracket": 0, "holder": 0}
    by_file = {}
    files = 0
    for p in sorted(UC.rglob("*.py")):
        sp = str(p)
        if any(x in sp for x in ("__pycache__", "/_trash/")):
            continue
        files += 1
        counts = scan_file(p, matchers)
        if counts:
            by_file[str(p.relative_to(HOME))] = counts
            for k, n in counts.items():
                totals[k] = totals.get(k, 0) + n

    print("[totals]")
    for k, n in totals.items():
        print("  " + k.ljust(10) + " " + str(n))
    print("  files:     " + str(files))
    print("  files with hits: " + str(len(by_file)))
    print()

    if by_file:
        print("[files with hits, top 20]")
        ranked = sorted(by_file.items(), key=lambda kv: -sum(kv[1].values()))
        for path, counts in ranked[:20]:
            parts = ", ".join(k + "=" + str(n) for k, n in counts.items())
            print("  " + path.ljust(60) + " " + parts)

    out = UC / "placeholder_scan.json"
    out.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "grammar": g,
                "totals": totals,
                "files": files,
                "by_file": by_file,
            },
            indent=2,
        )
    )
    print()
    print("  report: " + str(out))


if __name__ == "__main__":
    main()
