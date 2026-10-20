#!/usr/bin/env python3
"""Fault-injection harness for executive murmurations swarm."""
import sys
from murmurations import MurmurationsSwarm

def test_fault_injection():
    swarm = MurmurationsSwarm()
    
    # Test case 1: Trigger CISO unverified dependency veto
    packet_ciso_fail = {
        "has_unverified_deps": True,
        "schema_validated": True,
        "license_risk": False,
        "untested_bias": False
    }
    res = swarm.reach_consensus(packet_ciso_fail)
    assert not res["consensus_reached"], "Expected CISO veto failure!"
    assert any(v["role"] == "CISO" for v in res["vetoes"]), "CISO veto missing!"
    print("[test_fault] CISO veto gate verified successfully.")

    # Test case 2: Clean packet (all pass)
    packet_clean = {
        "has_unverified_deps": False,
        "schema_validated": True,
        "license_risk": False,
        "untested_bias": False
    }
    res_clean = swarm.reach_consensus(packet_clean)
    assert res_clean["consensus_reached"], "Expected clean consensus!"
    print("[test_fault] Clean consensus gate verified successfully.")
    print("[test_fault] All executive fault-injection tests passed.")

if __name__ == "__main__":
    test_fault_injection()
    sys.exit(0)
