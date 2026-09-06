"""Embeddings: optional hybrid recall behind a flag.

Off by default. Mnemos stays zero-embedding, deterministic FTS: the
token-free recall story is the default, not an add-on. When
MNEMOS_EMBED_BASE_URL, MNEMOS_EMBED_API_KEY, and MNEMOS_EMBED_MODEL
are all set, facts get vectors and hybrid recall fuses cosine
similarity with FTS scores.

The transport is stdlib urllib against any OpenAI-compatible
`/embeddings` endpoint. No new dependency.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.request
from typing import Any, Protocol

from .store import DURABLE_CATEGORIES, MemoryStore


def enabled() -> bool:
    return all(
        os.environ.get(key)
        for key in ("MNEMOS_EMBED_BASE_URL", "MNEMOS_EMBED_API_KEY", "MNEMOS_EMBED_MODEL")
    )


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HTTPEmbedder:
    """OpenAI-compatible embeddings endpoint over stdlib urllib."""

    name = "http"

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        base = base_url.rstrip("/")
        self.url = (
            base + "/embeddings"
            if base.endswith("/v1")
            else base + "/v1/embeddings"
        )
        self.api_key = api_key
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        request = urllib.request.Request(
            self.url,
            data=json.dumps({"model": self.model, "input": texts}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        data = sorted(payload.get("data", []), key=lambda item: item.get("index", 0))
        return [list(item.get("embedding") or []) for item in data]


class HashEmbedder:
    """Deterministic hashed vectors. Tests and offline demos only."""

    name = "hash"
    DIM = 32

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.DIM
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = digest[0] % self.DIM
                sign = 1.0 if digest[1] % 2 == 0 else -1.0
                vector[index] += sign
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (norm_a * norm_b)


def embed_store(store: MemoryStore, embedder: Embedder) -> dict[str, Any]:
    """Write a vector onto every durable entity that has a value."""
    records: list[dict[str, Any]] = []
    texts: list[str] = []
    for category in DURABLE_CATEGORIES:
        for record in store.list_durable(category):
            body = record.get("body") or {}
            value = body.get("value")
            if not value:
                continue
            records.append(record)
            texts.append(f"{category} {record.get('name')}: {value}")

    embedded = 0
    if texts:
        vectors = embedder.embed(texts)
        for record, vector in zip(records, vectors):
            body = dict(record.get("body") or {})
            body["embedding"] = vector
            store.remember_durable(
                record.get("category"),
                record.get("name"),
                body,
                status=record.get("status"),
            )
            embedded += 1
    store.record_event(
        evaluated={"embedder": embedder.name, "embedded": embedded},
        acted=[f"embedded {embedded} entities with {embedder.name}"],
    )
    return {"embedder": embedder.name, "embedded": embedded}


def hybrid_rank(
    store: MemoryStore,
    question: str,
    embedder: Embedder,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Fuse FTS results with cosine similarity to entity vectors.

    When FTS returns nothing (uncommon wording), rank every durable
    entity by cosine alone so hybrid recall never comes back empty
    while memory holds anything relevant.
    """
    query_vector = embedder.embed([question])[0]
    fts_results = store.search(question, limit=limit)

    if not fts_results:
        records: list[dict[str, Any]] = []
        for category in DURABLE_CATEGORIES:
            records.extend(store.list_durable(category))
        fts_results = records

    ranked: list[dict[str, Any]] = []
    for position, record in enumerate(fts_results):
        vector = (record.get("body") or {}).get("embedding") or []
        cosine = _cosine(query_vector, vector)
        fts = 1.0 / (1.0 + position)
        ranked.append({**record, "_hybrid_score": 0.5 * fts + 0.5 * cosine})
    ranked.sort(key=lambda record: record["_hybrid_score"], reverse=True)
    return ranked
