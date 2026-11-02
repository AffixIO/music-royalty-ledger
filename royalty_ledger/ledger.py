from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Iterable
from uuid import uuid4

def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return sha256(raw).hexdigest()

@dataclass(frozen=True)
class SplitEntry:
    contributor: str
    share_percent: float

@dataclass(frozen=True)
class SplitAgreement:
    release_id: str
    version: int
    currency: str
    splits: tuple[SplitEntry, ...]
    agreement_digest: str

    @classmethod
    def create(cls, release_id: str, splits: Iterable[SplitEntry], currency: str = "GBP", version: int = 1):
        entries = tuple(splits)
        if not entries or abs(sum(e.share_percent for e in entries) - 100) > 0.000001:
            raise ValueError("royalty shares must total exactly 100 percent")
        if any(e.share_percent < 0 for e in entries):
            raise ValueError("royalty shares cannot be negative")
        body = {"release_id": release_id, "version": version, "currency": currency, "splits": [asdict(e) for e in entries]}
        return cls(release_id, version, currency, entries, _digest(body))

@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str

@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    kind: str
    subject: str
    event_digest: str
    previous_digest: str
    chain_digest: str

class RoyaltyLedger:
    def __init__(self):
        self._agreements, self._consumed, self._revoked = {}, set(), set()
        self._events: list[AuditEvent] = []

    def _record_event(self, kind: str, subject: str, data: object) -> AuditEvent:
        previous = self._events[-1].chain_digest if self._events else "GENESIS"
        event_digest = _digest({"kind": kind, "subject": subject, "data": data})
        chain_digest = _digest({"sequence": len(self._events) + 1, "event": event_digest, "previous": previous})
        event = AuditEvent(len(self._events) + 1, kind, subject, event_digest, previous, chain_digest)
        self._events.append(event)
        return event

    def record(self, agreement: SplitAgreement) -> str:
        if agreement.release_id in self._agreements:
            raise ValueError("release already has an agreement; create a new version")
        self._agreements[agreement.release_id] = agreement
        self._record_event("agreement-recorded", agreement.release_id, agreement.agreement_digest)
        return agreement.agreement_digest

    def authorise_statement(self, release_id: str, gross_amount: float, statement_id: str | None = None) -> dict:
        agreement = self._agreements[release_id]
        statement_id = statement_id or str(uuid4())
        payload = {"statement_id": statement_id, "release_id": release_id, "version": agreement.version, "currency": agreement.currency, "gross_amount": gross_amount, "agreement_digest": agreement.agreement_digest}
        statement = {"payload": payload, "evidence_digest": _digest(payload)}
        self._record_event("statement-authorised", statement_id, statement["evidence_digest"])
        return statement

    def allocations(self, statement: dict) -> dict[str, float]:
        """Calculate simulated allocations without rounding away the total."""
        payload = statement["payload"]
        agreement = self._agreements[payload["release_id"]]
        amount = float(payload["gross_amount"])
        if amount < 0:
            raise ValueError("gross amount cannot be negative")
        allocations = {entry.contributor: round(amount * entry.share_percent / 100, 2) for entry in agreement.splits}
        remainder = round(amount - sum(allocations.values()), 2)
        if remainder:
            first = agreement.splits[0].contributor
            allocations[first] = round(allocations[first] + remainder, 2)
        return allocations

    def verify_statement(self, statement: dict, expected_release: str, *, consume: bool = False) -> VerificationResult:
        try:
            payload = statement["payload"]
            if payload["release_id"] != expected_release: return VerificationResult(False, "wrong-release")
            if payload["statement_id"] in self._revoked: return VerificationResult(False, "revoked")
            if payload["statement_id"] in self._consumed: return VerificationResult(False, "replay")
            if _digest(payload) != statement["evidence_digest"]: return VerificationResult(False, "tampered")
            agreement = self._agreements.get(expected_release)
            if not agreement or payload["agreement_digest"] != agreement.agreement_digest: return VerificationResult(False, "agreement-mismatch")
            if consume: self._consumed.add(payload["statement_id"])
            if consume: self._record_event("statement-consumed", payload["statement_id"], statement["evidence_digest"])
            return VerificationResult(True, "verified")
        except (KeyError, TypeError):
            return VerificationResult(False, "malformed")

    def revoke(self, statement_id: str) -> None:
        self._revoked.add(statement_id)
        self._record_event("statement-revoked", statement_id, statement_id)

    def audit_events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def verify_audit_chain(self) -> VerificationResult:
        previous = "GENESIS"
        for index, event in enumerate(self._events, 1):
            expected = _digest({"sequence": index, "event": event.event_digest, "previous": previous})
            if event.sequence != index or event.previous_digest != previous or event.chain_digest != expected:
                return VerificationResult(False, "audit-chain-tampered")
            previous = event.chain_digest
        return VerificationResult(True, "audit-chain-verified")
