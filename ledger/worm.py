import pathlib
import json
import time
import hashlib
import os

class WORMLedger:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch(mode=0o600)

    def append(self, event_type: str, payload: dict) -> str:
        prev_hash = self._get_last_hash()
        record = {
            "timestamp": time.time(),
            "event": event_type,
            "payload": payload,
            "prev_hash": prev_hash
        }
        canonical_line = json.dumps(record, sort_keys=True)
        current_hash = hashlib.sha256(canonical_line.encode()).hexdigest()
        record["hash"] = current_hash
        
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return current_hash

    def _get_last_hash(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return "0" * 64
        last_line = ""
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    last_line = line.strip()
        if not last_line:
            return "0" * 64
        try:
            data = json.loads(last_line)
            return data.get("hash", "0" * 64)
        except Exception:
            return "0" * 64

    def verify_integrity(self) -> bool:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return True
        expected_prev = "0" * 64
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line.strip())
                h = data.pop("hash")
                p = data.get("prev_hash")
                if p != expected_prev:
                    return False
                canonical = json.dumps(data, sort_keys=True)
                computed = hashlib.sha256(canonical.encode()).hexdigest()
                if computed != h:
                    return False
                expected_prev = h
        return True
