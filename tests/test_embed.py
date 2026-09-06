"""Embedding tests: optional hybrid recall stays deterministic and behind a flag."""
from __future__ import annotations

from core.memory.embed import HashEmbedder, _cosine, embed_store, hybrid_rank
from core.memory.store import MemoryStore


def _remember(store, name, value):
    store.remember_durable("preference", name, {"value": value})


def test_hash_embedder_is_deterministic():
    embedder = HashEmbedder()
    first = embedder.embed(["same text"])[0]
    second = embedder.embed(["same text"])[0]
    assert first == second
    assert len(first) == HashEmbedder.DIM


def test_embed_store_writes_vectors_onto_facts(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _remember(store, "rate", "contractor rate is 40")
        _remember(store, "answer_style", "short direct answers")

        summary = embed_store(store, HashEmbedder())

        assert summary["embedded"] == 2
        record = store.recall_durable("preference", "rate")
        assert len(record["body"]["embedding"]) == HashEmbedder.DIM
    finally:
        store.close()


def test_hybrid_rank_fuses_fts_with_cosine(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _remember(store, "rate", "contractor rate is 40 per hour")
        _remember(store, "answer_style", "short direct answers")
        embed_store(store, HashEmbedder())

        ranked = hybrid_rank(store, "what is the contractor rate", HashEmbedder())

        assert ranked, "hybrid search should surface the rate fact"
        top = ranked[0]
        assert "rate" in str(top.get("name")) or "contractor" in str(
            top.get("body", {}).get("value")
        )
    finally:
        store.close()


def test_cosine_is_zero_for_mismatched_lengths():
    assert _cosine([1.0], []) == 0.0
