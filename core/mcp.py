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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import Icon

from .agent import RecallEngine
from .agent.recap import recap
from .agent.replay import replay as replay_memory
from .memory.lessons import learn
from .memory.revision import (
    blast_radius as blast_radius_memory,
    is_suspect as is_suspect_memory,
    reconsider as reconsider_memory,
    revise as revise_memory,
)
from .memory.store import MemoryStore
from .memory.tasks import Task, unfinished

DB_ENV = "MNEMOS_DB"
DEFAULT_DB = str(Path.home() / ".mnemos" / "memory.db")

# Host 0.0.0.0 keeps FastMCP from auto-enabling localhost-only DNS
# rebinding protection, which would reject Railway/Smithery hostnames.
server = FastMCP(
    "mnemos",
    host="0.0.0.0",
    instructions=(
        "Mnemos is an agent with durable memory on Sibyl. Store facts, ask "
        "recall questions, record lessons, manage tasks that survive "
        "restarts, and use the revision gate: when a fact is corrected, "
        "everything that depended on it becomes suspect and the payment "
        "gate refuses until each item is explicitly reconsidered."
    ),
    website_url="https://github.com/Gideon145/mnemos",
    icons=[
        Icon(
            src="https://raw.githubusercontent.com/Gideon145/mnemos/main/docs/images/banner.jpg",
            sizes=["1024x1024"],
        )
    ],
)


