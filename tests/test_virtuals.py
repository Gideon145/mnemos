"""Virtuals registration write-back and dispatch tests."""
from __future__ import annotations

import pytest

from core.integrations.virtuals import (
    dispatch_to_virtuals,
    register_with_virtuals,
)
from core.memory.store import MemoryStore


@pytest.fixture(autouse=True)
def clear_virtuals_env(monkeypatch):
    """The live env vars must never leak into tests."""
    for name in ("VIRTUALS_API_KEY", "VIRTUALS_COMPUTE_URL", "VIRTUALS_MODEL"):
        monkeypatch.delenv(name, raising=False)
    yield


class FakeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.tasks = []

    def create_agent(self, name, description, goal):
        return f"agent-{name}-123"

    def set_worker_task(self, agent_id, task):
        self.tasks.append((agent_id, task))
        return {"task_id": "t1", "agent_id": agent_id}


def test_dry_run_writes_honest_identity(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = register_with_virtuals(store, name="mnemos")
        assert result.registered is False
        record = store.recall_durable("identity", "virtuals_agent")
        assert record is not None
        assert record["body"]["registered"] is False
        assert "dry run" in record["body"]["note"]
    finally:
        store.close()


def test_live_registration_stores_agent_id(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = register_with_virtuals(
            store,
            name="mnemos",
            api_key="fake-key",
            live=True,
            client_factory=FakeClient,
        )
        assert result.registered is True
        assert result.agent_id == "agent-mnemos-123"
        record = store.recall_durable("identity", "virtuals_agent")
        assert record["body"]["agent_id"] == "agent-mnemos-123"
    finally:
        store.close()


def test_live_registration_without_key_raises(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        with pytest.raises(RuntimeError):
            register_with_virtuals(store, live=True)
    finally:
        store.close()


def test_dispatch_uses_remembered_agent_id(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        register_with_virtuals(
            store, api_key="fake-key", live=True, client_factory=FakeClient
        )
        result = dispatch_to_virtuals(
            store, "fix the fence", api_key="fake-key", client_factory=FakeClient
        )
        assert result["task_id"] == "t1"
        assert any(
            "dispatched to virtuals agent agent-mnemos-123" in line
            for event in store.timeline(limit=5)
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def test_console_agent_id_is_recorded(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        result = register_with_virtuals(store, agent_id="console-agent-9")
        assert result.registered is True
        assert result.agent_id == "console-agent-9"
        record = store.recall_durable("identity", "virtuals_agent")
        assert record["body"]["registered"] is True
    finally:
        store.close()


def test_acp_dispatch_calls_the_compute_endpoint(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        register_with_virtuals(store, agent_id="console-agent-9")
        sent = {}

        def fake_transport(endpoint, api_key, payload):
            sent["endpoint"] = endpoint
            sent["payload"] = payload
            return {"choices": [{"message": {"content": "done"}}]}

        result = dispatch_to_virtuals(
            store,
            "fix the fence",
            api_key="fake-key",
            endpoint="https://compute.example",
            transport=fake_transport,
        )
        assert sent["endpoint"] == "https://compute.example"
        assert "fix the fence" in sent["payload"]["messages"][0]["content"]
        assert result["response"]["choices"][0]["message"]["content"] == "done"
    finally:
        store.close()


def test_acp_dispatch_journals(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        register_with_virtuals(store, agent_id="console-agent-9")

        def fake_transport(endpoint, api_key, payload):
            return {"choices": []}

        dispatch_to_virtuals(
            store,
            "fix the fence",
            api_key="fake-key",
            endpoint="https://compute.example",
            transport=fake_transport,
        )
        assert any(
            "dispatched to virtuals agent console-agent-9" in line
            for event in store.timeline(limit=5)
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def test_dispatch_without_registration_raises(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        with pytest.raises(RuntimeError):
            dispatch_to_virtuals(store, "anything")
    finally:
        store.close()


def test_registration_is_journaled(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        register_with_virtuals(store)
        timeline = store.timeline(limit=5)
        assert any(
            "virtuals registration attempt" in line
            for event in timeline
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def _acted_lines(event):
    acted = event.get("acted")
    if isinstance(acted, str):
        return [acted]
    return list(acted or [])
