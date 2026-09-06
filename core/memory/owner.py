"""Owner profile: a curated summary, not a raw history dump.

Mirroring the pattern of a canonical owner document: identity, active
preferences, accepted principles, standing agreements, and lessons
that still veto. Compiled deterministically from durable entities, so
the same memory always yields the same profile. It is a compact
curated snapshot, deliberately separate from the full journal.
"""
from __future__ import annotations

from typing import Any

from .store import MemoryStore

_HOUSEKEEPING = {"dream_cursor", "pulse_suppress"}


def _is_active(record: dict[str, Any]) -> bool:
    return record.get("status") in (None, "active")


def owner_profile(store: MemoryStore) -> dict[str, Any]:
    identity: list[str] = []
    for record in store.list_durable("identity"):
        name = str(record.get("name"))
        if name in _HOUSEKEEPING:
            continue
        body = record.get("body") or {}
        value = body.get("value") or body.get("agent_id") or name
        identity.append(str(value))

    preferences: list[str] = []
    principles: list[str] = []
    for record in store.list_durable("preference"):
        name = str(record.get("name"))
        if not _is_active(record):
            continue
        body = record.get("body") or {}
        value = str(body.get("value") or name)
        if name.startswith("proposal_") and body.get("accepted_at"):
            principles.append(value)
        elif not name.startswith("dream_"):
            preferences.append(value)

    agreements: list[str] = []
    for record in store.list_durable("agreement"):
        body = record.get("body") or {}
        state = str(record.get("status") or "draft")
        amount = body.get("amount")
        line = f"{record.get('name')}: {state}"
        if amount is not None:
            line += f" (amount {amount})"
        agreements.append(line)

    vetoes: list[str] = []
    for record in store.list_durable("lesson"):
        body = record.get("body") or {}
        if body.get("severity") == "high" and not body.get("resolved"):
            vetoes.append(f"({body.get('severity')}) {body.get('value', '')}")

    sections: list[str] = ["# Owner profile (curated by Mnemos)"]
    if identity:
        sections.append("\n## Identity\n- " + "\n- ".join(identity))
    if preferences:
        sections.append("\n## Preferences\n- " + "\n- ".join(preferences))
    if principles:
        sections.append("\n## Principles (accepted proposals)\n- " + "\n- ".join(principles))
    if agreements:
        sections.append("\n## Standing agreements\n- " + "\n- ".join(agreements))
    if vetoes:
        sections.append("\n## Lessons that still veto\n- " + "\n- ".join(vetoes))

    return {
        "profile": "\n".join(sections).strip(),
        "identity": len(identity),
        "preferences": len(preferences),
        "principles": len(principles),
        "agreements": len(agreements),
        "vetoes": len(vetoes),
    }
