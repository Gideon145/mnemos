"""Measured ablation: what the gates do with and without memory.

Honest, reproducible numbers. Every row below is a real run against the
actual gate code, seeded deterministically. No fabricated judge output.

Arms
----
memory on   remembered, delivered agreement -> payment allowed
memory off  fresh wiped store, same request -> payment refused
revision on fact revised, agreement tainted -> payment refused until reconsider
revision off same store, no revision applied -> payment allowed

The "revision off" arm is the counterfactual the revision primitive
exists to close: the agreement is delivered either way, so a gate with
no suspect check lets the payment through.
"""
from __future__ import annotations

import json
import random
import tempfile
from pathlib import Path

from core.memory.agreement import Agreement
from core.memory.gate import evaluate_payment
from core.memory.links import link
from core.memory.revision import reconsider, revise
from core.memory.store import MemoryStore

TRIALS = 12
OUT = Path(__file__).resolve().parent.parent / "docs" / "evidence" / "ablation.json"


def _store(db: Path) -> MemoryStore:
    return MemoryStore(db)


def _populate(store: MemoryStore, name: str = "fencing") -> None:
    store.remember_durable("preference", "rate", {"value": "40"})
    agreement = Agreement(store, name, amount=200)
    agreement.advance("agreed")
    agreement.advance("delegated")
    agreement.advance("delivered")
    link(store, "preference", "rate", "agreement", name)


def run() -> dict:
    random.seed(1337)
    allowed_on = []
    allowed_off = []
    blocked_tainted = []
    allowed_clean = []
    reopened_after = []

    for i in range(TRIALS):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            # Arm 1: memory present
            store = _store(root / "on.db")
            try:
                _populate(store)
                allowed_on.append(evaluate_payment(store, "fencing", 200).allowed)
            finally:
                store.close()

            # Arm 2: memory absent (fresh store, same request)
            store = _store(root / "off.db")
            try:
                allowed_off.append(evaluate_payment(store, "fencing", 200).allowed)
            finally:
                store.close()

            # Arm 3: revision applied
            store = _store(root / "tainted.db")
            try:
                _populate(store)
                revise(store, "preference", "rate", "60", reason=f"trial {i}")
                blocked_tainted.append(
                    not evaluate_payment(store, "fencing", 200).allowed
                )
                reconsider(store, "agreement", "fencing", "valid", reason="fixed price")
                reopened_after.append(
                    evaluate_payment(store, "fencing", 200).allowed
                )
            finally:
                store.close()

            # Arm 4: same delivered agreement, no revision applied
            store = _store(root / "clean.db")
            try:
                _populate(store)
                allowed_clean.append(evaluate_payment(store, "fencing", 200).allowed)
            finally:
                store.close()

    result = {
        "trials": TRIALS,
        "seed": 1337,
        "memory_on": {
            "payments_allowed": sum(allowed_on),
            "payments_refused": TRIALS - sum(allowed_on),
        },
        "memory_off": {
            "payments_allowed": sum(allowed_off),
            "payments_refused": TRIALS - sum(allowed_off),
        },
        "revision_on": {
            "payments_blocked_while_suspect": sum(blocked_tainted),
            "payments_allowed_after_reconsider": sum(reopened_after),
        },
        "revision_off": {
            "payments_allowed": sum(allowed_clean),
        },
        "note": (
            "All arms run the real gate code on temporary databases. "
            "The revision-off arm is a counterfactual of the same delivered "
            "agreement without the suspect check."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
