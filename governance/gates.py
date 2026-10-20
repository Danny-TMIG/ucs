import pathlib
import json

class ExecutiveGovernance:
    def __init__(self):
        self.roles = ["CDO", "CISO", "CRO", "CLO", "Ethics/RAI", "CPO"]
        self.state_path = pathlib.Path.home() / ".ucs" / "governance_state.json"
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def _load_state(self):
        if self.state_path.exists():
            try:
                self.veto_states = json.loads(self.state_path.read_text())
            except Exception:
                self.veto_states = {role: False for role in self.roles}
        else:
            self.veto_states = {role: False for role in self.roles}

    def _save_state(self):
        self.state_path.write_text(json.dumps(self.veto_states, indent=2))

    def assert_no_veto(self) -> bool:
        self._load_state()
        for role, vetoed in self.veto_states.items():
            if vetoed:
                raise PermissionError(f"Deployment halted by active executive veto: {role}")
        return True

    def trigger_veto(self, role: str):
        if role not in self.roles:
            raise ValueError(f"Unknown executive role: {role}")
        self.veto_states[role] = True
        self._save_state()

    def clear_veto(self, role: str):
        if role not in self.roles:
            raise ValueError(f"Unknown executive role: {role}")
        self.veto_states[role] = False
        self._save_state()
