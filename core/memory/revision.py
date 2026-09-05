"""Revision: correcting a fact retroactively governs what the agent may do.

Most memory systems go memory -> correction -> updated memory, and the
past keeps working as if nothing happened. Mnemos goes memory ->
correction -> dependency walk -> affected decisions and actions ->
suspect state -> the execution gate closes -> explicit reconsideration
reopens it.

Everything here is deterministic. No model is involved in deciding
whether something is affected. The dependency walk reads only what the
journal and the entity links already record.

State model
-----------
- A fact entity (preference / identity / lesson) carries its value and
  an append-only history of every superseded value.
- A revision is identified by the journal event id that recorded it.
- Affected agreements and tasks carry `tainted_by`: the revision ids
  whose facts they depended on, each with the fact reference.
- Reconsideration appends a review for each taint and either clears it
  (decision valid) or keeps it (decision invalid).
- An entity is suspect while any taint entry has no valid review.

Nothing is ever deleted. History is append-only; the gate only reads
the current suspect state.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .store import DURABLE_CATEGORIES, MemoryStore

_TAINTABLE = ("agreement", "task")


def _ref(category: str, name: str) -> str:
    return f"{category}:{name}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _suspect_entries(record: dict[str, Any]) -> list[dict[str, Any]]:
    body = record.get("body") or {}
    reviews = {
        entry["revision_id"]: entry
        for entry in body.get("reviews") or []
        if isinstance(entry, dict)
    }
    pending: list[dict[str, Any]] = []
    for entry in body.get("tainted_by") or []:
        if not isinstance(entry, dict):
            continue
        review = reviews.get(entry.get("revision_id"))
        if review is None or review.get("decision") != "valid":
            pending.append(entry)
    return pending


def is_suspect(store: MemoryStore, category: str, name: str) -> bool:
    record = store.recall_durable(category, name)
    if record is None:
        return False
    return bool(_suspect_entries(record))


def suspect_reasons(store: MemoryStore, category: str, name: str) -> list[str]:
    record = store.recall_durable(category, name)
    if record is None:
        return []
    return [str(entry.get("fact")) for entry in _suspect_entries(record)]


def blast_radius(store: MemoryStore, fact_ref: str) -> dict[str, Any]:
    """Deterministic walk: which decisions and entities depend on a fact."""
    events = store.timeline(limit=1000)

    decisions: list[dict[str, Any]] = []
    for event in events:
        sources = (event.get("evaluated") or {}).get("sources")
        if isinstance(sources, list) and fact_ref in sources:
            decisions.append(event)

    affected: dict[str, list[str]] = {"agreement": [], "task": []}
    seen: set[str] = set()
    # One-hop: entities that link the fact directly.
    for category in _TAINTABLE:
        for record in store.list_durable(category):
            linked = list((record.get("body") or {}).get("linked") or [])
            if fact_ref in linked:
                key = f"{category}:{record.get('name')}"
                seen.add(key)
                affected[category].append(record.get("name"))
    # Two-hop: entities linked from an affected entity inherit the taint.
    for category in _TAINTABLE:
        for record in store.list_durable(category):
            name = record.get("name")
            if f"{category}:{name}" in seen:
                continue
            for linked in (record.get("body") or {}).get("linked") or []:
                if str(linked) in seen:
                    key = f"{category}:{name}"
                    seen.add(key)
                    affected[category].append(name)
                    break

    payment_events = []
    for agreement in affected["agreement"]:
        for event in events:
            evaluated = event.get("evaluated") or {}
            # The SDK stores acted strings with spaces between every
            # character; collapse whitespace before matching.
            acted_text = " ".join(str(event.get("acted") or [])).replace(" ", "")
            if evaluated.get("agreement") == agreement and "payment" in acted_text:
                payment_events.append(event)

    return {
        "fact": fact_ref,
        "decisions": len(decisions),
        "agreements": affected["agreement"],
        "tasks": affected["task"],
        "payments": len(payment_events),
    }


def revise(
    store: MemoryStore,
    category: str,
    name: str,
    new_value: str,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    """Correct a fact, then taint everything that depended on it."""
    if category not in DURABLE_CATEGORIES:
        raise ValueError(f"category {category!r} is not durable")
    record = store.recall_durable(category, name)
    if record is None:
        raise ValueError(f"no {category} named {name!r}")

    body = dict(record.get("body") or {})
    old_value = body.get("value")
    history = list(body.get("history") or [])
    history.append(
        {
            "value": old_value,
            "superseded_at": _now(),
            "reason": reason,
        }
    )
    body["value"] = new_value
    body["history"] = history
    store.remember_durable(category, name, body, status=record.get("status"))

    revision_id = store.record_event(
        evaluated={"fact": _ref(category, name), "from": old_value, "to": new_value},
        acted=[f"revised {_ref(category, name)}: {old_value} -> {new_value}"],
        extra={"reason": reason},
    )

    radius = blast_radius(store, _ref(category, name))
    newly_suspect: list[str] = []
    for taint_category in _TAINTABLE:
        for taint_name in radius[taint_category + "s"]:
            taint_record = store.recall_durable(taint_category, taint_name)
            if taint_record is None:
                continue
            taint_body = dict(taint_record.get("body") or {})
            tainted = list(taint_body.get("tainted_by") or [])
            tainted.append(
                {"revision_id": revision_id, "fact": _ref(category, name)}
            )
            taint_body["tainted_by"] = tainted
            store.remember_durable(
                taint_category,
                taint_name,
                taint_body,
                status=taint_record.get("status"),
            )
            store.record_event(
                evaluated={"entity": taint_name, "fact": _ref(category, name)},
                acted=[f"suspect {taint_category} {taint_name}: depends on revised {_ref(category, name)}"],
            )
            newly_suspect.append(f"{taint_category}:{taint_name}")

    return {
        "revision_id": revision_id,
        "fact": _ref(category, name),
        "from": old_value,
        "to": new_value,
        "decisions_affected": radius["decisions"],
        "payments_affected": radius["payments"],
        "newly_suspect": newly_suspect,
    }


def reconsider(
    store: MemoryStore,
    category: str,
    name: str,
    decision: str,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    """Review a suspect entity. valid clears each taint, invalid keeps it."""
    if decision not in ("valid", "invalid"):
        raise ValueError(f"decision must be valid or invalid, got {decision!r}")
    record = store.recall_durable(category, name)
    if record is None:
        raise ValueError(f"no {category} named {name!r}")
    body = dict(record.get("body") or {})
    pending = _suspect_entries(record)
    if not pending:
        return {"reopened": True, "reviewed": [], "note": f"{name} was not suspect"}

    reviews = list(body.get("reviews") or [])
    cleared: list[str] = []
    for entry in pending:
        reviews.append(
            {
                "revision_id": entry.get("revision_id"),
                "decision": decision,
                "reason": reason,
                "at": _now(),
            }
        )
        if decision == "valid":
            cleared.append(entry.get("revision_id"))
    body["reviews"] = reviews
    if decision == "valid":
        kept = [
            entry
            for entry in body.get("tainted_by") or []
            if entry.get("revision_id") not in cleared
        ]
        body["tainted_by"] = kept
    store.remember_durable(category, name, body, status=record.get("status"))
    store.record_event(
        evaluated={"entity": name, "decision": decision},
        acted=[f"reconsidered {category} {name}: {decision}"],
        extra={"reason": reason},
    )
    return {
        "reopened": decision == "valid" and not body.get("tainted_by"),
        "reviewed": cleared,
        "decision": decision,
    }
