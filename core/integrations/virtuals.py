"""Virtuals registration and dispatch with memory write-back.

Two live paths are supported:

- Console (ACP): the agent is created in the Virtuals console and its
  id is recorded with `--agent-id`. Dispatch calls the agent's compute
  endpoint (OpenAI-compatible) with the API key generated in the
  console's Compute settings.
- GAME SDK v2: `register --live` creates the agent through the legacy
  SDK and dispatch sets a worker task.

Either way the agent id lives in memory, not in process: a fresh
Mnemos reads it back from the store before acting.
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from ..memory.store import MemoryStore

_IDENTITY = "identity"
_AGENT_NAME = "virtuals_agent"

ClientFactory = Callable[[str], Any]
Transport = Callable[[str, str, dict[str, Any]], Any]


def _game_client(api_key: str) -> Any:
    from game_sdk.game.api_v2 import GAMEClientV2

    return GAMEClientV2(api_key)


def _acp_transport(endpoint: str, api_key: str, payload: dict[str, Any]) -> Any:
    base = endpoint.rstrip("/")
    url = (
        base + "/chat/completions"
        if base.endswith("/v1")
        else base + "/v1/chat/completions"
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


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
    agent_id: str | None = None,
    client_factory: ClientFactory | None = None,
) -> Registration:
    api_key = api_key or os.environ.get("VIRTUALS_API_KEY")

    if agent_id:
        store.remember_durable(
            _IDENTITY,
            _AGENT_NAME,
            {
                "requested_name": name,
                "agent_id": agent_id,
                "registered": True,
                "note": "created in the virtuals console",
            },
        )
        store.record_event(
            evaluated={"platform": "virtuals", "agent_id": agent_id},
            acted=[f"virtuals registration: console agent {agent_id}"],
        )
        return Registration(
            registered=True,
            note=f"recorded console agent {agent_id}",
            agent_id=agent_id,
        )

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
    endpoint: str | None = None,
    model: str | None = None,
    client_factory: ClientFactory | None = None,
    transport: Transport | None = None,
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
    endpoint = endpoint or os.environ.get("VIRTUALS_COMPUTE_URL")

    if endpoint:
        if not api_key:
            raise RuntimeError("ACP dispatch needs VIRTUALS_API_KEY")
        payload = {
            "messages": [{"role": "user", "content": task}],
        }
        model = model or os.environ.get("VIRTUALS_MODEL")
        if model:
            payload["model"] = model
        send = transport or _acp_transport
        result = send(endpoint, api_key, payload)
        store.record_event(
            evaluated={"platform": "virtuals", "agent_id": agent_id, "task": task},
            acted=[f"dispatched to virtuals agent {agent_id}: {task}"],
        )
        return {"agent_id": agent_id, "response": result}

    if not api_key:
        raise RuntimeError("dispatch needs VIRTUALS_API_KEY")
    client = (client_factory or _game_client)(api_key)
    result = client.set_worker_task(agent_id, task)
    store.record_event(
        evaluated={"platform": "virtuals", "agent_id": agent_id, "task": task},
        acted=[f"dispatched to virtuals agent {agent_id}: {task}"],
    )
    return result
