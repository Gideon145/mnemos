"""Dream tests: consolidation proposals are review-gated and cursor-safe."""
from __future__ import annotations

from core.memory.dream import apply, dream, pending, reject
from core.memory.store import MemoryStore


def test_repeated_actions_become_review_gated_proposals(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        for _ in range(3):
            store.record_event(acted=["asked for a status report"])

        report = dream(store)

        assert report["events_scanned"] == 3
        assert report["kinds"]["repeat"] == 1
        name = report["proposals"][0]
        record = store.recall_durable("preference", name)
        assert record is not None
        assert record.get("status") == "proposed"
        assert "status report" in record["body"]["value"]
    finally:
        store.close()


def test_missed_questions_become_proposals(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(
            evaluated={"question": "what is my shoe size", "found": False},
            acted=["asked: what is my shoe size"],
        )

        report = dream(store)

        assert report["kinds"]["miss"] == 1
    finally:
        store.close()


def test_refusals_become_proposals(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.record_event(
            evaluated={"reason": "no delivered agreement"},
            acted=["payment refused"],
        )

        report = dream(store)

        assert report["kinds"]["refusal"] == 1
    finally:
        store.close()


def test_second_dream_skips_its_own_output(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        for _ in range(2):
            store.record_event(acted=["asked for a status report"])

        first = dream(store)
        second = dream(store)

        assert len(first["proposals"]) == 1
        assert second["events_scanned"] == 0
        assert second["proposals"] == []
    finally:
        store.close()


def test_apply_promotes_to_lesson_and_archives_proposal(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        for _ in range(2):
            store.record_event(acted=["asked for a status report"])
        name = dream(store)["proposals"][0]

        lesson = apply(store, name)

        assert lesson is not None
        assert lesson.get("body", {}).get("value") == "asked for a status report"
        assert pending(store) == []
    finally:
        store.close()


def test_reject_archives_proposal(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        for _ in range(2):
            store.record_event(acted=["asked for a status report"])
        name = dream(store)["proposals"][0]

        assert reject(store, name) is True
        assert pending(store) == []
    finally:
        store.close()
