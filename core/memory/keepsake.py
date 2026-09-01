"""Portable memory packs: Keepsakes (.mne).

A Keepsake serializes the durable entities and journal events of a store
into one human-inspectable JSON file, so a fresh Mnemos on a fresh
machine can recall everything the previous instance learned.

The pack carries a canonical digest of its payload. Import merges
records into a fresh store and reports what changed; it never silently
overwrites newer local records.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .store import MemoryStore

FORMAT_VERSION = 1


def export_keepsake(store: MemoryStore, path: str | Path) -> dict[str, Any]:
    """Write the store's durable tier and journal into a .mne pack."""
    entities = store.list_durable(limit=1000)
    events = store.timeline(limit=1000)

    payload: dict[str, Any] = {
        "mnemos_version": "0.1.0",
        "format_version": FORMAT_VERSION,
        "entities": entities,
        "events": events,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    pack = {
        "digest": digest,
        "payload": payload,
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    return {
        "path": str(out),
        "entities": len(entities),
        "events": len(events),
        "digest": digest[:16],
    }


def import_keepsake(store: MemoryStore, path: str | Path) -> dict[str, Any]:
    """Merge a .mne pack into a store; report conflicts without overwriting."""
    pack = json.loads(Path(path).read_text(encoding="utf-8"))
    payload = pack["payload"]

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if digest != pack["digest"]:
        raise ValueError("keepsake digest mismatch: pack has been modified")

    imported = 0
    skipped = 0
    for entity in payload["entities"]:
        category = entity.get("category")
        name = entity.get("name")
        body = entity.get("body") or {}
        status = entity.get("status")
        existing = store.recall_durable(category, name)
        if existing is not None:
            skipped += 1
            continue
        store.remember_durable(category, name, body, status=status)
        imported += 1

    events_imported = 0
    for event in payload["events"]:
        store.record_event(
            evaluated=event.get("evaluated"),
            acted=event.get("acted"),
            forward=event.get("forward"),
            extra=event.get("extra") or {"keepsake_import": str(path)},
        )
        events_imported += 1

    return {
        "entities_imported": imported,
        "entities_skipped": skipped,
        "events_imported": events_imported,
    }
