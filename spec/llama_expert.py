\
import serve
class ModelUnavailable(Exception):
    pass
def invoke(inp):
    if not isinstance(inp, dict):
        raise ValueError("invoke requires a dict")
    if not serve.available():
        raise ModelUnavailable("no local model; set AETHER_GGUF or AETHER_MLX_MODEL")
    if "prompt" in inp and isinstance(inp["prompt"], str) and inp["prompt"]:
        prompt = inp["prompt"]
    elif "goal" in inp and isinstance(inp["goal"], str) and inp["goal"]:
        lines = [f"Goal: {inp['goal']}"]
        if inp.get("constraints"):
            lines.append("Constraints:"); lines.extend(f"- {c}" for c in inp["constraints"])
        if inp.get("acceptance"):
            lines.append("Acceptance:"); lines.extend(f"- {a}" for a in inp["acceptance"])
        lines.append("\nRespond with a short plan (bullet points).")
        prompt = "\n".join(lines)
    else:
        raise ValueError("invoke requires prompt or goal (non-empty string)")
    out = serve.generate(prompt, n=inp.get("n", 200),
                         temperature=inp.get("temperature", 0.7))
    if not out:
        raise RuntimeError("model returned empty output")
    return {"family": "llama", "output": out, "model": serve.model_info().get("model")}
if __name__ == "__main__":
    if serve.available():
        r = invoke({"goal": "JSON schema for a user record", "n": 80})
        assert r["family"] == "llama" and isinstance(r["output"], str) and r["output"]
        assert r["model"]
        print(f"llama_expert OK (model): {r['output'][:60]!r}")
    else:
        try:
            invoke({"goal": "x"})
        except ModelUnavailable:
            print("llama_expert OK (refused): ModelUnavailable when no model")
        else:
            raise SystemExit("invoke should raise ModelUnavailable when no model")
    for bad in ({}, {"goal": ""}, {"prompt": ""}, "not a dict"):
        try:
            invoke(bad)
        except (ValueError, ModelUnavailable):
            pass
        else:
            raise SystemExit(f"invoke should raise on bad input {bad!r}")
