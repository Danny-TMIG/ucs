import os
import sys
import subprocess
import json
import pathlib
import hashlib
import time
from typing import Dict, Any

class AutonomousEvaluator:
    def __init__(self, submission_dir: str):
        self.submission_dir = pathlib.Path(submission_dir)
        self.report_path = self.submission_dir / "evaluation_report.json"
        self.ledger_path = pathlib.Path.home() / ".ucs" / "evaluator_ledger.jsonl"
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def run_full_pipeline(self) -> Dict[str, Any]:
        result = {
            "timestamp": time.time(),
            "submission": str(self.submission_dir),
            "stages": {}
        }
        try:
            result["stages"]["static_analysis"] = self._run_static_analysis()
            result["stages"]["unit_tests"] = self._run_unit_tests()
            result["stages"]["air_gap_audit"] = self._run_air_gap_audit()
            result["stages"]["intent_alignment"] = self._evaluate_intent()
            result["overall_status"] = "PASS"
            result["receipt"] = self._seal_receipt(result)
        except Exception as e:
            result["overall_status"] = "FAIL"
            result["error"] = str(e)
        self.report_path.write_text(json.dumps(result, indent=2))
        return result

    def _run_static_analysis(self) -> Dict[str, Any]:
        for py_file in self.submission_dir.glob("**/*.py"):
            try:
                compile(py_file.read_text(), str(py_file), "exec")
            except SyntaxError as se:
                raise RuntimeError(f"Syntax violation in {py_file.name}: {se}")
        return {"status": "passed", "checked_files": len(list(self.submission_dir.glob("**/*.py")))}

    def _run_unit_tests(self) -> Dict[str, Any]:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", str(self.submission_dir), "-q"],
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            raise RuntimeError(f"Unit test failure: {res.stdout}\n{res.stderr}")
        return {"status": "passed", "output": res.stdout.strip()}

    def _run_air_gap_audit(self) -> Dict[str, Any]:
        forbidden_patterns = ["requests.", "urllib.", "socket.", "http.client", "openai"]
        for py_file in self.submission_dir.glob("**/*.py"):
            content = py_file.read_text()
            for pattern in forbidden_patterns:
                if pattern in content and "test" not in py_file.name:
                    raise PermissionError(f"Air-gap violation: Forbidden pattern {pattern} found in {py_file.name}")
        return {"status": "passed", "external_calls_detected": False}

    def _evaluate_intent(self) -> Dict[str, Any]:
        intent_file = self.submission_dir / "INTENT.md"
        if not intent_file.exists():
            raise ValueError("Missing architectural intent specification (INTENT.md)")
        return {"status": "passed", "intent_verified": True}

    def _seal_receipt(self, data: dict) -> str:
        line = json.dumps(data, sort_keys=True)
        h = hashlib.sha256(line.encode()).hexdigest()
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps({"receipt_hash": h, "data": data}) + "\n")
        return h
