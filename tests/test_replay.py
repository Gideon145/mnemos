"""Replay tests: the causal chain as the journal recorded it."""
from __future__ import annotations

from core.agent.replay import replay
from core.memory.agreement import Agreement
from core.memory.store import MemoryStore


def test_replay_empty_store(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = replay(store, "contractor")
        assert result.events == 0
        assert "nothing in memory" in result.text
    finally:
        store.close()


def test_replay_returns_chain_oldest_first(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        agreement = Agreement(store, "contractor", amount=160)
        agreement.advance("agreed")
        agreement.advance("delegated")
        store.record_event(acted=["payment refused: contractor not delivered"])

        result = replay(store, "contractor")
        assert result.events == 3
        first = result.text.index("draft -> agreed")
        last = result.text.index("payment refused")
        assert first < last
    finally:
        store.close()


def test_replay_is_case_insensitive(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(acted=["remembered preference AnswerStyle"])
        result = replay(store, "answerstyle")
        assert result.events == 1
    finally:
        store.close()


def test_replay_ignores_unrelated_subjects(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(acted=["task fencing: queued -> working"])
        result = replay(store, "flights")
        assert result.events == 0
    finally:
        store.close()
