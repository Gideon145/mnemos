"""Agreement entities with an explicit state machine.

States advance in order and never move backward::

    draft -> agreed -> delegated -> delivered -> paid

Each transition writes the updated entity (via the entity status field)
and a journal event describing the change. There is no out-of-memory
copy of an agreement: the store is the single source of truth, enforced
by the store's uniqueness constraint on (category, name).
"""
from __future__ import annotations

from typing import Any

from .store import MemoryStore

STATES = ("draft", "agreed", "delegated", "delivered", "paid")
_ORDER = {state: index for index, state in enumerate(STATES)}

_CATEGORY = "agreement"


class AgreementError(ValueError):
    """Raised when an agreement transition is not allowed."""


class Agreement:
    """A handle over an agreement entity."""

    def __init__(
        self,
        store: MemoryStore,
        name: str,
        *,
        amount: Any = None,
        counterparty: str | None = None,
        note: str | None = None,
        linked: list[str] | None = None,
    ) -> None:
        self.store = store
        self.name = name
        record = store.remember_durable(
            _CATEGORY,
            name,
            {
                "amount": amount,
                "counterparty": counterparty,
                "note": note,
                "linked": linked or [],
            },
            status="draft",
        )
        self._record = record

    @classmethod
    def open(cls, store: MemoryStore, name: str) -> "Agreement | None":
        record = store.recall_durable(_CATEGORY, name)
        if record is None:
            return None
        agreement = cls.__new__(cls)
        agreement.store = store
        agreement.name = name
        agreement._record = record
        return agreement

    @property
    def state(self) -> str:
        return self._record.get("status") or "draft"

    @property
    def body(self) -> dict[str, Any]:
        return self._record.get("body") or {}

    def advance(self, next_state: str) -> dict[str, Any]:
        if next_state not in _ORDER:
            raise AgreementError(f"unknown agreement state {next_state!r}")
        if _ORDER[next_state] <= _ORDER[self.state]:
            raise AgreementError(
                f"cannot move agreement from {self.state!r} to {next_state!r}"
            )
        record = self.store.remember_durable(
            _CATEGORY,
            self.name,
            self.body,
            status=next_state,
        )
        self.store.record_event(
            evaluated={"agreement": self.name, "from": self.state, "to": next_state},
            acted=[f"agreement {self.name}: {self.state} -> {next_state}"],
        )
        self._record = record
        return record
