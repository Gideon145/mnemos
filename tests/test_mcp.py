"""MCP tools: every tool speaks to the same store the CLI uses."""
from __future__ import annotations

import os

import pytest

from core import mcp
from core.memory.store import MemoryStore


def _scoped_store():
    return MemoryStore(os.environ[mcp.DB_ENV])


@pytest.fixture(autouse=True)
def scoped_db(tmp_path, monkeypatch):
    monkeypatch.setenv(mcp.DB_ENV, str(tmp_path / "memory.db"))
    yield


def test_remember_then_ask_roundtrip():
    out = mcp.remember("contractor rate is 40", category="preference")
    assert out.category == "preference"
    answer = mcp.ask("what is the contractor rate?")
    assert "40" in answer.answer
    assert answer.found is True


def test_ask_with_empty_memory_is_honest():
    answer = mcp.ask("what is the contractor rate?")
    assert answer.answer  # says it does not know rather than fabricating
    assert answer.found is False


def test_learn_lesson_surfaces_severity():
    out = mcp.learn_lesson("prepaying contractors burns money", severity="high")
    assert out.severity == "high"


def test_task_and_resume_roundtrip():
    mcp.task("sweep the floor")
    mcp.task("paint the fence")
    out = mcp.resume()
    names = [item["name"] for item in out.unfinished]
    assert "sweep_the_floor" in names
    assert "paint_the_fence" in names


def test_resume_with_nothing_reports_empty():
    assert mcp.resume().unfinished == []


def test_recap_and_replay_roundtrip():
    mcp.remember("ship on fridays", category="preference")
    assert mcp.recap_day().text
    replay_result = mcp.replay("fridays")
    assert replay_result.text
    assert replay_result.subject == "fridays"


def test_revise_marks_dependents_suspect():
    store = _scoped_store()
    try:
        store.remember_durable("preference", "rate", {"value": "40"})
        agreement = store.remember_durable(
            "agreement", "fencing", {"value": "fence job", "linked": ["preference:rate"]}
        )
    finally:
        store.close()

    out = mcp.revise("preference", "rate", "60", reason="corrected")
    assert out.old == "40" and out.new == "60"
    assert "agreement:fencing" in out.newly_suspect
    assert out.revision_id

    suspect_list = mcp.suspect()
    assert "agreement fencing" in suspect_list.suspect


def test_reconsider_reopens_and_clears():
    store = _scoped_store()
    try:
        store.remember_durable("preference", "rate", {"value": "40"})
        store.remember_durable(
            "agreement", "fencing", {"value": "fence job", "linked": ["preference:rate"]}
        )
    finally:
        store.close()

    mcp.revise("preference", "rate", "60")
    out = mcp.reconsider("agreement", "fencing", "valid", reason="fixed price")
    assert out.gate_reopened is True
    assert mcp.suspect().suspect == []


def test_reconsider_invalid_keeps_suspect():
    store = _scoped_store()
    try:
        store.remember_durable("preference", "rate", {"value": "40"})
        store.remember_durable(
            "agreement", "fencing", {"value": "fence job", "linked": ["preference:rate"]}
        )
    finally:
        store.close()

    mcp.revise("preference", "rate", "60")
    out = mcp.reconsider("agreement", "fencing", "invalid")
    assert out.gate_reopened is False
    assert "agreement fencing" in mcp.suspect().suspect


def test_blast_reports_radius():
    store = _scoped_store()
    try:
        store.remember_durable("preference", "rate", {"value": "40"})
        store.remember_durable(
            "agreement", "fencing", {"value": "fence job", "linked": ["preference:rate"]}
        )
    finally:
        store.close()

    out = mcp.blast("preference", "rate")
    assert out.agreements == ["fencing"]
