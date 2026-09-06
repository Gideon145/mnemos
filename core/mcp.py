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
from .memory.dream import dream as dream_memory
from .memory.dream import pending as dream_pending
from .memory.entities import annotate
from .memory.lessons import learn
from .memory.owner import owner_profile
from .memory.pulse import decline, pulse as pulse_memory
from .memory.rewind import rewind as rewind_memory
from .memory.revision import (
    blast_radius as blast_radius_memory,
    is_suspect as is_suspect_memory,
    reconsider as reconsider_memory,
    revise as revise_memory,
)
from .memory.store import MemoryStore
from .memory.tasks import Task, unfinished

DB_ENV = "MNEMOS_DB"
DEVICES_ENV = "MNEMOS_DEVICES_DIR"
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


def _device_path(device: str) -> str:
    """One database per device, under the devices directory."""
    slug = re.sub(r"[^a-zA-Z0-9_-]", "", device)[:64] or "anon"
    base = os.environ.get(DEVICES_ENV, "")
    if base:
        return str(Path(base) / slug / "memory.db")
    return str(Path(os.environ.get(DB_ENV, DEFAULT_DB)).parent / "devices" / slug / "memory.db")


def _store(device: str = "") -> MemoryStore:
    if device:
        path = Path(_device_path(device))
        path.parent.mkdir(parents=True, exist_ok=True)
        return MemoryStore(path)
    return MemoryStore(os.environ.get(DB_ENV, DEFAULT_DB))


# ------------------------------------------------------------------ #
# typed results
# ------------------------------------------------------------------ #
@dataclass
class RememberResult:
    category: str
    name: str
    created_at: str = ""


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
def remember(text: str, category: str = "preference", device: str = "") -> RememberResult:
    """Store a durable fact. Categories: preference, lesson, identity."""
    store = _store(device)
    try:
        store.remember_durable(category, text, {"value": text})
        annotate(store, category, text, text)
        record = store.recall_durable(category, text)
        store.record_event(
            evaluated={"category": category, "name": text},
            acted=[f"remembered {category} {text[:60]}"],
        )
        return RememberResult(
            category=category,
            name=text,
            created_at=str((record or {}).get("created_at") or ""),
        )
    finally:
        store.close()


@server.tool(structured_output=True)
def ask(question: str, device: str = "") -> AskResult:
    """Ask the agent. It answers only from memory and says when it does not know."""
    store = _store(device)
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
def learn_lesson(text: str, severity: str = "medium", device: str = "") -> LessonResult:
    """Record a failure as a lesson. Severity: low, medium, high."""
    store = _store(device)
    try:
        learn(store, text, severity=severity)
        return LessonResult(severity=severity, text=text)
    finally:
        store.close()


@server.tool(structured_output=True)
def task(objective: str, device: str = "") -> TaskResult:
    """Create a task that survives restarts."""
    store = _store(device)
    try:
        name = _slug(objective)
        Task(store, name, objective=objective)
        return TaskResult(name=name, objective=objective)
    finally:
        store.close()


@server.tool(structured_output=True)
def resume(device: str = "") -> ResumeResult:
    """List unfinished work, work first."""
    store = _store(device)
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
def recap_day(device: str = "") -> RecapResult:
    """Summarize the journal and standing agreements."""
    store = _store(device)
    try:
        return RecapResult(text=recap(store).text)
    finally:
        store.close()


@server.tool(structured_output=True)
def replay(subject: str, device: str = "") -> ReplayResult:
    """Show the causal chain for a subject, oldest first."""
    store = _store(device)
    try:
        return ReplayResult(subject=subject, text=replay_memory(store, subject).text)
    finally:
        store.close()


@server.tool(structured_output=True)
def revise(
    category: str, name: str, new_value: str, reason: str = "", device: str = ""
) -> ReviseResult:
    """Correct a fact, then taint everything that depended on it."""
    store = _store(device)
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
def blast(category: str, name: str, device: str = "") -> BlastResult:
    """Report the blast radius of a fact without changing anything."""
    store = _store(device)
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
    category: str, name: str, decision: str, reason: str = "", device: str = ""
) -> ReconsiderResult:
    """Review a suspect entity. decision: valid or invalid."""
    store = _store(device)
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
def suspect(device: str = "") -> SuspectResult:
    """List entities currently blocked by a revised memory."""
    store = _store(device)
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
def reset(device: str = "") -> ResetResult:
    """Wipe every durable entity so the memory starts fresh. The journal stays."""
    from .memory.store import DURABLE_CATEGORIES

    store = _store(device)
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


