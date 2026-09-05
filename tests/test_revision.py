"""Revision tests: the full taint matrix, 18 cases."""
from __future__ import annotations

import pytest

from core.memory.agreement import Agreement
from core.memory.gate import evaluate_payment
from core.memory.links import link
from core.memory.revision import (
    blast_radius,
    is_suspect,
    reconsider,
    revise,
    suspect_reasons,
)
from core.memory.store import MemoryStore
from core.memory.tasks import Task


def _fact(store, name="rate", value="40"):
    store.remember_durable("preference", name, {"value": value})


def _delivered(store, name="fencing"):
    agreement = Agreement(store, name, amount=200)
    agreement.advance("agreed")
    agreement.advance("delegated")
    agreement.advance("delivered")
    return agreement


def test_direct_dependency_becomes_suspect(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        revise(store, "preference", "rate", "60", reason="corrected")
        assert is_suspect(store, "agreement", "fencing")
        assert "preference:rate" in suspect_reasons(store, "agreement", "fencing")
    finally:
        store.close()


def test_two_hop_dependency(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        Task(store, "sweep", objective="sweep after fencing")
        link(store, "preference", "rate", "agreement", "fencing")
        link(store, "agreement", "fencing", "task", "sweep")
        revise(store, "preference", "rate", "60")
        assert is_suspect(store, "agreement", "fencing")
        assert is_suspect(store, "task", "sweep")
    finally:
        store.close()


def test_unrelated_decision_stays_clean(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store, "rate")
        _fact(store, "unrelated", "always true")
        _delivered(store, "fencing")
        _delivered(store, "painting")
        link(store, "preference", "rate", "agreement", "fencing")
        link(store, "preference", "unrelated", "agreement", "painting")
        revise(store, "preference", "rate", "60")
        assert is_suspect(store, "agreement", "fencing")
        assert not is_suspect(store, "agreement", "painting")
    finally:
        store.close()


def test_blast_radius_counts_decision_events(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        store.record_event(
            evaluated={"question": "rate?", "sources": ["preference:rate"]},
            acted=["asked: rate?"],
        )
        radius = blast_radius(store, "preference:rate")
        assert radius["decisions"] == 1
    finally:
        store.close()


def test_blast_radius_counts_payment_events(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        store.record_event(
            evaluated={"agreement": "fencing", "amount": 200.0},
            acted=["payment sent: fencing 200 (dry run)"],
        )
        assert blast_radius(store, "preference:rate")["payments"] == 1
    finally:
        store.close()


def test_payment_blocked_while_suspect(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        revise(store, "preference", "rate", "60")
        result = evaluate_payment(store, "fencing", 200)
        assert result.allowed is False
        assert "suspect" in result.reason
        assert "reconsider" in result.reason
    finally:
        store.close()


def test_payment_allowed_after_valid_reconsideration(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        revise(store, "preference", "rate", "60")
        reconsider(store, "agreement", "fencing", "valid", reason="fixed price")
        assert evaluate_payment(store, "fencing", 200).allowed is True
    finally:
        store.close()


def test_invalid_reconsideration_keeps_gate_closed(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        revise(store, "preference", "rate", "60")
        reconsider(store, "agreement", "fencing", "invalid", reason="price void")
        result = evaluate_payment(store, "fencing", 200)
        assert result.allowed is False
        assert is_suspect(store, "agreement", "fencing")
    finally:
        store.close()


def test_multiple_source_entity_requires_each_review(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store, "rate")
        _fact(store, "scope", "fixed")
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        link(store, "preference", "scope", "agreement", "fencing")
        revise(store, "preference", "rate", "60")
        reconsider(store, "agreement", "fencing", "valid")
        # Only rate was revised, so the review cleared everything.
        assert not is_suspect(store, "agreement", "fencing")
        revise(store, "preference", "scope", "changed")
        # A new revision re-flags the entity, previous review does not cover it.
        assert is_suspect(store, "agreement", "fencing")
        reconsider(store, "agreement", "fencing", "valid")
        assert not is_suspect(store, "agreement", "fencing")
    finally:
        store.close()


def test_revision_after_reconsideration_reflags(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        revise(store, "preference", "rate", "60")
        reconsider(store, "agreement", "fencing", "valid")
        assert not is_suspect(store, "agreement", "fencing")
        revise(store, "preference", "rate", "70")
        assert is_suspect(store, "agreement", "fencing")
    finally:
        store.close()


def test_history_is_append_only(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        revise(store, "preference", "rate", "60")
        revise(store, "preference", "rate", "70")
        record = store.recall_durable("preference", "rate")
        history = record["body"]["history"]
        assert [entry["value"] for entry in history] == ["40", "60"]
        assert record["body"]["value"] == "70"
    finally:
        store.close()


def test_journal_remains_unchanged_by_revision(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        before = [e for e in store.timeline(limit=500)]
        revise(store, "preference", "rate", "60")
        after = store.timeline(limit=500)
        for old_event in before:
            assert old_event in after
    finally:
        store.close()


def test_revise_unknown_fact_raises(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        with pytest.raises(ValueError):
            revise(store, "preference", "ghost", "x")
    finally:
        store.close()


def test_revise_non_durable_category_raises(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        with pytest.raises(ValueError):
            revise(store, "note", "x", "y")
    finally:
        store.close()


def test_reconsider_unknown_entity_raises(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        with pytest.raises(ValueError):
            reconsider(store, "agreement", "ghost", "valid")
    finally:
        store.close()


def test_reconsider_bad_decision_raises(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered(store)
        with pytest.raises(ValueError):
            reconsider(store, "agreement", "fencing", "maybe")
    finally:
        store.close()


def test_reconsider_clean_entity_notes_noop(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered(store)
        result = reconsider(store, "agreement", "fencing", "valid")
        assert result["reopened"] is True
        assert "not suspect" in result["note"]
    finally:
        store.close()


def test_deletion_kills_taint_but_gate_closes_harder(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        revise(store, "preference", "rate", "60")
        store.forget_durable("preference", "rate")
        result = evaluate_payment(store, "fencing", 200)
        # Taint survives deletion of the fact: still blocked.
        assert result.allowed is False
    finally:
        store.close()


def test_repeated_revision_accumulates_taint(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _fact(store)
        _delivered(store)
        link(store, "preference", "rate", "agreement", "fencing")
        first = revise(store, "preference", "rate", "60")
        second = revise(store, "preference", "rate", "70")
        body = store.recall_durable("agreement", "fencing")["body"]
        ids = {entry["revision_id"] for entry in body["tainted_by"]}
        assert first["revision_id"] in ids
        assert second["revision_id"] in ids
    finally:
        store.close()
