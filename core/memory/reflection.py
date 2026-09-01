"""Reflection: turn repeated journal patterns into proposed preferences.

Reflection is deliberately deterministic: the same journal always
produces the same proposals. Nothing here calls a model. Patterns are
summarized with the Sibyl SDK's local deterministic summarizer (zero
network, free-tier-safe) and written as durable preference entities in
'proposed' status.

A proposal is not a preference yet. It must be explicitly accepted,
which promotes the entity to 'active' status and journals the decision.
Rejecting archives it with a reason. This keeps memory honest: the
agent never starts acting on something it merely inferred.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sibyl_memory_client import LocalDeterministicSummarizer

from .store import MemoryStore

_CATEGORY = "preference"
_PROPOSED = "proposed"
_ACTIVE = "active"


def _acted_lines(event: dict[str, Any]) -> list[str]:
    acted = event.get("acted")
    if isinstance(acted, str):
        return [acted]
    if isinstance(acted, list):
        return [str(item) for item in acted]
    return []


def _signature(line: str) -> str:
    return " ".join(line.lower().split())


def _slug(signature: str) -> str:
    return ("proposal_" + "_".join(signature.split()[:4]))[:40].rstrip("_")


def reflect(
    store: MemoryStore,
    *,
    since: str | None = None,
    limit: int = 100,
    min_hits: int = 2,
) -> dict[str, Any]:
    """Detect repeated actions in the journal and propose them as skills."""
    events = store.timeline(since=since, limit=limit)

    counts: Counter[str] = Counter()
    by_signature: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        for line in _acted_lines(event):
            signature = _signature(line)
            counts[signature] += 1
            by_signature.setdefault(signature, []).append(event)

    summarizer = LocalDeterministicSummarizer()
    proposals: list[str] = []
    for signature, count in counts.most_common():
        if count < min_hits:
            continue
        slug = _slug(signature)
        title = " ".join(word.capitalize() for word in signature.split()[:4])
        body, _ = summarizer.summarize(
            "repeated_action",
            by_signature[signature],
            {"action_signature": signature, "title": title},
        )
        store.remember_durable(
            _CATEGORY,
            slug,
            {
                "value": body,
                "evidence_count": count,
                "proposed_at": datetime.now(timezone.utc).isoformat(),
            },
            status=_PROPOSED,
        )
        proposals.append(slug)

    return {"events_scanned": len(events), "proposals": proposals}


def pending(store: MemoryStore) -> list[dict[str, Any]]:
    return store.list_durable(_CATEGORY, status=_PROPOSED)


def accept(store: MemoryStore, name: str) -> dict[str, Any] | None:
    record = store.recall_durable(_CATEGORY, name)
    if record is None:
        return None
    body = dict(record.get("body") or {})
    body["accepted_at"] = datetime.now(timezone.utc).isoformat()
    store.remember_durable(_CATEGORY, name, body, status=_ACTIVE)
    store.record_event(
        evaluated={"proposal": name},
        acted=[f"accepted proposal {name}"],
    )
    return store.recall_durable(_CATEGORY, name)


def reject(store: MemoryStore, name: str) -> bool:
    record = store.recall_durable(_CATEGORY, name)
    if record is None:
        return False
    store.archive_durable(_CATEGORY, name, reason="rejected proposal")
    store.record_event(
        evaluated={"proposal": name},
        acted=[f"rejected proposal {name}"],
    )
    return True
