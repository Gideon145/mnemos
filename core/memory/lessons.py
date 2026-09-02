"""Lessons: memory of what went wrong, so it stays wrong only once.

A lesson is a durable entity that records an outcome and its severity.
It is not a preference: it exists because something failed. The recall
engine surfaces lessons alongside preferences, so the next time the
same situation comes up, the agent remembers the scar before it acts.

This is the failure-shaped memory pattern: store the failure itself,
not just a log line about it.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from .store import MemoryStore

_CATEGORY = "lesson"
SEVERITIES = ("low", "medium", "high")


def _slug(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    slug = slug[:limit].rstrip("_")
    return slug or "lesson"


def learn(
    store: MemoryStore,
    text: str,
    *,
    severity: str = "medium",
) -> dict[str, Any]:
    if severity not in SEVERITIES:
        raise ValueError(f"severity must be one of {SEVERITIES}, got {severity!r}")
    name = _slug(text)
    record = store.remember_durable(
        _CATEGORY,
        name,
        {
            "value": text,
            "severity": severity,
            "learned_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    store.record_event(
        evaluated={"lesson": name, "severity": severity},
        acted=[f"learned ({severity}): {text}"],
    )
    return record


def lessons(store: MemoryStore) -> list[dict[str, Any]]:
    return store.list_durable(_CATEGORY)
