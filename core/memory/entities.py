"""Entities: deterministic extraction and entity-boosted recall.

Mnemos does not run a knowledge graph. It extracts entities
deterministically from remembered facts (proper nouns and email
addresses), stores them on the fact's body so they travel with
keepsakes, and boosts recall for facts that share entities with the
question. Zero model calls, zero embeddings.

The index is a plain aggregation over durable entities: entity ->
facts that mention it.
"""
from __future__ import annotations

import re
from typing import Any

from .store import DURABLE_CATEGORIES, MemoryStore

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Capitalized word runs not at the start of a sentence: Alice, Base,
# Mnemos, Nigeria. Deliberately simple and deterministic.
_PROPER = re.compile(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+){0,3}\b")

_SKIP = {"I", "I'm", "A", "An", "The"}


def extract_entities(text: str) -> list[str]:
    """Deterministic proper-noun and email extraction."""
    found: list[str] = []
    for match in _EMAIL.finditer(text):
        found.append(match.group(0))
    for match in _PROPER.finditer(text):
        span_start = match.start()
        # Drop capitalized words that open a sentence: they are not
        # evidence of an entity.
        prefix = text[:span_start].rstrip()
        if not prefix or prefix.endswith((".", "!", "?")):
            continue
        phrase = match.group(0)
        if phrase in _SKIP:
            continue
        found.append(phrase)
    deduped: list[str] = []
    for item in found:
        if item not in deduped:
            deduped.append(item)
    return deduped


def annotate(store: MemoryStore, category: str, name: str, text: str) -> list[str]:
    """Extract entities from text and store them on the fact's body."""
    record = store.recall_durable(category, name)
    if record is None:
        return []
    entities = extract_entities(text)
    if not entities:
        return []
    body = dict(record.get("body") or {})
    existing = list(body.get("entities") or [])
    for entity in entities:
        if entity not in existing:
            existing.append(entity)
    body["entities"] = existing
    store.remember_durable(category, name, body, status=record.get("status"))
    return entities


def index(store: MemoryStore) -> dict[str, list[str]]:
    """Entity -> facts that mention it, over every durable category."""
    aggregated: dict[str, list[str]] = {}
    for category in DURABLE_CATEGORIES:
        for record in store.list_durable(category):
            name = str(record.get("name"))
            for entity in (record.get("body") or {}).get("entities") or []:
                aggregated.setdefault(str(entity), []).append(f"{category}:{name}")
    return aggregated


def matched_entities(record: dict[str, Any], tokens: set[str]) -> int:
    """Count entity phrases on a record that overlap question tokens."""
    entities = (record.get("body") or {}).get("entities") or []
    hits = 0
    for entity in entities:
        entity_tokens = {token.lower() for token in entity.split() if len(token) > 2}
        if entity_tokens & tokens:
            hits += 1
    return hits
