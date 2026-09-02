"""Replay: the causal chain for any remembered subject.

Every memory write, recall, decision, and refusal leaves a journal
event. Replay walks that journal for one subject and returns the chain
in chronological order, so a change in behavior can be explained by the
memory that caused it.

This is the honest version of "why did the agent do that": the answer
is whatever the journal actually recorded, with timestamps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..memory.store import MemoryStore


@dataclass(frozen=True)
class Replay:
    subject: str
    text: str
    events: int


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


def replay(
    store: MemoryStore,
    subject: str,
    *,
    limit: int = 200,
) -> Replay:
    subject_lower = subject.lower()
    matching: list[dict[str, Any]] = []
    for event in store.timeline(limit=limit):
        flattened = " ".join(
            str(event.get(key) or "") for key in ("acted", "evaluated", "extra")
        ).lower()
        if subject_lower in flattened:
            matching.append(event)

    matching.reverse()  # journal is newest-first; a chain reads oldest-first
    if not matching:
        return Replay(
            subject=subject,
            text=f"nothing in memory mentions {subject!r}",
            events=0,
        )
    lines = [f"causal chain for {subject!r}:", ""]
    lines.extend(_event_line(event) for event in matching)
    return Replay(subject=subject, text="\n".join(lines), events=len(matching))
