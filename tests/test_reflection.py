"""Reflection tests: journal patterns become proposals, not preferences."""
from __future__ import annotations

from core.memory.reflection import accept, pending, reflect, reject
from core.memory.store import MemoryStore


def test_repeated_action_becomes_proposal(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(acted=["user asked to keep replies brief"])
        store.record_event(acted=["user asked to keep replies brief"])

        report = reflect(store)

        assert report["events_scanned"] == 2
        assert len(report["proposals"]) == 1
        name = report["proposals"][0]
        record = store.recall_durable("preference", name)
        assert record is not None
        assert record.get("status") == "proposed"
    finally:
        store.close()


def test_single_occurrence_is_not_proposed(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(acted=["one-off thing"])
        report = reflect(store)
        assert report["proposals"] == []
    finally:
        store.close()


def test_pending_lists_only_proposals(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("preference", "real_one", {"value": "x"})
        for _ in range(2):
            store.record_event(acted=["user asked to keep replies brief"])
        reflect(store)

        names = [record["name"] for record in pending(store)]
        assert "proposal_user_asked_to_keep" in names
        assert "real_one" not in names
    finally:
        store.close()


def test_accept_promotes_and_journals(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        for _ in range(2):
            store.record_event(acted=["user asked to keep replies brief"])
        name = reflect(store)["proposals"][0]

        record = accept(store, name)
        assert record is not None
        assert record.get("status") == "active"

        timeline = store.timeline(limit=5)
        assert any(
            "accepted proposal" in line
            for event in timeline
            for line in _acted(event)
        )
    finally:
        store.close()


def test_reject_archives(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        for _ in range(2):
            store.record_event(acted=["user asked to keep replies brief"])
        name = reflect(store)["proposals"][0]

        assert reject(store, name) is True
        assert store.recall_durable("preference", name) is None
    finally:
        store.close()


def _acted(event):
    acted = event.get("acted")
    return [acted] if isinstance(acted, str) else list(acted or [])
