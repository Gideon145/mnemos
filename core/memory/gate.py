"""Deterministic gates that read memory before allowing an action.

The agent proposes; the gate checks memory. No remembered agreement, or
an agreement in the wrong state, and the action does not execute. This
is ordinary, predictable code: it cannot be talked out of its rules.

Scars veto actions too: a high severity lesson linked to an agreement
blocks its payments until the lesson is resolved. Memory of a failure
changes what the agent may do next, not just what it can recall.

The deletion test lives here: remove the store and every gate closes.
"""
from __future__ import annotations

from dataclasses import dataclass

from .agreement import Agreement
from .store import MemoryStore


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str


def _unresolved_scars(store: MemoryStore, agreement: Agreement) -> list[str]:
    scars: list[str] = []
    for ref in agreement.body.get("linked") or []:
        if not str(ref).startswith("lesson:"):
            continue
        name = str(ref).split(":", 1)[1]
        record = store.recall_durable("lesson", name)
        if record is None:
            continue
        body = record.get("body") or {}
        if body.get("severity") == "high" and not body.get("resolved"):
            scars.append(ref)
    return scars


def evaluate_payment(store: MemoryStore, agreement_name: str, amount: float) -> GateResult:
    """Only a remembered, delivered, unscarred agreement authorizes a payment."""
    agreement = Agreement.open(store, agreement_name)
    if agreement is None:
        return GateResult(
            allowed=False,
            reason=f"no remembered agreement named {agreement_name!r}",
        )
    if agreement.state != "delivered":
        return GateResult(
            allowed=False,
            reason=(
                f"agreement {agreement_name!r} is in state {agreement.state!r}; "
                "payments require 'delivered'"
            ),
        )
    agreed_amount = agreement.body.get("amount")
    if agreed_amount is not None and amount > float(agreed_amount):
        return GateResult(
            allowed=False,
            reason=(
                f"amount {amount} exceeds remembered agreement "
                f"({agreed_amount})"
            ),
        )
    scars = _unresolved_scars(store, agreement)
    if scars:
        return GateResult(
            allowed=False,
            reason=(
                f"unresolved scars block {agreement_name!r}: "
                f"{', '.join(scars)}; resolve the lesson first"
            ),
        )
    from .revision import suspect_reasons

    suspect = suspect_reasons(store, "agreement", agreement_name)
    if suspect:
        return GateResult(
            allowed=False,
            reason=(
                f"agreement {agreement_name!r} is suspect: depends on revised "
                f"memory {', '.join(suspect)}; reconsider first"
            ),
        )
    return GateResult(
        allowed=True,
        reason=f"agreement {agreement_name!r} is delivered and covers {amount}",
    )
