"""Dogfood: store this project's own lessons in Mnemos.

The build team uses the product it builds. The database lives in
.mnemos/project.db (gitignored) and holds the real lessons from the
hackathon so far, plus the agreements we made with ourselves.
"""
from __future__ import annotations

from pathlib import Path

from core.memory.lessons import learn
from core.memory.store import MemoryStore
from core.memory.tasks import Task

DB = Path(__file__).resolve().parent.parent / ".mnemos" / "project.db"

LESSONS = [
    ("committed twice with a failing test still red", "medium"),
    ("x api posting is blocked at the account level, use the browser", "medium"),
    ("inline python in powershell always breaks, write script files", "low"),
    ("never announce a feature before its tests are green", "high"),
]


def main() -> int:
    DB.parent.mkdir(parents=True, exist_ok=True)
    store = MemoryStore(DB)
    try:
        store.remember_durable(
            "preference", "commit_style",
            {"value": "granular commits, tests before push, no fake history"},
        )
        store.remember_durable(
            "preference", "post_rules",
            {"value": "no em dashes, no emojis, tag sibylcap and the partner"},
        )
        for text, severity in LESSONS:
            learn(store, text, severity=severity)
        Task(store, "film-demo", objective="record the unedited demo take")
        Task(store, "virtuals-live", objective="register the agent on Virtuals")
        print(f"dogfooded into {DB}")
        print("lessons:", len(store.list_durable("lesson")))
        print("tasks:", len(store.list_durable("task")))
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
