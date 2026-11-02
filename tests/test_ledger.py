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
