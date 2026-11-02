# Verifiable music royalty splits

Collaborative releases often fail at the handoff between a split agreement, a royalty statement and a later dispute. This small example shows how an agent or rights workflow can verify that a simulated statement still matches the agreed release, version and contributor shares.

It uses fictional data only. No streaming account, label system, bank, wallet, payment provider or real royalty is contacted.

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install pytest
pytest -q
python demo.py
```

The demo creates a 60/25/15 split for a fictional release, creates a simulated £1,000 statement, calculates each contributor's allocation, verifies it once and consumes the evidence. It also maintains a hash-linked audit chain. Tests show that changed amounts are rejected, consumed statements cannot be replayed, revoked evidence fails, wrong releases fail, audit history tampering is detected, and shares must total 100%.

## Why this matters

The useful claim is narrow: the record proves that the checked statement still corresponds to a specific release agreement. It does not prove that a platform reported revenue correctly, that contributors own the rights, or that money was paid.

## AffixIO integration boundary

The example keeps the ledger local and dependency-light so it can be reviewed in five minutes. A production adapter would replace the local digest with the documented AffixIO SDK proof-generation and verification interfaces available to the integrator, pin the expected signer, and retain only the minimum evidence needed for audit. No SDK method is invented here and no private key is included.

## Possible extensions

- versioned agreements for remixes, samples and territory changes
- split-aware approval before a statement is released
- pseudonymous contributor IDs with private recovery by an authorised party
- Merkle-batched monthly evidence for catalogue-scale reporting
- adapters for platform exports without granting the verifier payment authority
- dispute windows that preserve both the original and amended agreement versions
- catalogue-level Merkle roots for compact monthly audit references

## Status and safety

Research example. Simulated only. Not legal advice, rights administration, accounting software, a payment system or a guarantee of royalty accuracy.

## Contributing

Small, tested improvements are welcome. Keep fixtures fictional and never commit credentials, private keys, unreleased tracks or personal data.

## License

MIT
