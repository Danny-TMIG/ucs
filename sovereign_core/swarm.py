#!/usr/bin/env python3

class MurmurationsEngine:
    def __init__(self):
        # The 6 foundational executive basis set
        self.basis_roles = ["CDO", "CISO", "CRO", "CLO", "Ethics/RAI", "CPO"]

    def project_role(self, role_name: str, custom_weights: dict = None) -> dict:
        """Projects any arbitrary role in existence via linear weight combinations of the 6 basis nodes."""
        weights = custom_weights or {role: 1.0 / len(self.basis_roles) for role in self.basis_roles}
        return {
            "projected_role": role_name,
            "basis_weights": weights,
            "active_basis": self.basis_roles
        }

    def evaluate(self, telemetry_metrics: dict) -> dict:
        vetoes = []
        
        # CISO Gate: Check error rates and latency spikes
        if telemetry_metrics.get("error_rate", 0.0) > 0.15:
            vetoes.append({"role": "CISO", "reason": f"Error rate {telemetry_metrics['error_rate']} exceeds 0.15 threshold."})
            
        # Ethics/RAI Gate: Check confidence degradation
        if telemetry_metrics.get("confidence_score", 1.0) < 0.85:
            vetoes.append({"role": "Ethics/RAI", "reason": f"Model confidence {telemetry_metrics['confidence_score']} below 0.85 threshold."})
            
        # CDO Gate: Ensure sample throughput exists
        if telemetry_metrics.get("sample_count", 0) == 0:
            vetoes.append({"role": "CDO", "reason": "Zero telemetry throughput detected."})

        passed = len(vetoes) == 0
        return {
            "consensus_passed": passed,
            "veto_count": len(vetoes),
            "vetoes": vetoes
        }
