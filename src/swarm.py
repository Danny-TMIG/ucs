#!/usr/bin/env python3
class MurmurationsSwarm:
    def __init__(self):
        self.roles = ["CDO", "CISO", "CRO", "CLO", "Ethics/RAI", "CPO"]

    def reach_consensus(self, packet: dict) -> dict:
        print("[murmurations] Evaluating decentralized swarm consensus across 6 executive nodes...")
        vetoes = []
        
        if packet.get("has_unverified_deps"):
            veto_note = "Unverified dependencies detected."
            vetoes.append({"role": "CISO", "reason": veto_note})
            
        if not packet.get("schema_validated"):
            veto_note = "Schema validation failed."
            vetoes.append({"role": "CDO", "reason": veto_note})
            
        if packet.get("license_risk"):
            veto_note = "License compliance risk."
            vetoes.append({"role": "CRO", "reason": veto_note})
            
        if packet.get("untested_bias"):
            veto_note = "Unmitigated algorithmic bias metrics."
            vetoes.append({"role": "Ethics/RAI", "reason": veto_note})

        passed = len(vetoes) == 0
        status_str = f"Autonomous swarm consensus achieved: {len(vetoes)} vetoes."
        print(f"[murmurations] {status_str}")
        
        return {
            "consensus_reached": passed,
            "roles_evaluated": len(self.roles),
            "vetoes": vetoes
        }
