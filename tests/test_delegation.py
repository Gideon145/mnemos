"""Delegation tests: handing work to another agent, remembered."""
from __future__ import annotations

import pytest

from core.memory.agreement import Agreement, AgreementError
from core.memory.store import MemoryStore


def _agree(store):
    agreement = Agreement(store, "contractor", amount=160, counterparty="alice")
    agreement.advance("agreed")
    return agreement


def test_delegation_writes_agent_and_task_into_memory(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        agreement = _agree(store)
        agreement.note_delegation("agent-42", "fix the fence")
        agreement.advance("delegated")

        record = store.recall_durable("agreement", "contractor")
        body = record["body"]
        assert body["delegated_to"] == "agent-42"
        assert body["task"] == "fix the fence"
        assert record.get("status") == "delegated"
    finally:
        store.close()


def test_delegation_is_journaled(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        agreement = _agree(store)
        agreement.note_delegation("agent-42", "fix the fence")
        timeline = store.timeline(limit=5)
        assert any(
            "delegated contractor to agent-42" in line
            for event in timeline
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def test_cannot_skip_to_delegated_without_agreement(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        agreement = Agreement(store, "solo", amount=10)
        with pytest.raises(AgreementError):
            agreement.advance("delegated")
    finally:
        store.close()


def _acted_lines(event):
    acted = event.get("acted")
    if isinstance(acted, str):
        return [acted]
    return list(acted or [])
