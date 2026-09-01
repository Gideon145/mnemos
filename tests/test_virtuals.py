"""Virtuals registration write-back tests."""
from __future__ import annotations

from core.integrations.virtuals import register_with_virtuals
from core.memory.store import MemoryStore


def test_dry_run_writes_honest_identity(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = register_with_virtuals(store, name="mnemos")
        assert result.registered is False
        record = store.recall_durable("identity", "virtuals_agent")
        assert record is not None
        assert record["body"]["registered"] is False
        assert "dry run" in record["body"]["note"]
    finally:
        store.close()


def test_registration_survives_reopen(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        register_with_virtuals(store, name="mnemos")
        record = store.recall_durable("identity", "virtuals_agent")
        assert record["body"]["requested_name"] == "mnemos"
    finally:
        store.close()


def test_registration_is_journaled(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        register_with_virtuals(store)
        timeline = store.timeline(limit=5)
        assert any(
            "virtuals registration attempt" in line
            for event in timeline
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def _acted_lines(event):
    acted = event.get("acted")
    if isinstance(acted, str):
        return [acted]
    return list(acted or [])
