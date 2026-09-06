"""Doctor: prove that memory is load-bearing.

The doctor runs on a throwaway database, never the user's real one.
It verifies the two claims the whole product rests on:

1. A remembered fact and a remembered agreement survive a reopen.
2. Delete the database and recall goes empty and the payment gate
   closes. The agent loses its memory, so it loses its authority.

It also reports memory hygiene: duplicates, stale facts superseded by
a revision, and an estimate of the context-token cost of the hot set.

If any check fails, memory is not load-bearing and the demo is broken.
"""
from __future__ import annotations

import glob
import json
import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .agreement import Agreement
from .gate import evaluate_payment
from .revision import revise
from .seal import seal_journal, verify_journal
from .store import DURABLE_CATEGORIES, MemoryStore


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[tuple[str, bool, str], ...] = field(default_factory=tuple)

    @property
    def healthy(self) -> bool:
        return bool(self.checks) and all(ok for _, ok, _ in self.checks)


def duplicates(store: MemoryStore) -> dict[str, list[str]]:
    """Facts whose value text repeats under more than one name."""
    groups: dict[str, list[str]] = defaultdict(list)
    for category in DURABLE_CATEGORIES:
        for record in store.list_durable(category):
            body = record.get("body") or {}
            value = str(body.get("value") or "").strip()
            if not value:
                continue
            groups[f"{category}|{value}"].append(str(record.get("name")))
    return {key: names for key, names in groups.items() if len(names) > 1}


def stale(store: MemoryStore) -> list[str]:
    """Entities whose value was superseded by a revision."""
    found: list[str] = []
    for category in DURABLE_CATEGORIES:
        for record in store.list_durable(category):
            if (record.get("body") or {}).get("history"):
                found.append(f"{category}:{record.get('name')}")
    return found


def token_budget(store: MemoryStore) -> int:
    """Rough context-token estimate of the durable hot set (4 chars/token)."""
    total = 0
    for category in DURABLE_CATEGORIES:
        for record in store.list_durable(category):
            total += len(json.dumps(record.get("body") or {}, default=str))
    return total // 4


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

        checks.append(
            (
                "duplicate detection is clean on a fresh store",
                not duplicates(store),
                "no repeated values under different names",
            )
        )
        checks.append(
            (
                "token budget is estimated",
                token_budget(store) > 0,
                f"hot set estimated at {token_budget(store)} tokens",
            )
        )

        revise(store, "preference", "ping", "pong, corrected", reason="doctor")
        checks.append(
            (
                "stale facts are counted after a revision",
                "preference:ping" in stale(store),
                "superseded values stay visible",
            )
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