def _slug(text: str, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    slug = slug[:limit].rstrip("_")
    return slug or "note"


def _store() -> MemoryStore:
    return MemoryStore(os.environ.get(DB_ENV, DEFAULT_DB))


# ------------------------------------------------------------------ #
# typed results
# ------------------------------------------------------------------ #
@dataclass
class RememberResult:
    category: str
    name: str


@dataclass
class AskResult:
    question: str
    answer: str
    found: bool
    sources: list[str] = field(default_factory=list)


@dataclass
class LessonResult:
    severity: str
    text: str


@dataclass
class TaskResult:
    name: str
    objective: str


@dataclass
class ResumeResult:
    unfinished: list[dict[str, str]]


@dataclass
class RecapResult:
    text: str


@dataclass
class ReplayResult:
    subject: str
    text: str


@dataclass
class ReviseResult:
    revision_id: str
    fact: str
    old: str
    new: str
    decisions_affected: int
    payments_affected: int
    newly_suspect: list[str] = field(default_factory=list)


@dataclass
class BlastResult:
    fact: str
    decisions: int
    agreements: list[str] = field(default_factory=list)
    tasks: list[str] = field(default_factory=list)
    payments: int = 0


@dataclass
class ReconsiderResult:
    entity: str
    decision: str
    gate_reopened: bool


@dataclass
class SuspectResult:
    suspect: list[str] = field(default_factory=list)


@dataclass
class ResetResult:
    cleared: int


@server.tool(structured_output=True)
def remember(text: str, category: str = "preference") -> RememberResult:
    """Store a durable fact. Categories: preference, lesson, identity."""
    store = _store()
    try:
        store.remember_durable(category, text, {"value": text})
        store.record_event(
            evaluated={"category": category, "name": text},
            acted=[f"remembered {category} {text[:60]}"],
        )
        return RememberResult(category=category, name=text)
    finally:
        store.close()


@server.tool(structured_output=True)
def ask(question: str) -> AskResult:
    """Ask the agent. It answers only from memory and says when it does not know."""
    store = _store()
    try:
        answer = RecallEngine(store).ask(question)
        return AskResult(
            question=question,
            answer=answer.answer,
            found=answer.found_anything,
            sources=list(answer.sources),
        )
    finally:
        store.close()


@server.tool(structured_output=True)
def learn_lesson(text: str, severity: str = "medium") -> LessonResult:
    """Record a failure as a lesson. Severity: low, medium, high."""
    store = _store()
    try:
        learn(store, text, severity=severity)
        return LessonResult(severity=severity, text=text)
    finally:
        store.close()


@server.tool(structured_output=True)
def task(objective: str) -> TaskResult:
    """Create a task that survives restarts."""
    store = _store()
    try:
        name = _slug(objective)
        Task(store, name, objective=objective)
        return TaskResult(name=name, objective=objective)
    finally:
        store.close()


@server.tool(structured_output=True)
def resume() -> ResumeResult:
    """List unfinished work, work first."""
    store = _store()
    try:
        items = [
            {
                "name": str(record.get("name")),
                "status": str(record.get("status")),
                "objective": str((record.get("body") or {}).get("objective", "")),
            }
            for record in unfinished(store)
        ]
        return ResumeResult(unfinished=items)
    finally:
        store.close()


@server.tool(structured_output=True)
def recap_day() -> RecapResult:
    """Summarize the journal and standing agreements."""
    store = _store()
    try:
        return RecapResult(text=recap(store).text)
    finally:
        store.close()


@server.tool(structured_output=True)
def replay(subject: str) -> ReplayResult:
    """Show the causal chain for a subject, oldest first."""
    store = _store()
    try:
        return ReplayResult(subject=subject, text=replay_memory(store, subject).text)
    finally:
        store.close()


@server.tool(structured_output=True)
def revise(
    category: str, name: str, new_value: str, reason: str = ""
) -> ReviseResult:
    """Correct a fact, then taint everything that depended on it."""
    store = _store()
    try:
        result = revise_memory(
            store, category, name, new_value, reason=reason or None
        )
        return ReviseResult(
            revision_id=str(result["revision_id"]),
            fact=str(result["fact"]),
            old=str(result["from"]),
            new=str(result["to"]),
            decisions_affected=int(result["decisions_affected"]),
            payments_affected=int(result["payments_affected"]),
            newly_suspect=list(result["newly_suspect"]),
        )
    finally:
        store.close()


@server.tool(structured_output=True)
def blast(category: str, name: str) -> BlastResult:
    """Report the blast radius of a fact without changing anything."""
    store = _store()
    try:
        radius = blast_radius_memory(store, f"{category}:{name}")
        return BlastResult(
            fact=str(radius["fact"]),
            decisions=int(radius["decisions"]),
            agreements=list(radius["agreements"]),
            tasks=list(radius["tasks"]),
            payments=int(radius["payments"]),
        )
    finally:
        store.close()


@server.tool(structured_output=True)
def reconsider(
    category: str, name: str, decision: str, reason: str = ""
) -> ReconsiderResult:
    """Review a suspect entity. decision: valid or invalid."""
    store = _store()
    try:
        result = reconsider_memory(
            store, category, name, decision, reason=reason or None
        )
        return ReconsiderResult(
            entity=f"{category}:{name}",
            decision=decision,
            gate_reopened=bool(result["reopened"]),
        )
    finally:
        store.close()


@server.tool(structured_output=True)
def suspect() -> SuspectResult:
    """List entities currently blocked by a revised memory."""
    store = _store()
    try:
        blocked = []
        for category in ("agreement", "task"):
            for record in store.list_durable(category):
                name = record.get("name")
                if is_suspect_memory(store, category, name):
                    blocked.append(f"{category} {name}")
        return SuspectResult(suspect=blocked)
    finally:
        store.close()


@server.tool(structured_output=True)
def reset() -> ResetResult:
    """Wipe every durable entity so the memory starts fresh. The journal stays."""
    from .memory.store import DURABLE_CATEGORIES

    store = _store()
    try:
        cleared = 0
        for category in DURABLE_CATEGORIES:
            for record in store.list_durable(category):
                store.forget_durable(category, record.get("name"))
                cleared += 1
        store.record_event(acted=[f"reset memory: {cleared} entities cleared"])
        return ResetResult(cleared=cleared)
    finally:
        store.close()


_FACT_PATTERNS = (
    (r"(?:my name is|call me)\s+(.+)", "identity"),
    (r"i like\s+(.+)", "preference"),
    (r"my\s+(.+?)\s+is\s+(.+)", "preference"),
    (r"i am\s+(.+)", "preference"),
)


def _extract_facts(text: str) -> list[tuple[str, str]]:
    """Pull stated facts out of a chat message, deterministically."""
    facts: list[tuple[str, str]] = []
    for pattern, category in _FACT_PATTERNS:
        match = re.match(pattern, text.strip(), re.IGNORECASE)
        if match:
            raw = " ".join(match.groups()).strip()
            if len(raw.split()) > 12 or not raw:
                continue
            facts.append((category, raw))
            break
    return facts


def _chat_answer(user_text: str) -> str:
    """Answer conversationally, grounded in whatever memory currently holds."""
    api_key = os.environ.get("VIRTUALS_API_KEY")
    endpoint = os.environ.get("VIRTUALS_COMPUTE_URL")
    if not api_key or not endpoint:
        raise RuntimeError(
            "the hosted chat needs VIRTUALS_API_KEY and VIRTUALS_COMPUTE_URL"
        )

    # Facts the user states get stored before the model answers, so the
    # memory the answer is grounded in already contains them.
    for category, value in _extract_facts(user_text):
        store = _store()
        try:
            store.remember_durable(category, _slug(value), {"value": value})
            store.record_event(
                evaluated={"source": "playground chat"},
                acted=[f"remembered {category} {value[:60]}"],
            )
        finally:
            store.close()

    store = _store()
    try:
        memory = RecallEngine(store).ask("what do you know about me?").answer
    finally:
        store.close()
    # The ACP content filter refuses retention phrasing like "I will keep
    # it", so normalize the empty-store answer before embedding.
    if "don't remember anything" in memory:
        memory = "The memory store is currently empty."

    system = (
        "You are Mnemos, a memory assistant. A durable memory store, owned by "
        "the user and stored on Sibyl, is attached to this chat. Below is its "
        "current content. Facts the user states are stored automatically.\n\n"
        f"MEMORY:\n{memory}\n\n"
        "Rules: ground answers in the memory above when the user asks about "
        "it. Acknowledge newly stated facts naturally, no need to instruct "
        "the user to do anything. Never present invented content as memory. "
        "Never use em dashes or en dashes, use commas or periods instead. "
        "Keep answers to 1 to 3 sentences, warm but not sycophantic."
    )
    payload: dict[str, Any] = {
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ]
    }
    model = os.environ.get("VIRTUALS_MODEL")
    if model:
        payload["model"] = model

    from .integrations.virtuals import _acp_transport

    result = _acp_transport(endpoint, api_key, payload)
    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError(f"agent returned no choices: {str(result)[:160]}")
    answer = str((choices[0].get("message") or {}).get("content", "")).strip()
    # House style: no em or en dashes anywhere.
    return answer.replace("\u2014", ", ").replace("\u2013", "-")


