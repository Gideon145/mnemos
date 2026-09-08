"""Waitlist tests: real signups, dedup, live count, no fabrication."""
from __future__ import annotations

import pytest

from core.waitlist import add_email, count, entries, prune_test_entries


def test_add_email_stores_and_counts(tmp_path):
    path = tmp_path / "waitlist.json"
    assert add_email(path, "ada@example.com") == 1
    assert add_email(path, "bob@example.com") == 2
    assert count(path) == 2


def test_entries_are_newest_first(tmp_path):
    path = tmp_path / "waitlist.json"
    add_email(path, "ada@example.com")
    add_email(path, "bob@example.com")
    rows = entries(path)
    assert rows[0]["email"] == "bob@example.com"
    assert rows[1]["email"] == "ada@example.com"


def test_duplicate_email_does_not_double_count(tmp_path):
    path = tmp_path / "waitlist.json"
    add_email(path, "ada@example.com")
    assert add_email(path, "ADA@example.com") == 1
    assert count(path) == 1


def test_invalid_email_is_rejected(tmp_path):
    path = tmp_path / "waitlist.json"
    with pytest.raises(ValueError):
        add_email(path, "not-an-email")
    assert count(path) == 0


def test_missing_file_counts_zero(tmp_path):
    assert count(tmp_path / "nope.json") == 0


def test_prune_removes_only_test_entries(tmp_path):
    path = tmp_path / "waitlist.json"
    add_email(path, "judge-test@example.com")
    add_email(path, "real@domain.com")

    removed = prune_test_entries(path)

    assert removed == 1
    assert [row["email"] for row in entries(path)] == ["real@domain.com"]


def test_prune_is_idempotent(tmp_path):
    path = tmp_path / "waitlist.json"
    add_email(path, "real@domain.com")

    assert prune_test_entries(path) == 0
    assert count(path) == 1
