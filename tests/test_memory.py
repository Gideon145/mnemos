"""Phase 1 tests: tiers, agreements, keepsakes, gates, and the deletion test."""
import tempfile
from pathlib import Path

import pytest

from core.memory import (
    Agreement,
    AgreementError,
    MemoryStore,
    evaluate_payment,
    export_keepsake,
    import_keepsake,
)


@pytest.fixture()
def store(tmp_path: Path) -> MemoryStore:
    return MemoryStore(tmp_path / "memory.db")


def test_durable_roundtrip(store: MemoryStore) -> None:
    store.remember_durable("preference", "answer-style", {"value": "short"})
    record = store.recall_durable("preference", "answer-style")
    assert record is not None
    assert record["body"]["value"] == "short"
    assert record["category"] == "preference"


def test_durable_rejects_unknown_category(store: MemoryStore) -> None:
    with pytest.raises(ValueError):
        store.remember_durable("scratch", "x", {"v": 1})


def test_agreement_state_machine(store: MemoryStore) -> None:
    agreement = Agreement(store, "banner-job", amount=60, counterparty="alex")
    assert agreement.state == "draft"

    agreement.advance("agreed")
    agreement.advance("delegated")
    agreement.advance("delivered")
    assert agreement.state == "delivered"

    # reopening sees the same state
    reopened = Agreement.open(store, "banner-job")
    assert reopened is not None
    assert reopened.state == "delivered"
    assert reopened.body["amount"] == 60


def test_agreement_cannot_move_backward(store: MemoryStore) -> None:
    agreement = Agreement(store, "job", amount=10)
    agreement.advance("agreed")
    with pytest.raises(AgreementError):
        agreement.advance("draft")
    with pytest.raises(AgreementError):
        agreement.advance("unknown-state")


def test_journal_time_travel(store: MemoryStore) -> None:
    store.record_event(acted=["first"])
    first_ts = store.timeline()[0]["ts"]
    store.record_event(acted=["second"])
    window = store.timeline(since=first_ts)
    assert len(window) >= 1


def test_search_finds_entity(store: MemoryStore) -> None:
    store.remember_durable("agreement", "contractor-rate", {"rate_usd_hr": 40})
    hits = store.search("contractor")
    assert len(hits) >= 1


def test_keepsake_roundtrip(store: MemoryStore, tmp_path: Path) -> None:
    store.remember_durable("preference", "answer-style", {"value": "short"})
    store.remember_durable("agreement", "contractor-rate", {"rate_usd_hr": 40})
    store.record_event(acted=["taught answer-style"])

    pack_path = tmp_path / "mnemos.mne"
    summary = export_keepsake(store, pack_path)
    assert summary["entities"] == 2

    fresh = MemoryStore(tmp_path / "fresh.db")
    result = import_keepsake(fresh, pack_path)
    assert result["entities_imported"] == 2
    assert fresh.recall_durable("agreement", "contractor-rate") is not None


def test_deletion_closes_every_gate(tmp_path: Path) -> None:
    db = tmp_path / "memory.db"
    store = MemoryStore(db)
    agreement = Agreement(store, "banner-job", amount=60)
    for state in ("agreed", "delegated", "delivered"):
        agreement.advance(state)

    allowed = evaluate_payment(store, "banner-job", 60)
    assert allowed.allowed is True

    # delete the store: recall and gates must fail
    store.close()
    for leftover in tmp_path.glob("memory.db*"):
        leftover.unlink()
    empty = MemoryStore(db)
    assert empty.recall_durable("agreement", "banner-job") is None
    blocked = evaluate_payment(empty, "banner-job", 60)
    assert blocked.allowed is False
    assert "no remembered agreement" in blocked.reason
    empty.close()


def test_gate_blocks_wrong_state(store: MemoryStore) -> None:
    agreement = Agreement(store, "job", amount=100)
    agreement.advance("agreed")
    result = evaluate_payment(store, "job", 100)
    assert result.allowed is False
    assert "delivered" in result.reason


def test_gate_blocks_amount_over_agreement(store: MemoryStore) -> None:
    agreement = Agreement(store, "job", amount=100)
    for state in ("agreed", "delegated", "delivered"):
        agreement.advance(state)
    result = evaluate_payment(store, "job", 150)
    assert result.allowed is False
    assert "exceeds" in result.reason
