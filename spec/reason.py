#!/usr/bin/env python3
"""reason.py — reasoning substrate.

If serve.available(): call the model, return its output with source="model".
If not: raise ReasoningUnavailable. No silent stub fallback.
The caller decides what to do when reasoning is not available."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

class ReasoningUnavailable(Exception):
    pass

def reason(goal, constraints=None, acceptance=None, n=300, temperature=0.4):
    if not goal or not isinstance(goal, str):
        raise ValueError("goal must be a non-empty string")
    try:
        import serve
    except ImportError:
        serve = None
    if serve is None or not serve.available():
        raise ReasoningUnavailable("no local model; set AETHER_GGUF or AETHER_MLX_MODEL")
    lines = [f"Goal: {goal}"]
    if constraints:
        lines.append("Constraints:"); lines.extend(f"- {c}" for c in constraints)
    if acceptance:
        lines.append("Acceptance:"); lines.extend(f"- {a}" for a in acceptance)
    lines.append("\nReturn a concise plan (bullets, no preamble).")
    text = serve.generate("\n".join(lines), n=n, temperature=temperature, timeout=180)
    return {"text": text, "source": "model", "model": serve.model_info().get("model")}

if __name__ == "__main__":
    import serve
    if serve.available():
        r = reason("write a function that reverses a string",
                   ["use slicing"], ["returns reverse"], n=100)
        assert r["source"] == "model", r
        assert isinstance(r["text"], str) and len(r["text"]) > 0, r
        assert r["model"] and r["model"].endswith(".gguf") or "mlx" in (r["model"] or "")
        print(f"reason OK (model): {r['text'][:60]!r}")
    else:
        # real path: refusal is loud, not a stub
        try:
            reason("x")
        except ReasoningUnavailable:
            print("reason OK (refused): ReasoningUnavailable raised when no model")
        else:
            raise SystemExit("reason should raise ReasoningUnavailable when no model")
    # negative test: empty goal raises ValueError regardless of model state
    try:
        reason("")
    except ValueError:
        pass
    else:
        raise SystemExit("reason should raise ValueError on empty goal")
