"""Task entities: work that survives a restart.

A task is durable memory, not a process variable. It lives in the same
store as preferences and agreements, so a fresh Mnemos on a fresh
machine can resume unfinished work exactly where it stopped.

States move forward one step at a time::

    queued -> working -> blocked -> completed

`blocked` can step back to `working` when the blocker clears. That is
the only allowed backward move: unfinished work must stay visible.
"""
from __future__ import annotations

from typing import Any

from .store import MemoryStore

STATES = ("queued", "working", "blocked", "completed")
_ORDER = {state: index for index, state in enumerate(STATES)}
_CATEGORY = "task"


class TaskError(ValueError):
    """Raised when a task transition is not allowed."""


class Task:
    """A handle over a durable task entity."""

    def __init__(
        self,
        store: MemoryStore,
        name: str,
        *,
        objective: str | None = None,
        linked: list[str] | None = None,
    ) -> None:
        self.store = store
        self.name = name
        record = store.remember_durable(
            _CATEGORY,
            name,
            {"objective": objective, "linked": linked or []},
            status="queued",
        )
        self._record = record

    @classmethod
    def open(cls, store: MemoryStore, name: str) -> "Task | None":
        record = store.recall_durable(_CATEGORY, name)
        if record is None:
            return None
        task = cls.__new__(cls)
        task.store = store
        task.name = name
        task._record = record
        return task

    @property
    def state(self) -> str:
        return self._record.get("status") or "queued"

    @property
    def body(self) -> dict[str, Any]:
        return self._record.get("body") or {}

    def advance(self, next_state: str) -> dict[str, Any]:
        if next_state not in _ORDER:
            raise TaskError(f"unknown task state {next_state!r}")
        if next_state == "working" and self.state == "blocked":
            pass  # clearing a blocker is allowed
        elif _ORDER[next_state] != _ORDER[self.state] + 1:
            if _ORDER[next_state] <= _ORDER[self.state]:
                raise TaskError(
                    f"cannot move task from {self.state!r} to {next_state!r}"
                )
            raise TaskError(
                f"cannot skip from {self.state!r} to {next_state!r}; "
                "advance one state at a time"
            )
        record = self.store.remember_durable(
            _CATEGORY, self.name, self.body, status=next_state
        )
        self.store.record_event(
            evaluated={"task": self.name, "from": self.state, "to": next_state},
            acted=[f"task {self.name}: {self.state} -> {next_state}"],
        )
        self._record = record
        return record


def unfinished(store: MemoryStore) -> list[dict[str, Any]]:
    """Return every task that is not completed, work first."""
    tasks = store.list_durable(_CATEGORY)
    open_tasks = [task for task in tasks if task.get("status") != "completed"]
    rank = {"working": 0, "blocked": 1, "queued": 2}
    open_tasks.sort(key=lambda task: rank.get(task.get("status"), 9))
    return open_tasks