@dataclass
class DreamResult:
    events_scanned: int
    proposals: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)


@dataclass
class RewindResult:
    at: str
    entities: int
    changed_count: int
    changed: list[dict[str, str]] = field(default_factory=list)


@dataclass
class PulseResult:
    matter: str = ""
    matter_id: str = ""
    queued: int = 0


@dataclass
class OwnerResult:
    profile: str
    identity: int
    preferences: int
    principles: int
    agreements: int
    vetoes: int


@server.tool(structured_output=True)
def dream(min_hits: int = 2, device: str = "") -> DreamResult:
    """Consolidate the journal into review-gated proposals. Nothing applies itself."""
    store = _store(device)
    try:
        report = dream_memory(store, min_hits=min_hits)
        return DreamResult(
            events_scanned=int(report["events_scanned"]),
            proposals=list(report["proposals"]),
            pending=[str(r.get("name")) for r in dream_pending(store)],
        )
    finally:
        store.close()


@server.tool(structured_output=True)
def rewind(at: str, device: str = "") -> RewindResult:
    """Memory state at a past timestamp, with the diff to now."""
    store = _store(device)
    try:
        result = rewind_memory(store, at)
        return RewindResult(
            at=at,
            entities=len(result["entities"]),
            changed_count=int(result["changed_count"]),
            changed=[
                {
                    "entity": f"{item['category']}:{item['name']}",
                    "at": str(item["at"]),
                    "now": str(item["now"]),
                }
                for item in result["changed"]
            ],
        )
    finally:
        store.close()


@server.tool(structured_output=True)
def pulse(device: str = "") -> PulseResult:
    """Raise the most urgent matter memory is holding, at most one per tick."""
    store = _store(device)
    try:
        result = pulse_memory(store)
        matter = result["matter"] or {}
        return PulseResult(
            matter=str(matter.get("text") or ""),
            matter_id=str(matter.get("id") or ""),
            queued=int(result["queued"]),
        )
    finally:
        store.close()


@server.tool(structured_output=True)
def pulse_decline(matter_id: str, device: str = "") -> PulseResult:
    """Suppress a pulse matter id so it never returns."""
    store = _store(device)
    try:
        decline(store, matter_id)
        return PulseResult(matter_id=matter_id)
    finally:
        store.close()


@server.tool(structured_output=True)
def owner(device: str = "") -> OwnerResult:
    """The curated owner profile: identity, preferences, principles, agreements."""
    store = _store(device)
    try:
        result = owner_profile(store)
        return OwnerResult(
            profile=str(result["profile"]),
            identity=int(result["identity"]),
            preferences=int(result["preferences"]),
            principles=int(result["principles"]),
            agreements=int(result["agreements"]),
            vetoes=int(result["vetoes"]),
        )
    finally:
        store.close()


_FACT_PATTERNS = (
    (r"(?:my name is|call me)\s+(.+)", "identity"),
    (r"i like\s+(.+)", "preference"),
    (r"my\s+(.+?)\s+is\s+(.+)", "preference"),
    (r"i am\s+(.+)", "preference"),
)


def _extract_facts(text: str) -> list[tuple[str, str]]:
    """Pull every stated fact out of a chat message, deterministically.

    Scans the whole message, so compound sentences like
    "how are u my name is john and i live in england" yield every fact.
    """
    facts: list[tuple[str, str]] = []
    lowered = text.lower()
    seen: set[tuple[str, str]] = set()

    def add(category: str, raw: str) -> None:
        raw = raw.strip().rstrip(".,")
        if not raw or len(raw.split()) > 12:
            return
        if (category, raw) not in seen:
            seen.add((category, raw))
            facts.append((category, raw))

    boundary = r"(?=\s+and\s|\s+but\s|[,.]|\s+i\s+live|\s+i\s+like|\s+i\s+am|\s+my\s|$)"
    for match in re.finditer(r"my name is\s+([a-z][a-z ]*?)" + boundary, lowered):
        add("identity", match.group(1))
    for match in re.finditer(r"call me\s+([a-z][a-z ]*?)" + boundary, lowered):
        add("identity", match.group(1))
    for match in re.finditer(r"i live in\s+([a-z][a-z ]*?)" + boundary, lowered):
        add("preference", "i live in " + match.group(1))
    for match in re.finditer(r"i like\s+([a-z0-9 ,.$]+?)" + boundary, lowered):
        add("preference", "i like " + match.group(1))
    for match in re.finditer(
        r"i\s+(?:also\s+|really\s+|just\s+|kind\s+of\s+|kinda\s+)?(like|love)\s+"
        r"([a-z0-9 ,.$]+?)" + boundary,
        lowered,
    ):
        add("preference", "i " + match.group(1) + " " + match.group(2))
    for match in re.finditer(
        r"my\s+([a-z][a-z ]*?)\s+is\s+([a-z0-9 .,$]+?)" + boundary, lowered
    ):
        subject = match.group(1).strip()
        if subject != "name":
            add("preference", f"{subject} is {match.group(2)}")
    whole = re.match(r"i am\s+(.+)", lowered.strip())
    if whole:
        raw = whole.group(1).strip()
        if raw not in ("fine", "ok", "okay", "good", "here"):
            add("preference", raw)
    return facts


