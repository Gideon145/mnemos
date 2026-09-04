"""Run one dispatch to the Virtuals compute service and save the
response as UTF-8 JSON, bypassing shell encoding entirely."""
import json
import os
import sys
from pathlib import Path

from core.integrations.virtuals import dispatch_to_virtuals
from core.memory.store import MemoryStore

OUT = Path(__file__).resolve().parent.parent / "docs" / "evidence" / "dispatch.json"
DB = Path(__file__).resolve().parent.parent / ".mnemos" / "project.db"

PROMPT = (
    "You are Mnemos, an agent with durable memory. "
    "Confirm in one line that memory, not context, is your source of truth."
)


def main() -> int:
    store = MemoryStore(DB)
    try:
        result = dispatch_to_virtuals(store, PROMPT)
        response = result.get("response") or {}
        payload = {
            "agent_id": result.get("agent_id"),
            "response_id": response.get("id"),
            "model": response.get("model"),
            "provider": response.get("provider"),
            "content": ((response.get("choices") or [{}])[0].get("message") or {}).get("content", ""),
            "usage": response.get("usage") or {},
            "cost": (response.get("usage") or {}).get("cost"),
        }
        OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
