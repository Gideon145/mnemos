"""Fresh live Base mainnet payment for the verification page.

Reads MNEMOS_PAYER_KEY / MNEMOS_PAYEE_KEY from the environment (raw key
or file path), builds a delivered agreement in a dedicated evidence db,
and submits a real mainnet transaction through the memory gate.
"""
import json
import os
import sys
from pathlib import Path

from core.memory.agreement import Agreement
from core.memory.store import MemoryStore
from core.payments import BaseExecutor, pay

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "docs" / "evidence" / "payment.db"
OUT = ROOT / "docs" / "evidence" / "payment.json"


def main() -> int:
    store = MemoryStore(DB)
    try:
        agreement = Agreement(store, "hardening", amount=50)
        agreement.advance("agreed")
        agreement.advance("delegated")
        agreement.advance("delivered")

        executor = BaseExecutor(network="mainnet")
        outcome = pay(store, "hardening", 50, executor=executor)

        payload = {
            "allowed": outcome.allowed,
            "reason": outcome.reason,
            "transaction": outcome.transaction,
            "executor": outcome.executor,
        }
        OUT.write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        print(json.dumps(payload, indent=2))
        return 0 if outcome.allowed else 1
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
