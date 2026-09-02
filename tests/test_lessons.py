"""Lesson tests: failures remembered so they are not repeated."""
from __future__ import annotations

import pytest

from core.memory.lessons import learn, lessons
from core.memory.store import MemoryStore


def test_learn_stores_lesson_with_severity(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        learn(store, "contractor vanished after prepayment", severity="high")
        records = lessons(store)
        assert len(records) == 1
        body = records[0]["body"]
        assert body["severity"] == "high"
        assert "prepayment" in body["value"]
    finally:
        store.close()


def test_learn_rejects_unknown_severity(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        with pytest.raises(ValueError):
            learn(store, "something failed", severity="catastrophic")
    finally:
        store.close()


def test_learn_is_journaled_for_replay(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        learn(store, "contractor vanished after prepayment")
        timeline = store.timeline(limit=5)
        assert any(
            "learned (medium)" in line
            for event in timeline
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def test_lesson_is_durable_and_recallable(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        learn(store, "never trust unverified invoices")
        record = store.recall_durable("lesson", "never_trust_unverified_invoices")
        assert record is not None
    finally:
        store.close()


def _acted_lines(event):
    acted = event.get("acted")
    if isinstance(acted, str):
        return [acted]
    return list(acted or [])
