import pytest
from royalty_ledger import RoyaltyLedger, SplitAgreement, SplitEntry

def setup_ledger():
    ledger = RoyaltyLedger()
    ledger.record(SplitAgreement.create("release-1", [SplitEntry("artist", 70), SplitEntry("producer", 30)]))
    return ledger

def test_valid_statement_is_verified_and_one_use():
    ledger = setup_ledger(); statement = ledger.authorise_statement("release-1", 500, "s-1")
    assert ledger.verify_statement(statement, "release-1", consume=True).ok
    assert ledger.verify_statement(statement, "release-1").reason == "replay"

def test_changed_amount_is_rejected():
    ledger = setup_ledger(); statement = ledger.authorise_statement("release-1", 500, "s-2")
    statement["payload"]["gross_amount"] = 5000
    assert ledger.verify_statement(statement, "release-1").reason == "tampered"

def test_revocation_and_wrong_release_fail_closed():
    ledger = setup_ledger(); statement = ledger.authorise_statement("release-1", 500, "s-3")
    ledger.revoke("s-3")
    assert ledger.verify_statement(statement, "release-1").reason == "revoked"
    assert ledger.verify_statement(statement, "another-release").reason == "wrong-release"

def test_splits_must_total_one_hundred():
    with pytest.raises(ValueError): SplitAgreement.create("bad", [SplitEntry("artist", 99)])

def test_allocations_preserve_the_simulated_gross_total():
    ledger = setup_ledger(); statement = ledger.authorise_statement("release-1", 100, "s-4")
    assert ledger.allocations(statement) == {"artist": 70.0, "producer": 30.0}

def test_audit_chain_detects_history_tampering():
    ledger = setup_ledger(); ledger.authorise_statement("release-1", 100, "s-5")
    assert ledger.verify_audit_chain().ok
    ledger._events[0] = ledger._events[0].__class__(1, "changed", "release-1", "bad", "GENESIS", "bad")
    assert ledger.verify_audit_chain().reason == "audit-chain-tampered"
