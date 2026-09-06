"""Pulse: a bounded proactive queue grounded in memory.

Nothing here is a model. Pulse reads the state that already exists in
memory and raises the most urgent matter: a suspect entity the gate
refuses, an unresolved high-severity lesson, a blocked task, or a
pending dream proposal. At most one matter surfaces per tick. Declined
matters are suppressed so the same nudge never returns.

Deterministic: the same memory always yields the same queue.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from .dream import pending as dream_pending
from .revision import is_suspect
from .store import MemoryStore

_SUPPRESS_CATEGORY = "identity"
_SUPPRESS_NAME = "pulse_suppress"

# Lower number = higher urgency.
_PRIORITY = {
    "suspect": 0,
    "lesson": 1,
    "blocked_task": 2,
    "dream": 3,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:limit].rstrip("_") or "matter"


def _suppressed(store: MemoryStore) -> list[str]:
    record = store.recall_durable(_SUPPRESS_CATEGORY, _SUPPRESS_NAME)
    if record is None:
        return []
    return [str(item) for item in (record.get("body") or {}).get("suppressed") or []]


def candidates(store: MemoryStore) -> list[dict[str, Any]]:
    """Every matter memory currently raises, in priority order."""
    matters: list[dict[str, Any]] = []

    for category in ("agreement", "task"):
        for record in store.list_durable(category):
            name = record.get("name")
            if is_suspect(store, category, name):
                matters.append(
                    {
                        "id": _slug(f"suspect {category} {name}"),
                        "kind": "suspect",
                        "priority": _PRIORITY["suspect"],
                        "text": f"review suspect {category} {name}: "
                        f"it depends on a revised memory and the gate is closed",
                        "source": f"{category}:{name}",
                    }
                )

    for record in store.list_durable("lesson"):
        body = record.get("body") or {}
        if body.get("severity") == "high" and not body.get("resolved"):
            matters.append(
                {
                    "id": _slug(f"lesson {record.get('name')}"),
                    "kind": "lesson",
                    "priority": _PRIORITY["lesson"],
                    "text": f"resolve the high-severity lesson "
                    f"{body.get('value', record.get('name'))}",
                    "source": f"lesson:{record.get('name')}",
                }
            )

    for record in store.list_durable("task"):
        if record.get("status") == "blocked":
            matters.append(
                {
                    "id": _slug(f"blocked {record.get('name')}"),
                    "kind": "blocked_task",
                    "priority": _PRIORITY["blocked_task"],
                    "text": f"unblock task {record.get('name')}",
                    "source": f"task:{record.get('name')}",
                }
            )

    for record in dream_pending(store):
        body = record.get("body") or {}
        matters.append(
            {
                "id": _slug(f"dream {record.get('name')}"),
                "kind": "dream",
                "priority": _PRIORITY["dream"],
                "text": f"review the dream proposal {body.get('value', '')}",
                "source": f"proposal:{record.get('name')}",
            }
        )

    matters.sort(key=lambda matter: (matter["priority"], matter["text"]))
    return matters


def pulse(store: MemoryStore) -> dict[str, Any]:
    """Raise the most urgent unsuppressed matter, at most one per tick."""
    suppressed = set(_suppressed(store))
    queued = [matter for matter in candidates(store) if matter["id"] not in suppressed]
    top = queued[0] if queued else None
    store.record_event(
        evaluated={
            "queued": len(queued),
            "matter": top["text"] if top else None,
            "tick_at": _now(),
        },
        acted=[f"pulse tick: {top['text'] if top else 'nothing queued'}"],
    )
    return {"matter": top, "queued": len(queued), "candidates": queued}


def decline(store: MemoryStore, matter_id: str) -> bool:
    """Suppress a matter so the same nudge never returns."""
    record = store.recall_durable(_SUPPRESS_CATEGORY, _SUPPRESS_NAME)
    body = dict((record.get("body") if record else None) or {})
    suppressed = [str(item) for item in body.get("suppressed") or []]
    if matter_id not in suppressed:
        suppressed.append(matter_id)
    body["suppressed"] = suppressed
    store.remember_durable(_SUPPRESS_CATEGORY, _SUPPRESS_NAME, body)
    store.record_event(
        evaluated={"matter": matter_id},
        acted=[f"pulse declined {matter_id}"],
    )
    return True
