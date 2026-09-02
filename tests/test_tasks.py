"""Task lifecycle tests: work that survives a restart."""
from __future__ import annotations

import pytest

from core.memory.store import MemoryStore
from core.memory.tasks import Task, TaskError, unfinished


def test_task_starts_queued_and_advances_one_step(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        task = Task(store, "book-flights", objective="book the trip")
        assert task.state == "queued"
        task.advance("working")
        assert task.state == "working"
    finally:
        store.close()


def test_task_survives_reopen(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        Task(store, "book-flights", objective="book the trip").advance("working")
        reopened = Task.open(store, "book-flights")
        assert reopened is not None
        assert reopened.state == "working"
        assert reopened.body["objective"] == "book the trip"
    finally:
        store.close()


def test_cannot_skip_states(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        task = Task(store, "book-flights")
        with pytest.raises(TaskError):
            task.advance("completed")
    finally:
        store.close()


def test_blocked_can_return_to_working(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        task = Task(store, "book-flights")
        task.advance("working")
        task.advance("blocked")
        task.advance("working")
        assert task.state == "working"
    finally:
        store.close()


def test_unfinished_lists_work_first_and_skips_completed(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        Task(store, "todo-a").advance("working")
        Task(store, "todo-b")  # queued
        done = Task(store, "done-a")
        done.advance("working")
        done.advance("blocked")
        done.advance("working")
        done.advance("completed")

        names = [task["name"] for task in unfinished(store)]
        assert names == ["todo-a", "todo-b"]
    finally:
        store.close()
