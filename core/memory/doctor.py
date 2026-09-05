"""Doctor: prove that memory is load-bearing.

The doctor runs on a throwaway database, never the user's real one.
It verifies the two claims the whole product rests on:

1. A remembered fact and a remembered agreement survive a reopen.
2. Delete the database and recall goes empty and the payment gate
   closes. The agent loses its memory, so it loses its authority.

If any check fails, memory is not load-bearing and the demo is broken.
"""
from __future__ import annotations

import glob
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .agreement import Agreement
from .gate import evaluate_payment
from .seal import seal_journal, verify_journal
from .store import MemoryStore


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[tuple[str, bool, str], ...] = field(default_factory=tuple)

    @property
    def healthy(self) -> bool:
        return bool(self.checks) and all(ok for _, ok, _ in self.checks)


def run_doctor() -> DoctorReport:
    checks: list[tuple[str, bool, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "memory.db"

        store = MemoryStore(db)
        store.remember_durable("preference", "ping", {"value": "pong"})
        record = store.recall_durable("preference", "ping")
        checks.append(
            (
                "durable write and recall",
                record is not None and record.get("body", {}).get("value") == "pong",
                "a remembered fact survives the roundtrip",
            )
        )

        agreement = Agreement(store, "contractor", amount=40)
        agreement.advance("agreed")
        agreement.advance("delegated")
        agreement.advance("delivered")
        before = evaluate_payment(store, "contractor", 40)
        checks.append(
            ("gate opens on a remembered agreement", before.allowed, before.reason)
        )

        seal_journal(store)
        sealed = verify_journal(store)
        checks.append(
            ("journal seal verifies", sealed["ok"], sealed.get("detail", "sealed"))
        )
        store.close()

        for path in glob.glob(str(db) + "*"):
            os.remove(path)

        fresh = MemoryStore(db)
        checks.append(
            (
                "deletion empties recall",
                fresh.recall_durable("preference", "ping") is None,
                "a fresh store remembers nothing",
            )
        )
        after = evaluate_payment(fresh, "contractor", 40)
        checks.append(
            ("deletion closes the gate", not after.allowed, after.reason)
        )
        broken = verify_journal(fresh)
        checks.append(
            (
                "deletion breaks the journal seal",
                not broken["ok"],
                broken["detail"],
            )
        )
        fresh.close()

    return DoctorReport(checks=tuple(checks))
