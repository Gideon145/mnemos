"""MCP server: every Mnemos command as a tool for any MCP client.

A Claude, Codex, or any other MCP host that runs this server gets a
durable memory with honest recall, gated payments, lessons, and tasks.
The tools are thin wrappers over the same core the CLI uses: there is
exactly one code path for memory, and both surfaces share it.

Run with: mnemos mcp  (or python -m core.mcp)
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .agent import RecallEngine
from .agent.recap import recap
from .agent.replay import replay
from .memory.lessons import learn
from .memory.revision import blast_radius, is_suspect, reconsider, revise
from .memory.store import MemoryStore
from .memory.tasks import Task, unfinished

DB_ENV = "MNEMOS_DB"
DEFAULT_DB = str(Path.home() / ".mnemos" / "memory.db")

server = FastMCP("mnemos")


def _slug(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    slug = slug[:limit].rstrip("_")
    return slug or "note"


def _store() -> MemoryStore:
    return MemoryStore(os.environ.get(DB_ENV, DEFAULT_DB))


@server.tool()
def remember(text: str, category: str = "preference") -> str:
    """Store a durable fact. Categories: preference, lesson, identity."""
    store = _store()
    try:
        store.remember_durable(category, text, {"value": text})
        store.record_event(
            evaluated={"category": category, "name": text},
            acted=[f"remembered {category} {text[:60]}"],
        )
        return f"remembered {category}: {text}"
    finally:
        store.close()


@server.tool()
def ask(question: str) -> str:
    """Ask the agent. It answers only from memory and says when it does not know."""
    store = _store()
    try:
        answer = RecallEngine(store).ask(question)
        return answer.answer
    finally:
        store.close()


@server.tool()
def learn_lesson(text: str, severity: str = "medium") -> str:
    """Record a failure as a lesson. Severity: low, medium, high."""
    store = _store()
    try:
        learn(store, text, severity=severity)
        return f"learned ({severity}): {text}"
    finally:
        store.close()


@server.tool()
def task(objective: str) -> str:
    """Create a task that survives restarts."""
    store = _store()
    try:
        Task(store, _slug(objective), objective=objective)
        return f"task queued: {objective}"
    finally:
        store.close()


@server.tool()
def resume() -> str:
    """List unfinished work, work first."""
    store = _store()
    try:
        records = unfinished(store)
        if not records:
            return "nothing unfinished"
        lines = [
            f"- {record.get('name')} ({record.get('status')}): "
            f"{(record.get('body') or {}).get('objective', '')}"
            for record in records
        ]
        return "\n".join(lines)
    finally:
        store.close()


@server.tool()
def recap_day() -> str:
    """Summarize the journal and standing agreements."""
    store = _store()
    try:
        return recap(store).text
    finally:
        store.close()


@server.tool()
def replay(subject: str) -> str:
    """Show the causal chain for a subject, oldest first."""
    store = _store()
    try:
        return replay(store, subject).text
    finally:
        store.close()


@server.tool()
def revise(category: str, name: str, new_value: str, reason: str = "") -> str:
    """Correct a fact, then taint everything that depended on it."""
    store = _store()
    try:
        result = revise(
            store, category, name, new_value, reason=reason or None
        )
        lines = [
            f"revised {result['fact']}: {result['from']} -> {result['to']}",
            f"decisions affected: {result['decisions_affected']}",
        ]
        for item in result["newly_suspect"]:
            lines.append(f"suspect: {item}")
        if not result["newly_suspect"]:
            lines.append("nothing depended on this fact")
        return "\n".join(lines)
    finally:
        store.close()


@server.tool()
def blast(category: str, name: str) -> str:
    """Report the blast radius of a fact without changing anything."""
    store = _store()
    try:
        radius = blast_radius(store, f"{category}:{name}")
        return (
            f"blast radius of {radius['fact']}: {radius['decisions']} "
            f"decisions, {radius['agreements']} agreements, "
            f"{radius['tasks']} tasks, {radius['payments']} payments"
        )
    finally:
        store.close()


@server.tool()
def reconsider(category: str, name: str, decision: str, reason: str = "") -> str:
    """Review a suspect entity. decision: valid or invalid."""
    store = _store()
    try:
        result = reconsider(
            store, category, name, decision, reason=reason or None
        )
        state = "gate reopened" if result["reopened"] else "still suspect"
        return f"reconsidered {category} {name}: {decision}, {state}"
    finally:
        store.close()


@server.tool()
def suspect() -> str:
    """List entities currently blocked by a revised memory."""
    store = _store()
    try:
        lines = []
        for category in ("agreement", "task"):
            for record in store.list_durable(category):
                name = record.get("name")
                if is_suspect(store, category, name):
                    lines.append(f"- {category} {name}")
        return "\n".join(lines) if lines else "(nothing suspect)"
    finally:
        store.close()


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
