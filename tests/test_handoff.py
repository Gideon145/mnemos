"""Handoff tests: one pack carries memory between two agents."""
from __future__ import annotations

from core.agent import RecallEngine
from core.memory.handoff import handoff
from core.memory.keepsake import import_keepsake
from core.memory.store import MemoryStore


def test_handoff_exports_and_journals(tmp_path):
    store = MemoryStore(tmp_path / "a.db")
    try:
        store.remember_durable("preference", "style", {"value": "short"})
        pack = tmp_path / "hand.mne"
        summary = handoff(store, pack, recipient="agent-b")
        assert pack.exists()
        assert summary["import_command"].endswith("hand.mne")
        assert any(
            "keepsake handed to agent-b" in line
            for event in store.timeline(limit=5)
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def test_recipient_recalls_after_import(tmp_path):
    agent_a = MemoryStore(tmp_path / "a.db")
    agent_b = MemoryStore(tmp_path / "b.db")
    try:
        agent_a.remember_durable("preference", "style", {"value": "short"})
        agent_a.remember_durable("identity", "user", {"value": "vergio"})
        pack = tmp_path / "hand.mne"
        handoff(agent_a, pack, recipient="agent-b")

        import_keepsake(agent_b, pack)
        answer = RecallEngine(agent_b).ask("my name and my answer style")
        assert answer.found_anything is True
        assert "style" in answer.answer
        assert "vergio" in answer.answer
    finally:
        agent_a.close()
        agent_b.close()


def _acted_lines(event):
    acted = event.get("acted")
    if isinstance(acted, str):
        return [acted]
    return list(acted or [])
