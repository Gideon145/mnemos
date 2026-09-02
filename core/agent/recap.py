"""Recap: a deterministic daily summary straight from the journal.

Recap is the mirror image of recall. Recall answers questions about
durable facts. Recap reports what actually happened: the journal in
time order, the standing agreements and their states, and how many
preferences are stored.

No model, no inference. The recap contains only what memory contains,
which makes it safe to show the user as an audit of the agent's day.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..memory.store import MemoryStore


@dataclass(frozen=True)
class Recap:
    text: str
    events: int
    agreements: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    preferences: int = 0


def _event_line(event: dict[str, Any]) -> str:
    ts = event.get("ts") or event.get("created_at") or "?"
    acted = event.get("acted")
    if isinstance(acted, str):
        detail = acted
    elif isinstance(acted, list) and acted:
        detail = "; ".join(str(item) for item in acted)
    else:
        detail = str(event.get("evaluated") or event.get("extra") or "(no detail)")
    return f"- {ts}: {detail}"


def _agreement_line(record: dict[str, Any]) -> str:
    body = record.get("body") or {}
    amount = body.get("amount")
    counterparty = body.get("counterparty")
    state = record.get("status") or "draft"
    bits = [f"{record.get('name')}: {state}"]
    if amount is not None:
        bits.append(f"amount={amount}")
    if counterparty:
        bits.append(f"with={counterparty}")
    return " ".join(bits)


def _lesson_line(record: dict[str, Any]) -> str:
    body = record.get("body") or {}
    severity = body.get("severity", "medium")
    value = body.get("value", "")
    return f"- ({severity}) {value}"


def recap(
    store: MemoryStore,
    *,
    since: str | None = None,
    limit: int = 20,
) -> Recap:
    events = list(reversed(store.timeline(since=since, limit=limit)))
    agreements = store.list_durable("agreement")
    preferences = store.list_durable("preference")
    lessons = store.list_durable("lesson")

    lines = ["Mnemos recap", ""]
    if events:
        lines.append(f"Journal, latest {len(events)}:")
        lines.extend(_event_line(event) for event in events)
    else:
        lines.append("Nothing happened yet. The journal is empty.")
    lines.append("")

    if agreements:
        lines.append("Standing agreements:")
        lines.extend(f"- {_agreement_line(record)}" for record in agreements)
    else:
        lines.append("No agreements on record.")
    lines.append("")

    if lessons:
        lines.append("Lessons:")
        lines.extend(f"- {_lesson_line(record)}" for record in lessons)

    return Recap(
        text="\n".join(lines),
        events=len(events),
        agreements=tuple(
            (record.get("name"), record.get("status") or "draft")
            for record in agreements
        ),
        preferences=len(preferences),
    )
