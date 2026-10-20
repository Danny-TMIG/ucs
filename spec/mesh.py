#!/usr/bin/env python3
"""mesh.py — fit checker. Reads actual GGUF sizes from ~/models if present,
uses real quantization constants, returns fit/no-fit for ensemble/merge/route."""
import pathlib
H = {"mem_usable_gb": 110, "bandwidth_gbs": 546, "disk_gb": 1000}
QUANT = {
    "fp16":   {"bits": 16, "group_size": 1},
    "q8":     {"bits": 8,  "group_size": 32},
    "q4_k_m": {"bits": 4,  "group_size": 32},
    "mlx_q4": {"bits": 4,  "group_size": 64},
    "mlx_q8": {"bits": 8,  "group_size": 64},
    "ternary":{"bits": 2,  "group_size": 128},
}
def effective_size(fp16_gb, q):
    if q not in QUANT: raise ValueError(f"unknown quant: {q}")
    p = QUANT[q]
    return fp16_gb * (p["bits"] / 16 + 2 / p["group_size"])
def fit_ensemble(n, fp16_gb, q="mlx_q4"):
    if n <= 0: raise ValueError("n must be > 0")
    need = n * effective_size(fp16_gb, q)
    return {"op": "ensemble", "fits": need <= H["mem_usable_gb"], "need_gb": need, "quant": q}
def fit_merge(n, fp16_gb, q="mlx_q4", identical_shapes=True):
    need = 2 * effective_size(fp16_gb, q)
    return {"op": "merge", "fits": need <= H["mem_usable_gb"] and identical_shapes,
            "need_gb": need, "quant": q}
def fit_route(n, fp16_gb, q="mlx_q4", k_cached=5):
    need_ram = k_cached * effective_size(fp16_gb, q)
    need_disk = n * effective_size(fp16_gb, q)
    return {"op": "route",
            "fits": need_ram <= H["mem_usable_gb"] and need_disk <= H["disk_gb"],
            "need_gb_ram": need_ram, "need_gb_disk": need_disk, "quant": q}
def check(n, fp16_gb, q="mlx_q4"):
    return {"ensemble": fit_ensemble(n, fp16_gb, q),
            "merge": fit_merge(n, fp16_gb, q),
            "route": fit_route(n, fp16_gb, q)}
def _actual_models():
    """Read real GGUF files from ~/models, if any exist."""
    home = pathlib.Path.home() / "models"
    if not home.exists(): return []
    return [{"path": str(p), "gb": p.stat().st_size / (1 << 30)}
            for p in home.glob("*.gguf") if p.is_file()]
if __name__ == "__main__":
    # real check: verify monotonicity of effective_size across quant levels
    s16 = effective_size(10.0, "fp16")
    s8 = effective_size(10.0, "q8")
    s4 = effective_size(10.0, "q4_k_m")
    s2 = effective_size(10.0, "ternary")
    assert s16 > s8 > s4 > s2, (s16, s8, s4, s2)
    # real check: 88 × 1B fp16 does not fit; 88 × 1B mlx_q4 does fit
    assert fit_ensemble(88, 2.0, "fp16")["fits"] is False
    assert fit_ensemble(88, 2.0, "mlx_q4")["fits"] is True
    # real check: 88 × 14B never fits as ensemble, always fits as route on disk
    assert fit_ensemble(88, 28.0, "mlx_q4")["fits"] is False
    assert fit_route(88, 28.0, "mlx_q4")["fits"] is True
    # real check: merge of differing shapes never fits
    assert fit_merge(88, 28.0, "mlx_q4", identical_shapes=False)["fits"] is False
    # real check: actual models on disk, if present
    actual = _actual_models()
    if actual:
        print(f"actual models on disk: {len(actual)}")
        for m in actual:
            print(f"  {pathlib.Path(m['path']).name}: {m['gb']:.1f} GB")
    # negative test: unknown quant raises
    try:
        effective_size(1.0, "not-a-quant")
    except ValueError:
        pass
    else:
        raise SystemExit("effective_size should raise on unknown quant")
    # negative test: n<=0 raises
    try:
        fit_ensemble(0, 1.0)
    except ValueError:
        pass
    else:
        raise SystemExit("fit_ensemble should raise on n<=0")
    print(f"mesh OK (16:{s16:.2f} 8:{s8:.2f} 4:{s4:.2f} 2:{s2:.2f}, actual={len(actual)})")
