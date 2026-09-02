"""Recall engine: answer questions strictly from what memory holds.

The engine has exactly two jobs:

1. Find durable facts (preferences, agreements, identity) relevant to a
   question, using the store's FTS search first and a deterministic
   lexical fallback second.
2. Say so, plainly, when there is nothing to find.

An agent that makes up answers when its memory is empty is not an agent
with memory. It is an agent that pretends. The empty-store answer is a
feature, and the deletion test proves it is load-bearing.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ..memory.store import DURABLE_CATEGORIES, MemoryStore

_WORD = re.compile(r"[a-zA-Z0-9]{3,}")

# Question tokens that make identity records relevant regardless of
# lexical overlap: "who am i", "my name", "your name", and friends.
_IDENTITY_TRIGGERS = {"who", "you", "your", "name", "identit"}


@dataclass(frozen=True)
class RecallAnswer:
    """The result of asking the agent a question."""

    question: str
    answer: str
    found_anything: bool = False
    confidence: float = 0.0
    sources: tuple[str, ...] = field(default_factory=tuple)


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _tokenize(text: str) -> set[str]:
    return {_stem(match.group(0).lower()) for match in _WORD.finditer(text)}


def _entity_text(record: dict[str, Any]) -> str:
    """Flatten an entity record into searchable text."""
    parts = [
        str(record.get("category", "")),
        str(record.get("name", "")),
        str(record.get("status", "")),
    ]
    body = record.get("body")
    if isinstance(body, dict):
        parts.append(json.dumps(body, sort_keys=True, default=str))
    else:
        parts.append(str(body))
    return " ".join(parts)


def _describe(record: dict[str, Any]) -> str:
    category = record.get("category", "?")
    name = record.get("name", "?")
    body = record.get("body")
    status = record.get("status")
    if isinstance(body, dict) and body:
        body_text = "; ".join(f"{key}={value}" for key, value in body.items())
    else:
        body_text = str(body) if body else ""
    body_text = " ".join(body_text.split())
    if len(body_text) > 140:
        body_text = body_text[:137].rstrip() + "..."
    suffix = f" ({status})" if status else ""
    return f"{category} {name}{suffix}: {body_text}".strip()


def _score_overlap(tokens: set[str], text: str) -> int:
    return len(tokens & _tokenize(text))


class RecallEngine:
    """Consult memory and answer with the evidence attached."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def ask(self, question: str) -> RecallAnswer:
        tokens = _tokenize(question)
        matches: list[tuple[int, dict[str, Any]]] = []

        # Pass 1: the store's own full-text search over entities.
        seen: set[tuple[str, str]] = set()
        for record in self._store.search(question):
            key = (str(record.get("category")), str(record.get("name")))
            if key in seen:
                continue
            seen.add(key)
            matches.append((_score_overlap(tokens, _entity_text(record)), record))

        # Pass 2: lexical fallback, so plain wording still finds facts
        # the FTS index tokenizes differently.
        for category in DURABLE_CATEGORIES:
            for record in self._store.list_durable(category):
                key = (str(record.get("category")), str(record.get("name")))
                if key in seen:
                    continue
                score = _score_overlap(tokens, _entity_text(record))
                if score:
                    seen.add(key)
                    matches.append((score, record))

        # Pass 3: questions about the user always surface identity.
        if tokens & _IDENTITY_TRIGGERS:
            for record in self._store.list_durable("identity"):
                key = (str(record.get("category")), str(record.get("name")))
                if key in seen:
                    continue
                seen.add(key)
                matches.append((1, record))

        if not matches:
            return RecallAnswer(
                question=question,
                answer="I don't remember anything about that. "
                "Tell me, and I will keep it.",
                found_anything=False,
                confidence=0.0,
            )

        matches.sort(key=lambda pair: (-pair[0], _entity_text(pair[1])))
        lines = [f"- {_describe(record)}" for _, record in matches]
        answer = "\n".join(lines)
        confidence = min(0.95, 0.4 + 0.15 * len(matches))
        return RecallAnswer(
            question=question,
            answer=answer,
            found_anything=True,
            confidence=round(confidence, 2),
            sources=tuple(f"{r.get('category')}:{r.get('name')}" for _, r in matches),
        )
