"""Virtuals registration and dispatch with memory write-back.

The agent registers itself with Virtuals through the GAME SDK v2, then
remembers its own agent id as a durable identity entity. The id lives
in memory, not in process: every later run reads it back from the
store, so a fresh Mnemos still knows which agent it is and can dispatch
work to it.

Memory stays honest: without an API key the identity records a dry-run
attempt and never claims to be registered.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

from ..memory.store import MemoryStore

_IDENTITY = "identity"
_AGENT_NAME = "virtuals_agent"

ClientFactory = Callable[[str], Any]


def _game_client(api_key: str) -> Any:
    from game_sdk.game.api_v2 import GAMEClientV2

    return GAMEClientV2(api_key)


@dataclass(frozen=True)
class Registration:
    registered: bool
    note: str
    agent_id: str | None = None


def register_with_virtuals(
    store: MemoryStore,
    *,
    name: str = "mnemos",
    api_key: str | None = None,
    live: bool = False,
    client_factory: ClientFactory | None = None,
) -> Registration:
    api_key = api_key or os.environ.get("VIRTUALS_API_KEY")

    if live:
        if not api_key:
            raise RuntimeError("live registration needs VIRTUALS_API_KEY")
        client = (client_factory or _game_client)(api_key)
        agent_id = client.create_agent(
            name,
            "personal agent with durable Sibyl memory",
            "act for its owner using remembered facts, agreements, and lessons",
        )
        store.remember_durable(
            _IDENTITY,
            _AGENT_NAME,
            {
                "requested_name": name,
                "agent_id": agent_id,
                "registered": True,
                "note": "live on virtuals",
            },
        )
        store.record_event(
            evaluated={"platform": "virtuals", "agent_id": agent_id},
            acted=[f"virtuals registration: agent {agent_id}"],
        )
        return Registration(
            registered=True,
            note=f"registered on Virtuals as {agent_id}",
            agent_id=agent_id,
        )

    if api_key:
        body = {
            "requested_name": name,
            "registered": False,
            "note": "key present, run with --live to register",
        }
        note = "api key found; run register --live to create the agent"
    else:
        body = {
            "requested_name": name,
            "registered": False,
            "note": "dry run, no VIRTUALS_API_KEY",
        }
        note = "dry run; set VIRTUALS_API_KEY and pass --live to register"

    store.remember_durable(_IDENTITY, _AGENT_NAME, body)
    store.record_event(
        evaluated={"platform": "virtuals", "name": name},
        acted=[f"virtuals registration attempt: {note}"],
    )
    return Registration(registered=False, note=note)


def dispatch_to_virtuals(
    store: MemoryStore,
    task: str,
    *,
    api_key: str | None = None,
    client_factory: ClientFactory | None = None,
) -> dict[str, Any]:
    """Send a task to the remembered Virtuals agent, from memory."""
    identity = store.recall_durable(_IDENTITY, _AGENT_NAME)
    if identity is None:
        raise RuntimeError("no virtuals identity in memory; register first")
    body = identity.get("body") or {}
    agent_id = body.get("agent_id")
    if not body.get("registered") or not agent_id:
        return {"note": "identity exists but is not registered; nothing sent"}

    api_key = api_key or os.environ.get("VIRTUALS_API_KEY")
    if not api_key:
        raise RuntimeError("dispatch needs VIRTUALS_API_KEY")
    client = (client_factory or _game_client)(api_key)
    result = client.set_worker_task(agent_id, task)
    store.record_event(
        evaluated={"platform": "virtuals", "agent_id": agent_id, "task": task},
        acted=[f"dispatched to virtuals agent {agent_id}: {task}"],
    )
    return result
