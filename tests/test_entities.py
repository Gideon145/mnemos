"""Entity tests: deterministic extraction, annotation, index, recall boost."""
from __future__ import annotations

from core.agent.recall import RecallEngine
from core.memory.entities import annotate, extract_entities, index, matched_entities
from core.memory.store import MemoryStore


def test_proper_nouns_and_emails_are_extracted():
    found = extract_entities("Alice works with Bob at Base and emails a@b.com")
    assert "Bob" in found
    assert "Base" in found
    assert "a@b.com" in found


def test_sentence_opener_is_not_an_entity():
    found = extract_entities("Alice likes coffee")
    assert "Alice" not in found


def test_annotate_stores_entities_on_the_fact(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("preference", "partner", {"value": "partner is Alice"})
        found = annotate(store, "preference", "partner", "partner is Alice")

        assert "Alice" in found
        record = store.recall_durable("preference", "partner")
        assert "Alice" in record["body"]["entities"]
    finally:
        store.close()


def test_index_aggregates_entity_to_facts(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("preference", "one", {"value": "works with Alice"})
        annotate(store, "preference", "one", "works with Alice")
        store.remember_durable("preference", "two", {"value": "pays Alice"})
        annotate(store, "preference", "two", "pays Alice")

        aggregated = index(store)

        assert "preference:one" in aggregated["Alice"]
        assert "preference:two" in aggregated["Alice"]
    finally:
        store.close()


def test_recall_boosts_facts_sharing_an_entity(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("preference", "one", {"value": "partner is Alice"})
        annotate(store, "preference", "one", "partner is Alice")
        store.remember_durable("preference", "two", {"value": "unrelated"})

        answer = RecallEngine(store).ask("what do I know about Alice")

        assert answer.found_anything is True
        assert "partner" in answer.answer.lower()
    finally:
        store.close()


def test_matched_entities_counts_overlaps():
    record = {"body": {"entities": ["Alice", "Base"]}}
    assert matched_entities(record, {"alice", "shoe"}) == 1
    assert matched_entities(record, {"bob"}) == 0
