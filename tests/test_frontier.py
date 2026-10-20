import pytest
import pathlib
from ucs.governance.gates import ExecutiveGovernance
from ucs.ledger.worm import WORMLedger

def test_governance_gate_mechanics(tmp_path):
    gov = ExecutiveGovernance()
    gov.state_path = tmp_path / "gov.json"
    gov.veto_states = {r: False for r in gov.roles}
    assert gov.assert_no_veto() is True
    gov.trigger_veto("CISO")
    with pytest.raises(PermissionError):
        gov.assert_no_veto()
    gov.clear_veto("CISO")
    assert gov.assert_no_veto() is True

def test_worm_ledger_chain(tmp_path):
    p = tmp_path / "ledger.jsonl"
    ledger = WORMLedger(p)
    h1 = ledger.append("event_1", {"data": 100})
    h2 = ledger.append("event_2", {"data": 200})
    assert len(h1) == 64
    assert len(h2) == 64
    assert h1 != h2
    assert ledger.verify_integrity() is True
