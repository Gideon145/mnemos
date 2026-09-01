"""Deterministic gates that read memory before allowing an action.

The agent proposes; the gate checks memory. No remembered agreement, or
an agreement in the wrong state, and the action does not execute. This
is ordinary, predictable code: it cannot be talked out of its rules.

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


def evaluate_payment(store: MemoryStore, agreement_name: str, amount: float) -> GateResult:
    """Only a remembered, delivered agreement authorizes a payment."""
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
    return GateResult(
        allowed=True,
        reason=f"agreement {agreement_name!r} is delivered and covers {amount}",
    )
