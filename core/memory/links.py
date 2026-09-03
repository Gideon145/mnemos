"""Relational breadcrumbs between durable entities.

Sibyl's index files link projects to entities and archives to entities.
Mnemos makes that explicit: any two durable entities can be linked in
both directions, so recalling one surfaces the other. A lesson links to
the agreement it came from; a task links to the preference that shaped
it; an agreement links to the agent it was delegated to.

The link is stored inside each entity's body, so it travels with
keepsakes and survives deletion of everything except memory itself.
"""
from __future__ import annotations

from typing import Any

from .store import DURABLE_CATEGORIES, MemoryStore


def _ref(category: str, name: str) -> str:
    return f"{category}:{name}"


def link(
    store: MemoryStore,
    category_a: str,
    name_a: str,
    category_b: str,
    name_b: str,
) -> dict[str, Any]:
    if category_a not in DURABLE_CATEGORIES:
        raise ValueError(f"category {category_a!r} is not durable")
    if category_b not in DURABLE_CATEGORIES:
        raise ValueError(f"category {category_b!r} is not durable")

    record_a = store.recall_durable(category_a, name_a)
    record_b = store.recall_durable(category_b, name_b)
    if record_a is None:
        raise ValueError(f"no {category_a} named {name_a!r}")
    if record_b is None:
        raise ValueError(f"no {category_b} named {name_b!r}")

    ref_a, ref_b = _ref(category_a, name_a), _ref(category_b, name_b)
    for record, other in ((record_a, ref_b), (record_b, ref_a)):
        body = dict(record.get("body") or {})
        linked = list(body.get("linked") or [])
        if other not in linked:
            linked.append(other)
        body["linked"] = linked
        store.remember_durable(
            record.get("category"),
            record.get("name"),
            body,
            status=record.get("status"),
        )

    store.record_event(
        evaluated={"from": ref_a, "to": ref_b},
        acted=[f"linked {ref_a} <-> {ref_b}"],
    )
    return {"linked": [ref_a, ref_b]}


def links_of(store: MemoryStore, category: str, name: str) -> list[str]:
    record = store.recall_durable(category, name)
    if record is None:
        return []
    return list((record.get("body") or {}).get("linked") or [])
