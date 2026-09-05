"""Keepsakes: a fresh machine gets the agent back."""
from __future__ import annotations

import json

import pytest

from core.agent import RecallEngine
from core.memory.agreement import Agreement
from core.memory.gate import evaluate_payment
from core.memory.keepsake import export_keepsake, import_keepsake
from core.memory.store import MemoryStore


def _populated(store: MemoryStore) -> None:
    store.remember_durable("preference", "rate", {"value": "40"})
    agreement = Agreement(store, "fencing", amount=200)
    agreement.advance("agreed")
    agreement.advance("delegated")
    agreement.advance("delivered")
    store.record_event(acted=["taught the agent"])


def test_fresh_machine_recalls_and_gate_holds(tmp_path):
    original = MemoryStore(tmp_path / "original.db")
    try:
        _populated(original)
        export_keepsake(original, tmp_path / "memory.mne")
    finally:
        original.close()

    fresh = MemoryStore(tmp_path / "fresh.db")
    try:
        summary = import_keepsake(fresh, tmp_path / "memory.mne")
        assert summary["entities_imported"] == 2  # preference + agreement
        answer = RecallEngine(fresh).ask("what is the contractor rate?")
        assert "40" in answer.answer
        result = evaluate_payment(fresh, "fencing", 200)
        assert result.allowed is True
    finally:
        fresh.close()


def test_tampered_pack_is_refused(tmp_path):
    original = MemoryStore(tmp_path / "original.db")
    try:
        _populated(original)
        export_keepsake(original, tmp_path / "memory.mne")
    finally:
        original.close()

    pack_path = tmp_path / "memory.mne"
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    pack["payload"]["entities"][0]["body"]["value"] = "999999"
    pack_path.write_text(json.dumps(pack), encoding="utf-8")

    fresh = MemoryStore(tmp_path / "fresh.db")
    try:
        with pytest.raises(ValueError, match="digest"):
            import_keepsake(fresh, pack_path)
    finally:
        fresh.close()


def test_import_never_overwrites_newer_local(tmp_path):
    original = MemoryStore(tmp_path / "original.db")
    try:
        original.remember_durable("preference", "rate", {"value": "40"})
        export_keepsake(original, tmp_path / "memory.mne")
    finally:
        original.close()

    fresh = MemoryStore(tmp_path / "fresh.db")
    try:
        fresh.remember_durable("preference", "rate", {"value": "60"})
        summary = import_keepsake(fresh, tmp_path / "memory.mne")
        assert summary["entities_imported"] == 0
        body = fresh.recall_durable("preference", "rate")["body"]
        assert body["value"] == "60"
    finally:
        fresh.close()


def test_journal_restored_for_replay(tmp_path):
    original = MemoryStore(tmp_path / "original.db")
    try:
        _populated(original)
        export_keepsake(original, tmp_path / "memory.mne")
    finally:
        original.close()

    fresh = MemoryStore(tmp_path / "fresh.db")
    try:
        import_keepsake(fresh, tmp_path / "memory.mne")
        events = fresh.timeline(limit=100)
        acted = [str(e.get("acted")) for e in events]
        collapsed = " ".join(acted).replace(" ", "")
        assert "taught" in collapsed
    finally:
        fresh.close()
