"""Tiered memory store over the Sibyl Memory SDK.

Tiers
-----
durable
    Entities in the WARM tier: preferences, agreements, identity. This is
    the critical path. Without it, Mnemos cannot recall anything it was
    ever told.
daily
    Journal events in the COLD tier: decisions, outcomes, handoffs, in
    time order. Supports time-travel reads via since/until windows.
session
    State documents in the HOT tier: the working set for the current
    turn. Never load-bearing; dropped between sessions.

There is deliberately no fallback path that restores durable recall
without the store. Deleting the database breaks recall and gates by
construction, which is the point.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from sibyl_memory_client import MemoryClient

DURABLE_CATEGORIES = ("preference", "agreement", "identity", "task", "lesson")


class MemoryStore:
    """A typed view over the memory tiers."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._client = MemoryClient.local(self.db_path)

    def close(self) -> None:
        """Release the underlying connection (required before file deletion on Windows)."""
        self._client.storage.close()

    # ------------------------------------------------------------------ #
    # durable tier (entities)
    # ------------------------------------------------------------------ #
    def remember_durable(
        self,
        category: str,
        name: str,
        body: dict[str, Any],
        *,
        status: str | None = None,
    ) -> dict[str, Any]:
        if category not in DURABLE_CATEGORIES:
            raise ValueError(
                f"category {category!r} is not durable; "
                f"expected one of {DURABLE_CATEGORIES}"
            )
        return self._client.set_entity(category, name, body, status=status)

    def recall_durable(self, category: str, name: str) -> dict[str, Any] | None:
        try:
            return self._client.get_entity(category, name)
        except Exception:
            return None

    def list_durable(
        self,
        category: str | None = None,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self._client.list_entities(category, status=status, limit=limit)

    def archive_durable(
        self, category: str, name: str, reason: str | None = None
    ) -> dict[str, Any]:
        return self._client.archive_entity(category, name, reason)

    def forget_durable(self, category: str, name: str) -> bool:
        return self._client.delete_entity(category, name)

    # ------------------------------------------------------------------ #
    # daily tier (journal)
    # ------------------------------------------------------------------ #
    def record_event(
        self,
        *,
        acted: Any = None,
        evaluated: Any = None,
        forward: Any = None,
        extra: Any = None,
    ) -> str:
        return self._client.write_event(
            evaluated=evaluated, acted=acted, forward=forward, extra=extra
        )

    def timeline(
        self,
        *,
        limit: int = 50,
        since: str | None = None,
        until: str | None = None,
    ) -> list[dict[str, Any]]:
        return self._client.read_events(limit=limit, since=since, until=until)

    # ------------------------------------------------------------------ #
    # session tier (state)
    # ------------------------------------------------------------------ #
    def set_working_state(self, key: str, body: dict[str, Any]) -> None:
        self._client.set_state(key, body)

    def get_working_state(self, key: str) -> dict[str, Any] | None:
        value = self._client.get_state(key)
        return value.get("body") if value else None

    # ------------------------------------------------------------------ #
    # search
    # ------------------------------------------------------------------ #
    def search(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        return self._client.search_entities(query, limit=limit)
