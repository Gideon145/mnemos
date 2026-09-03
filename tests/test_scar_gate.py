"""Scar-gate tests: memory of failure vetoes future actions."""
from __future__ import annotations

from core.memory.agreement import Agreement
from core.memory.gate import evaluate_payment
from core.memory.lessons import learn, resolve
from core.memory.links import link
from core.memory.store import MemoryStore


def _delivered(store, name="contractor"):
    agreement = Agreement(store, name, amount=160)
    agreement.advance("agreed")
    agreement.advance("delegated")
    agreement.advance("delivered")
    return agreement


def test_high_severity_scar_blocks_payment(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered(store)
        learn(store, "contractor vanished after prepayment", severity="high")
        link(
            store,
            "lesson",
            "contractor_vanished_after_prepayment",
            "agreement",
            "contractor",
        )
        result = evaluate_payment(store, "contractor", 160)
        assert result.allowed is False
        assert "scars block" in result.reason
    finally:
        store.close()


def test_resolved_scar_does_not_block(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered(store)
        learn(store, "contractor vanished after prepayment", severity="high")
        link(
            store,
            "lesson",
            "contractor_vanished_after_prepayment",
            "agreement",
            "contractor",
        )
        resolve(store, "contractor_vanished_after_prepayment")
        result = evaluate_payment(store, "contractor", 160)
        assert result.allowed is True
    finally:
        store.close()


def test_low_severity_scar_does_not_block(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered(store)
        learn(store, "invoice was late by a day", severity="low")
        link(
            store,
            "lesson",
            "invoice_was_late_by_a_day",
            "agreement",
            "contractor",
        )
        result = evaluate_payment(store, "contractor", 160)
        assert result.allowed is True
    finally:
        store.close()


def test_unlinked_scar_does_not_block(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered(store)
        learn(store, "someone else vanished", severity="high")
        result = evaluate_payment(store, "contractor", 160)
        assert result.allowed is True
    finally:
        store.close()
