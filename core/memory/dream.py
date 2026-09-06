"""Dream: background consolidation proposals from the journal.

Dream scans the journal since the last dream and proposes
consolidations, each review-gated. Nothing applies itself: a proposal
is written as a durable entity in 'proposed' status, and only an
explicit apply promotes it and journals the decision.

Deterministic. No model is involved: the same journal always yields
the same proposals.

Kinds
-----
repeat
    The same action signature appeared at least `min_hits` times. The
    proposal records the pattern so it is recognized next time.
miss
    A question was asked and memory answered that it held nothing. The
    proposal records the gap so it can be filled explicitly.
refusal
    A payment was refused by the gate. The proposal records the
    refusal reason so the cause is remembered.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from .store import MemoryStore

_CURSOR_CATEGORY = "identity"
_CURSOR_NAME = "dream_cursor"
_PROPOSAL_CATEGORY = "preference"
_PROPOSED = "proposed"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _slug(text: str, limit: int = 44) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    slug = slug[:limit].rstrip("_")
    return slug or "proposal"


def _cursor(store: MemoryStore) -> str:
    record = store.recall_durable(_CURSOR_CATEGORY, _CURSOR_NAME)
    if record is None:
        return ""
    return str((record.get("body") or {}).get("last_ts") or "")


def _advance_cursor(store: MemoryStore, latest_ts: str) -> None:
    store.remember_durable(
        _CURSOR_CATEGORY,
        _CURSOR_NAME,
        {"last_ts": latest_ts, "advanced_at": _now()},
    )


def _propose(
    store: MemoryStore,
    kind: str,
    value: str,
    evidence: int,
    *,
    evidence_text: str | None = None,
) -> str:
    name = f"dream_{kind}_{_slug(value)}"
    body: dict[str, Any] = {
        "value": value,
        "kind": kind,
        "evidence_count": evidence,
        "proposed_at": _now(),
    }
    if evidence_text:
        body["evidence"] = evidence_text
    store.remember_durable(_PROPOSAL_CATEGORY, name, body, status=_PROPOSED)
    store.record_event(
        evaluated={"proposal": name, "kind": kind},
        acted=[f"dream proposed {kind}: {value[:60]}"],
    )
    return name


def dream(
    store: MemoryStore,
    *,
    limit: int = 500,
    min_hits: int = 2,
) -> dict[str, Any]:
    """Scan the journal since the last dream and write proposals."""
    cursor = _cursor(store)
    events = store.timeline(limit=limit)
    unseen = [event for event in events if _event_ts(event) > cursor]

    signatures: Counter[str] = Counter()
    misses: list[str] = []
    refusals: list[str] = []
    latest_ts = cursor
    for event in unseen:
        ts = _event_ts(event)
        if ts and ts > latest_ts:
            latest_ts = ts
        acted = _acted_text(event)
        collapsed = acted.replace(" ", "")
        evaluated = event.get("evaluated") or {}

        # Housekeeping events are not patterns to learn from.
        housekeeping = "resetmemory" in collapsed or collapsed.startswith("dream")
        if acted and not housekeeping:
            signatures[acted.lower()] += 1

        found = evaluated.get("found")
        if found is False:
            question = str(evaluated.get("question") or acted or "a question")
            misses.append(question)

        if "refused" in collapsed or "paymentrefused" in collapsed:
            reason = str(evaluated.get("reason") or acted or "payment refused")
            refusals.append(reason)

    proposals: list[str] = []
    for signature, count in signatures.most_common():
        if count < min_hits:
            continue
        proposals.append(
            _propose(
                store,
                "repeat",
                signature,
                count,
                evidence_text=f"seen {count} times since last dream",
            )
        )

    for question in misses[-5:]:
        proposals.append(
            _propose(
                store,
                "miss",
                question,
                1,
                evidence_text="asked, memory held nothing",
            )
        )

    for reason in refusals[-5:]:
        proposals.append(
            _propose(store, "refusal", reason, 1, evidence_text="gate said no")
        )

    if latest_ts:
        # Proposals were journaled while scanning; move the cursor past
        # them too, or the next dream would re-read its own output.
        for event in store.timeline(limit=500):
            ts = _event_ts(event)
            if ts and ts > latest_ts:
                latest_ts = ts
        _advance_cursor(store, latest_ts)

    return {
        "events_scanned": len(unseen),
        "proposals": proposals,
        "kinds": {
            "repeat": sum(1 for item in proposals if item.startswith("dream_repeat_")),
            "miss": sum(1 for item in proposals if item.startswith("dream_miss_")),
            "refusal": sum(
                1 for item in proposals if item.startswith("dream_refusal_")
            ),
        },
    }


def pending(store: MemoryStore) -> list[dict[str, Any]]:
    return store.list_durable(_PROPOSAL_CATEGORY, status=_PROPOSED)


def apply(store: MemoryStore, name: str, severity: str = "medium") -> dict[str, Any] | None:
    """Promote a dream proposal to an active lesson."""
    record = store.recall_durable(_PROPOSAL_CATEGORY, name)
    if record is None or record.get("status") != _PROPOSED:
        return None
    body = record.get("body") or {}
    value = str(body.get("value") or name)
    lesson_name = _slug(value)
    from .lessons import learn

    learn(store, value, severity=severity)
    store.archive_durable(
        _PROPOSAL_CATEGORY, name, reason=f"applied as lesson {lesson_name}"
    )
    store.record_event(
        evaluated={"proposal": name, "lesson": lesson_name},
        acted=[f"dream applied {name}"],
    )
    return store.recall_durable("lesson", lesson_name)


def reject(store: MemoryStore, name: str) -> bool:
    record = store.recall_durable(_PROPOSAL_CATEGORY, name)
    if record is None or record.get("status") != _PROPOSED:
        return False
    store.archive_durable(_PROPOSAL_CATEGORY, name, reason="rejected dream proposal")
    store.record_event(
        evaluated={"proposal": name},
        acted=[f"dream rejected {name}"],
    )
    return True
