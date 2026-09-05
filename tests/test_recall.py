"""Recall engine tests, including the empty-memory honesty case."""
from __future__ import annotations

from core.agent import RecallEngine
from core.memory.store import MemoryStore


def test_empty_store_says_it_does_not_remember(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        engine = RecallEngine(store)
        answer = engine.ask("how do I like answers?")
        assert answer.found_anything is False
        assert answer.confidence == 0.0
        assert "don't remember" in answer.answer
    finally:
        store.close()


def test_ask_finds_remembered_preference(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "preference",
            "answer_style",
            {"value": "I like short direct answers"},
        )
        engine = RecallEngine(store)
        answer = engine.ask("how do I like answers?")
        assert answer.found_anything is True
        assert answer.confidence > 0.0
        assert "answer_style" in answer.answer
        assert "short direct answers" in answer.answer
    finally:
        store.close()


def test_ask_surfaces_agreement_state(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "agreement",
            "contractor",
            {"amount": 40, "counterparty": "alice"},
            status="delivered",
        )
        engine = RecallEngine(store)
        answer = engine.ask("contractor rate")
        assert answer.found_anything is True
        assert "contractor" in answer.answer
        assert "delivered" in answer.answer
    finally:
        store.close()


def test_ask_does_not_hallucinate_unrelated_facts(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "preference",
            "answer_style",
            {"value": "I like short direct answers"},
        )
        engine = RecallEngine(store)
        answer = engine.ask("where did I park the car?")
        assert answer.found_anything is False
        assert "short direct answers" not in answer.answer
    finally:
        store.close()


def test_sources_are_qualified_entity_keys(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "identity", "user_name", {"value": "vergio"}
        )
        engine = RecallEngine(store)
        answer = engine.ask("what is my name")
        assert "identity:user_name" in answer.sources
    finally:
        store.close()


def test_what_do_you_know_about_me_lists_everything(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "preference",
            "answer_style",
            {"value": "I like short direct answers"},
        )
        store.remember_durable(
            "preference",
            "contractor_rate_is_40_per_hour",
            {"value": "my contractor rate is 40 per hour"},
        )
        engine = RecallEngine(store)
        answer = engine.ask("what do you know about me?")
        assert answer.found_anything is True
        assert "short direct answers" in answer.answer
        assert "contractor rate" in answer.answer
        assert "preference:answer_style" in answer.sources
    finally:
        store.close()


def test_generic_you_question_does_not_hijack_identity(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable(
            "identity", "user_name", {"value": "vergio"}
        )
        engine = RecallEngine(store)
        answer = engine.ask("do you have any tips for watering plants?")
        assert answer.found_anything is False
        assert "identity:user_name" not in answer.sources
    finally:
        store.close()
