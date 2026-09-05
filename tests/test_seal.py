"""Tamper-evident journal seal tests."""
from __future__ import annotations

from core.memory.seal import seal_journal, verify_journal
from core.memory.store import MemoryStore


def test_seal_then_verify_ok(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(acted=["first"])
        store.record_event(acted=["second"])
        result = seal_journal(store)
        assert result["count"] == 2
        check = verify_journal(store)
        assert check["ok"] is True
        assert check["count"] == 2
    finally:
        store.close()


def test_never_sealed_reports_missing(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(acted=["first"])
        check = verify_journal(store)
        assert check["ok"] is False
        assert "never been sealed" in check["detail"]
    finally:
        store.close()


def test_appended_event_after_seal_breaks_chain(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(acted=["first"])
        seal_journal(store)
        store.record_event(acted=["sneaked in later"])
        check = verify_journal(store)
        assert check["ok"] is False
        assert "tampered" in check["detail"]
    finally:
        store.close()


def test_empty_journal_seals_to_fixed_head(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = seal_journal(store)
        assert result["count"] == 0
        assert verify_journal(store)["ok"] is True
    finally:
        store.close()
