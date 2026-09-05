"""Tamper-evident journal seal.

Every COLD journal event is folded into a chained SHA-256 head, stored in
the HOT tier. `verify_journal` recomputes the chain: editing, inserting,
or deleting any journal event breaks verification. The chain proves the
agent's audit trail is append-only, the "no record, no action" claim made
verifiable.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .store import MemoryStore

_SEAL_STATE_KEY = "journal_seal"


def _canonical(event: dict[str, Any]) -> bytes:
    payload = {
        "id": event.get("id"),
        "ts": event.get("ts"),
        "evaluated": event.get("evaluated"),
        "acted": event.get("acted"),
    }
    return json.dumps(payload, sort_keys=True, default=str).encode("utf-8")


def _chain_head(events: list[dict[str, Any]]) -> str:
    head = ""
    for event in events:
        head = hashlib.sha256(
            head.encode("utf-8") + _canonical(event)
        ).hexdigest()
    return head


def seal_journal(store: MemoryStore) -> dict[str, Any]:
    """Fold the whole journal into a chain head and persist it."""
    events = store.timeline(limit=100000)
    events.sort(key=lambda e: (str(e.get("ts") or ""), str(e.get("id") or "")))
    head = _chain_head(events)
    store.set_working_state(
        _SEAL_STATE_KEY, {"head": head, "count": len(events)}
    )
    return {"head": head, "count": len(events)}


def verify_journal(store: MemoryStore) -> dict[str, Any]:
    """Recompute the chain and compare with the stored seal."""
    state = store.get_working_state(_SEAL_STATE_KEY)
    events = store.timeline(limit=100000)
    events.sort(key=lambda e: (str(e.get("ts") or ""), str(e.get("id") or "")))
    head = _chain_head(events)
    if state is None:
        return {"ok": False, "detail": "journal has never been sealed"}
    stored = state.get("head")
    if stored != head:
        return {
            "ok": False,
            "detail": (
                f"journal tampered: chain head {head[:12]} does not match "
                f"sealed head {str(stored)[:12]}"
            ),
        }
    return {"ok": True, "head": head, "count": len(events)}
