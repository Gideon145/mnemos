"""Pulse tests: the proactive queue is deterministic and decline-safe."""
from __future__ import annotations

from core.memory.lessons import learn
from core.memory.pulse import candidates, decline, pulse
from core.memory.store import MemoryStore
from core.memory.tasks import Task


def test_high_severity_lesson_raises_a_matter(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        learn(store, "the price feed lied during settlement", severity="high")

        result = pulse(store)

        assert result["matter"] is not None
        assert result["matter"]["kind"] == "lesson"
        assert "price feed" in result["matter"]["text"]
        assert result["queued"] == 1
    finally:
        store.close()


def test_fresh_store_has_nothing_queued(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = pulse(store)
        assert result["matter"] is None
        assert result["queued"] == 0
    finally:
        store.close()


def test_declined_matter_never_returns(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        learn(store, "the price feed lied during settlement", severity="high")
        first = pulse(store)

        assert decline(store, first["matter"]["id"]) is True
        second = pulse(store)

        assert second["matter"] is None
        assert second["queued"] == 0
    finally:
        store.close()


def test_blocked_task_queues_after_lessons(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        task = Task(store, "ship", objective="ship the release")
        task.advance("working")
        task.advance("blocked")
        learn(store, "the price feed lied during settlement", severity="high")

        queued = candidates(store)

        assert queued[0]["kind"] == "lesson"
        assert any(matter["kind"] == "blocked_task" for matter in queued)
    finally:
        store.close()
