"""Handoff: give another agent your memory, on purpose.

A handoff is a keepsake plus a recipient. It exports the durable tier
and journal into a pack, journals the handoff itself, and prints the
exact command the receiving agent runs. The recipient imports the pack
and recalls everything, including why it was handed over.

This is agent-to-agent memory transfer with no shared runtime: two
instances, two databases, one portable pack.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .keepsake import export_keepsake
from .store import MemoryStore


def handoff(
    store: MemoryStore,
    path: str | Path,
    *,
    recipient: str | None = None,
) -> dict[str, Any]:
    summary = export_keepsake(store, path)
    who = recipient or "another agent"
    store.record_event(
        evaluated={"recipient": recipient, "path": str(path)},
        acted=[f"keepsake handed to {who}"],
    )
    summary["recipient"] = recipient
    summary["import_command"] = f"mnemos keepsake import {path}"
    return summary
