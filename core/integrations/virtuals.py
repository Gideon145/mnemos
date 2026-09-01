"""Virtuals registration with memory write-back.

The agent registers itself with Virtuals and then remembers its own
identity as a durable entity. The id lives in memory, not in process:
every later run reads it back from the store, so a fresh Mnemos on a
fresh machine still knows which agent it is.

Memory stays honest here. Without a real registration the identity
entity records a dry-run attempt and never claims to be registered.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from ..memory.store import MemoryStore

_IDENTITY = "identity"
_AGENT_NAME = "virtuals_agent"


@dataclass(frozen=True)
class Registration:
    registered: bool
    note: str


def register_with_virtuals(
    store: MemoryStore,
    *,
    name: str = "mnemos",
    api_key: str | None = None,
) -> Registration:
    api_key = api_key or os.environ.get("VIRTUALS_API_KEY")

    if api_key:
        # The live call lands when the Virtuals endpoint is wired.
        body: dict[str, Any] = {
            "requested_name": name,
            "registered": False,
            "note": "key present, live registration pending",
        }
        note = "api key found; live registration not wired yet"
    else:
        body = {
            "requested_name": name,
            "registered": False,
            "note": "dry run, no VIRTUALS_API_KEY",
        }
        note = "dry run; set VIRTUALS_API_KEY to register for real"

    store.remember_durable(_IDENTITY, _AGENT_NAME, body)
    store.record_event(
        evaluated={"platform": "virtuals", "name": name},
        acted=[f"virtuals registration attempt: {note}"],
    )
    return Registration(registered=False, note=note)
