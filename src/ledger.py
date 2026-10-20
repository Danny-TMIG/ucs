#!/usr/bin/env python3
import pathlib
import json
import time
import hashlib
import hmac
import os

class ProductionCryptoLedger:
    def __init__(self, workspace_dir="/tmp/ucs-clean"):
        self.workspace = pathlib.Path(workspace_dir)
        self.ledger_path = self.workspace / "build/ledger_secure.jsonl"
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.key_path = self.workspace / "build/ledger_hmac.key"
        
        if self.key_path.exists():
            self.secret_key = self.key_path.read_bytes()
        else:
            self.secret_key = os.urandom(32)
            self.key_path.write_bytes(self.secret_key)

    def append_secure_entry(self, event_type: str, payload: dict) -> dict:
        prev_hash = "0" * 64
        if self.ledger_path.exists():
            lines = self.ledger_path.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                try:
                    last_record = json.loads(lines[-1])
                    prev_hash = last_record.get("current_hash", prev_hash)
                except Exception:
                    pass

        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "payload": payload,
            "prev_hash": prev_hash
        }

        canonical_body = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        current_hash = hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()
        entry["current_hash"] = current_hash

        signature = hmac.new(self.secret_key, current_hash.encode("utf-8"), hashlib.sha256).hexdigest()
        entry["hmac_signature"] = signature

        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

        print(f"[crypto-ledger] Sealed [{event_type}] | Hash: {current_hash[:16]}... | HMAC: {signature[:16]}...")
        return entry

    def verify_ledger(self) -> bool:
        if not self.ledger_path.exists():
            return True
            
        lines = self.ledger_path.read_text(encoding="utf-8").strip().splitlines()
        expected_prev = "0" * 64
        
        for idx, line in enumerate(lines):
            try:
                record = json.loads(line)
            except Exception:
                print(f"[crypto-ledger] JSON decode error at line {idx}")
                return False
                
            saved_hash = record.pop("current_hash")
            saved_sig = record.pop("hmac_signature")
            
            if record.get("prev_hash") != expected_prev:
                print(f"[crypto-ledger] Chain broken at line {idx}!")
                return False
                
            canonical_body = json.dumps(record, sort_keys=True, separators=(',', ':'))
            computed_hash = hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()
            computed_sig = hmac.new(self.secret_key, computed_hash.encode("utf-8"), hashlib.sha256).hexdigest()
            
            if computed_hash != saved_hash or not hmac.compare_digest(computed_sig, saved_sig):
                print(f"[crypto-ledger] Cryptographic verification failed at line {idx}!")
                return False
                
            expected_prev = saved_hash
            
        print(f"[crypto-ledger] Ledger verification PASSED ({len(lines)} entries validated).")
        return True
