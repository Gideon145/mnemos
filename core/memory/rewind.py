"""Rewind: memory state at any past moment, with the diff to now.

Every entity body carries an append-only `history` of superseded
values with timestamps (written by revise). Rewind reconstructs the
value each entity held at a timestamp by walking that history
backwards, and reports which entities have changed since.

Deterministic and read-only: rewind never writes, and it answers only
from what the store and the journal actually record.
"""
from __future__ import annotations

from typing import Any

from .store import DURABLE_CATEGORIES, MemoryStore


def _event_ts(event: dict[str, Any]) -> str:
    return str(event.get("ts") or event.get("created_at") or "")


def _acted_text(event: dict[str, Any]) -> str:
    acted = event.get("acted")
    if isinstance(acted, str):
        return acted
    if isinstance(acted, list):
        return " ".join(
            item if isinstance(item, str) else str(item) for item in acted
        )
    return ""


def _first_mention(store: MemoryStore, name: str) -> str:
    """Earliest journal timestamp that mentions the entity name."""
    earliest = ""
    for event in store.timeline(limit=1000):
        ts = _event_ts(event)
        if not ts:
            continue
        if name and name in _acted_text(event).replace(" ", ""):
            if not earliest or ts < earliest:
                earliest = ts
    return earliest


def _value_at(body: dict[str, Any], at: str) -> Any:
    """Walk the revision history backwards to the value current at `at`."""
    value = body.get("value")
    for entry in reversed(body.get("history") or []):
        superseded_at = entry.get("superseded_at")
        if not superseded_at or superseded_at > at:
            value = entry.get("value")
        else:
            break
    return value


def rewind(store: MemoryStore, at: str) -> dict[str, Any]:
    """Reconstruct what memory held at `at`, and what changed since."""
    snapshot: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    for category in DURABLE_CATEGORIES:
        for record in store.list_durable(category):
            name = str(record.get("name"))
            first_ts = str(record.get("created_at") or "")
            if not first_ts:
                first_ts = _first_mention(store, name)
            if not first_ts or first_ts > at:
                continue
            body = record.get("body") or {}
            past_value = _value_at(body, at)
            current = body.get("value")
            snapshot.append(
                {
                    "category": category,
                    "name": name,
                    "value": past_value,
                    "status": record.get("status"),
                }
            )
            if past_value != current:
                changed.append(
                    {
                        "category": category,
                        "name": name,
                        "at": past_value,
                        "now": current,
                    }
                )
    return {
        "at": at,
        "entities": snapshot,
        "changed": changed,
        "changed_count": len(changed),
    }
