import os
import pathlib
try:
    import mlx.core as mx
    import mlx.nn as nn
    from mlx_lm import load, generate
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False

class LocalMLXModel:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.loaded = False

    def load(self):
        if not MLX_AVAILABLE:
            raise RuntimeError("MLX library and mlx_lm are not installed in the active python environment.")
        if not self.loaded:
            self.model, self.tokenizer = load(self.model_path)
            self.loaded = True
        return {"status": "loaded", "model": self.model_path}

    def generate(self, prompt: str, max_tokens: int = 128, temp: float = 0.0):
        if not self.loaded:
            self.load()
        response = generate(self.model, self.tokenizer, prompt=prompt, max_tokens=max_tokens, verbose=False)
        return {"prompt": prompt, "response": response, "tokens": max_tokens}