_CHANGE_RE = re.compile(
    r"(?:change|update|set)\s+(?:my\s+)?([a-z0-9 ]{1,50}?)\s+to\s+"
    r"([a-z0-9 .,$]{1,60})"
)

_QUESTION_OPENERS = {
    "what",
    "how",
    "when",
    "where",
    "who",
    "why",
    "do",
    "does",
    "did",
    "can",
    "could",
    "would",
    "should",
    "is",
    "are",
    "was",
    "were",
}


def _is_question(text: str) -> bool:
    """Questions do not state facts, so nothing is extracted from them."""
    lowered = text.strip().lower()
    if not lowered:
        return False
    if lowered.endswith("?"):
        return True
    first = lowered.split()[0].rstrip(",")
    return first in _QUESTION_OPENERS


def _change_intents(text: str) -> list[tuple[str, str]]:
    """Deterministic 'change X to Y' detection over a chat message."""
    lowered = text.lower()
    intents: list[tuple[str, str]] = []
    for match in _CHANGE_RE.finditer(lowered):
        subject = match.group(1).strip().rstrip(" .,")
        new_value = match.group(2).strip().rstrip(" .,")
        if subject and new_value and len(new_value.split()) <= 10:
            intents.append((subject, new_value))
    return intents


def _apply_change_intents(store: MemoryStore, user_text: str) -> int:
    """Revise the matching active entity for every change intent.

    A pronoun subject ("change it to dark coffee") resolves against the
    words of the new value, so the preference about coffee is the one
    that gets revised. A name subject revises the user's identity.
    Deterministic: no model decides the match.
    """
    applied = 0
    for subject, new_value in _change_intents(user_text):
        tokens = [word for word in subject.split() if len(word) > 2]
        if "name" in subject.split():
            for record in store.list_durable("identity"):
                name = record.get("name")
                if name in ("dream_cursor", "pulse_suppress"):
                    continue
                revise_memory(
                    store,
                    "identity",
                    name,
                    new_value,
                    reason="chat correction",
                )
                applied += 1
                break
            continue
        if not tokens:
            tokens = [word for word in new_value.split() if len(word) > 2]
        if not tokens:
            continue
        best: dict[str, Any] | None = None
        best_score = 0
        for record in store.list_durable("preference"):
            if record.get("status") not in (None, "active"):
                continue
            value = str((record.get("body") or {}).get("value") or "").lower()
            score = sum(1 for token in tokens if token in value)
            if score > best_score:
                best, best_score = record, score
        if best is not None:
            revise_memory(
                store,
                "preference",
                best.get("name"),
                new_value,
                reason="chat correction",
            )
            applied += 1
    return applied


