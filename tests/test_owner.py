"""Owner profile tests: a curated summary, not a raw history dump."""
from __future__ import annotations

from core.memory.owner import owner_profile
from core.memory.store import MemoryStore


def test_profile_compiles_identity_and_preferences(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("identity", "name", {"value": "Ada"})
        store.remember_durable("preference", "style", {"value": "short answers"})

        result = owner_profile(store)

        assert "Ada" in result["profile"]
        assert "short answers" in result["profile"]
        assert result["identity"] == 1
        assert result["preferences"] == 1
    finally:
        store.close()


def test_profile_is_deterministic(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("identity", "name", {"value": "Ada"})

        first = owner_profile(store)
        second = owner_profile(store)

        assert first["profile"] == second["profile"]
    finally:
        store.close()


def test_accepted_proposals_appear_as_principles(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "preference",
            "proposal_keep_replies_brief",
            {"value": "keep replies brief", "accepted_at": "2026-09-01T00:00:00Z"},
            status="active",
        )

        result = owner_profile(store)

        assert "keep replies brief" in result["profile"]
        assert result["principles"] == 1
        assert result["preferences"] == 0
    finally:
        store.close()


def test_housekeeping_entities_stay_out_of_the_profile(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "identity", "dream_cursor", {"last_ts": "2026-09-06T00:00:00Z"}
        )
        store.remember_durable(
            "identity", "pulse_suppress", {"suppressed": ["x"]}
        )

        result = owner_profile(store)

        assert result["identity"] == 0
    finally:
        store.close()
