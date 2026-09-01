"""Recap tests: the journal reported back as an audit."""
from __future__ import annotations

from core.agent.recap import recap
from core.memory.store import MemoryStore


def test_empty_store_recap(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = recap(store)
        assert result.events == 0
        assert result.agreements == ()
        assert "journal is empty" in result.text
    finally:
        store.close()


def test_recap_lists_events_in_order(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(acted=["first thing"])
        store.record_event(acted=["second thing"])
        result = recap(store)
        assert result.events == 2
        first = result.text.index("first thing")
        second = result.text.index("second thing")
        assert first < second
    finally:
        store.close()


def test_recap_reports_agreement_states(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "agreement",
            "contractor",
            {"amount": 160, "counterparty": "alice"},
            status="delivered",
        )
        result = recap(store)
        assert ("contractor", "delivered") in result.agreements
        assert "contractor: delivered" in result.text
        assert "amount=160" in result.text
    finally:
        store.close()


def test_recap_counts_preferences(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("preference", "style", {"value": "short"})
        result = recap(store)
        assert result.preferences == 1
    finally:
        store.close()