def run_server(http: bool = False) -> None:
    """Serve the tools over stdio (local clients) or streamable HTTP (Smithery)."""
    if not http:
        server.run()
        return
    import uvicorn
    from contextlib import asynccontextmanager
    from starlette.applications import Starlette
    from starlette.concurrency import run_in_threadpool
    from starlette.middleware.cors import CORSMiddleware
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

    async def chat_endpoint(request: Any) -> JSONResponse:
        try:
            body = await request.json()
            text = str((body or {}).get("message", "")).strip()
            if not text:
                return JSONResponse({"error": "message required"}, status_code=400)
            answer = await run_in_threadpool(_chat_answer, text)
            return JSONResponse({"answer": answer})
        except Exception as exc:  # pragma: no cover
            return JSONResponse({"error": str(exc)}, status_code=502)

    base = server.streamable_http_app()

    @asynccontextmanager
    async def combined_lifespan(_app: Any):
        # The mounted MCP app owns the session manager, which only starts
        # inside its own lifespan. Compose it into the root lifespan.
        async with base.router.lifespan_context(base):
            yield

    app: Any = Starlette(
        routes=[
            Route("/chat", chat_endpoint, methods=["POST"]),
            Mount("/", app=base),
        ],
        lifespan=combined_lifespan,
    )
    # Browser clients (the live playground) need CORS plus access to the
    # session header the streamable-http handshake returns.
    app = CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)


def main() -> None:
    run_server()


if __name__ == "__main__":
    main()
