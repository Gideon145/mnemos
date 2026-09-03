"""Link tests: breadcrumbs between durable entities."""
from __future__ import annotations

import pytest

from core.memory.agreement import Agreement
from core.memory.lessons import learn
from core.memory.links import link, links_of
from core.memory.store import MemoryStore


def test_link_is_bidirectional(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("preference", "style", {"value": "short"})
        learn(store, "contractor vanished after prepayment")

        link(store, "preference", "style", "lesson", "contractor_vanished_after_prepayment")

        assert "lesson:contractor_vanished_after_prepayment" in links_of(store, "preference", "style")
        assert "preference:style" in links_of(store, "lesson", "contractor_vanished_after_prepayment")
    finally:
        store.close()


def test_link_keeps_status_and_body(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        agreement = Agreement(store, "contractor", amount=160)
        agreement.advance("agreed")
        store.remember_durable("identity", "self", {"value": "me"})
        link(store, "agreement", "contractor", "identity", "self")

        reopened = Agreement.open(store, "contractor")
        assert reopened.state == "agreed"
        assert "identity:self" in reopened.body["linked"]
    finally:
        store.close()


def test_link_unknown_entity_raises(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("preference", "style", {"value": "short"})
        with pytest.raises(ValueError):
            link(store, "preference", "style", "task", "ghost")
    finally:
        store.close()


def test_link_is_journaled(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        store.remember_durable("preference", "style", {"value": "short"})
        learn(store, "contractor vanished after prepayment")
        link(store, "preference", "style", "lesson", "contractor_vanished_after_prepayment")
        timeline = store.timeline(limit=5)
        assert any(
            "linked preference:style <-> lesson:contractor_vanished_after_prepayment" in line
            for event in timeline
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def _acted_lines(event):
    acted = event.get("acted")
    if isinstance(acted, str):
        return [acted]
    return list(acted or [])