def _chat_answer(user_text: str, device: str = "") -> str:
    """Answer conversationally, grounded in whatever memory currently holds."""
    api_key = os.environ.get("VIRTUALS_API_KEY")
    endpoint = os.environ.get("VIRTUALS_COMPUTE_URL")
    if not api_key or not endpoint:
        raise RuntimeError(
            "the hosted chat needs VIRTUALS_API_KEY and VIRTUALS_COMPUTE_URL"
        )

    # Change intents go through the same revision path as the CLI, so a
    # "change it to X" in chat actually changes memory before the model
    # answers. The model never claims an update memory did not receive.
    store = _store(device)
    try:
        _apply_change_intents(store, user_text)
    finally:
        store.close()

    # Facts the user states get stored before the model answers, so the
    # memory the answer is grounded in already contains them. Questions
    # state nothing, so nothing is extracted from them.
    if not _is_question(user_text):
        for category, value in _extract_facts(user_text):
            store = _store(device)
            try:
                store.remember_durable(category, _slug(value), {"value": value})
                store.record_event(
                    evaluated={"source": "playground chat"},
                    acted=[f"remembered {category} {value[:60]}"],
                )
            finally:
                store.close()

    store = _store(device)
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
        "INTEGRATION: to add Mnemos to Claude Desktop, paste into "
        "claude_desktop_config.json: {\"mcpServers\": {\"mnemos\": "
        "{\"url\": \"https://mnemos-production-2572.up.railway.app/mcp\"}}}. "
        "For VS Code, put {\"servers\": {\"mnemos\": {\"type\": \"http\", "
        "\"url\": \"https://mnemos-production-2572.up.railway.app/mcp\"}}} "
        "in mcp.json. If the user asks how to integrate or connect you, give "
        "these exact configs and nothing vague.\n\n"
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
    from pathlib import Path as _Path
    from starlette.applications import Starlette
    from starlette.concurrency import run_in_threadpool
    from starlette.middleware.cors import CORSMiddleware
    from starlette.responses import FileResponse, JSONResponse
    from starlette.routing import Mount, Route
    from starlette.staticfiles import StaticFiles

    async def chat_endpoint(request: Any) -> JSONResponse:
        try:
            body = await request.json()
            text = str((body or {}).get("message", "")).strip()
            if not text:
                return JSONResponse({"error": "message required"}, status_code=400)
            device = str((body or {}).get("device", "")).strip()
            answer = await run_in_threadpool(_chat_answer, text, device)
            return JSONResponse({"answer": answer})
        except Exception as exc:  # pragma: no cover
            return JSONResponse({"error": str(exc)}, status_code=502)

    waitlist_path = os.environ.get(
        "WAITLIST_PATH", "/data/waitlist.json"
    )

    async def waitlist_endpoint(request: Any) -> JSONResponse:
        from .waitlist import add_email

        try:
            body = await request.json()
            email = str((body or {}).get("email", "")).strip()
            total = await run_in_threadpool(add_email, waitlist_path, email)
            return JSONResponse({"count": total})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)

    async def waitlist_count(_request: Any) -> JSONResponse:
        from .waitlist import count

        total = await run_in_threadpool(count, waitlist_path)
        return JSONResponse({"count": total})

    async def waitlist_list(_request: Any) -> JSONResponse:
        from .waitlist import entries

        rows = await run_in_threadpool(entries, waitlist_path)
        return JSONResponse({"count": len(rows), "entries": rows})

    async def stats_endpoint(_request: Any) -> JSONResponse:
        """Public usage: distinct playground devices and waitlist count."""
        from .waitlist import count

        def gather() -> dict[str, int]:
            devices_dir = os.environ.get("MNEMOS_DEVICES_DIR", "")
            devices = 0
            if devices_dir:
                root = Path(devices_dir)
                if root.is_dir():
                    devices = sum(
                        1 for child in root.iterdir() if child.is_dir()
                    )
            return {
                "devices": devices,
                "waitlist": count(waitlist_path),
            }

        return JSONResponse(await run_in_threadpool(gather))

    base = server.streamable_http_app()

    @asynccontextmanager
    async def combined_lifespan(_app: Any):
        # The mounted MCP app owns the session manager, which only starts
        # inside its own lifespan. Compose it into the root lifespan.
        async with base.router.lifespan_context(base):
            yield

    site_dir = os.environ.get("SITE_DIR", "")
    routes: list[Any] = [
        Route("/chat", chat_endpoint, methods=["POST"]),
        Route("/waitlist", waitlist_endpoint, methods=["POST"]),
        Route("/waitlist/count", waitlist_count, methods=["GET"]),
        Route("/waitlist/list", waitlist_list, methods=["GET"]),
        Route("/stats", stats_endpoint, methods=["GET"]),
    ]
    if site_dir and _Path(site_dir).is_dir():
        index_file = _Path(site_dir) / "index.html"

        async def home(_request: Any) -> Any:
            return FileResponse(index_file)

        routes += [
            Route("/", home),
            Mount(
                "/assets",
                app=StaticFiles(directory=str(_Path(site_dir) / "assets")),
                name="assets",
            ),
            Mount(
                "/css",
                app=StaticFiles(directory=str(_Path(site_dir) / "css")),
                name="css",
            ),
            Mount(
                "/js",
                app=StaticFiles(directory=str(_Path(site_dir) / "js")),
                name="js",
            ),
        ]
    routes.append(Mount("/", app=base))

    app: Any = Starlette(routes=routes, lifespan=combined_lifespan)
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
