"""Rewind tests: memory state at a past moment reconstructs from history."""
from __future__ import annotations

from core.memory.rewind import rewind
from core.memory.revision import revise
from core.memory.store import MemoryStore

FUTURE = "2999-01-01T00:00:00+00:00"


def _remember(store, category, name, value):
    store.remember_durable(category, name, {"value": value})
    store.record_event(acted=[f"remembered {category} {name}"])


def test_rewind_at_future_shows_everything_unchanged(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _remember(store, "preference", "rate", "40 per hour")

        result = rewind(store, FUTURE)

        assert result["entities"][0]["value"] == "40 per hour"
        assert result["changed_count"] == 0
    finally:
        store.close()


def test_rewind_reconstructs_the_value_before_a_revision(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _remember(store, "preference", "rate", "40 per hour")
        revise(store, "preference", "rate", "60 per hour", reason="raised")

        # Anchor just after the creation event: strictly before the
        # revision, regardless of how fast the two ran.
        creation_ts = next(
            event["ts"]
            for event in store.timeline(limit=100)
            if "remembered"
            in " ".join(
                item if isinstance(item, str) else str(item)
                for item in (event.get("acted") or [])
            )
        )
        just_before = creation_ts + "1"

        result = rewind(store, just_before)

        entry = next(
            item for item in result["entities"] if item["name"] == "rate"
        )
        assert entry["value"] == "40 per hour"
        change = next(item for item in result["changed"] if item["name"] == "rate")
        assert change["at"] == "40 per hour"
        assert change["now"] == "60 per hour"
    finally:
        store.close()


def test_rewind_reports_nothing_unknown_at_a_past_moment(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _remember(store, "preference", "rate", "40 per hour")

        result = rewind(store, "1990-01-01T00:00:00+00:00")

        assert result["entities"] == []
        assert result["changed_count"] == 0
    finally:
        store.close()
