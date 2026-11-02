from royalty_ledger import RoyaltyLedger, SplitAgreement, SplitEntry

ledger = RoyaltyLedger()
agreement = SplitAgreement.create("midnight-train", [SplitEntry("artist", 60), SplitEntry("producer", 25), SplitEntry("writer", 15)])
ledger.record(agreement)
statement = ledger.authorise_statement("midnight-train", 1000.0, "statement-001")
result = ledger.verify_statement(statement, "midnight-train", consume=True)
print({"mode": "simulation", "release": agreement.release_id, "statement": statement, "result": result.reason})
