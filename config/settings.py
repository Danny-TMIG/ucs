import os
import pathlib
import json

CONFIG_DIR = pathlib.Path.home() / ".ucs"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"

class Settings:
    def __init__(self):
        self.model_path = os.getenv("UCS_MODEL_PATH", "mlx-community/Qwen2.5-7B-Instruct-4bit")
        self.port = int(os.getenv("UCS_PORT", "8765"))
        self.host = os.getenv("UCS_HOST", "127.0.0.1")
        self.worm_ledger_path = pathlib.Path(os.getenv("UCS_LEDGER_PATH", CONFIG_DIR / "ledger.jsonl"))
        self._load_file_config()

    def _load_file_config(self):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                self.model_path = data.get("model_path", self.model_path)
                self.port = data.get("port", self.port)
                self.host = data.get("host", self.host)
            except Exception:
                pass

settings = Settings()
