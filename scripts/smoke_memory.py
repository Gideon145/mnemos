"""Smoke test for the Sibyl Memory SDK — verifies the integration surface
Mnemos builds on: entities, state, journal, search, and persistence across
reopen (the cold-start property the demo depends on)."""
import json
import tempfile
from pathlib import Path

from sibyl_memory_client import MemoryClient


def main() -> None:
    db_path = Path(tempfile.mkdtemp(prefix="mnemos-smoke-")) / "memory.db"
    print(f"[1] opening local store at {db_path}")

    memory = MemoryClient.local(str(db_path))

    # HOT state
    memory.set_state("session", {"mode": "short-answers"})
    assert memory.get_state("session")["body"] == {"mode": "short-answers"}
    print("[2] state set/get ok")

    # WARM entities (durable facts)
    memory.set_entity("preference", "answer-style", {"value": "short, direct"})
    memory.set_entity("agreement", "contractor-rate", {"rate_usd_hr": 40, "name": "alex"})
    got = memory.get_entity("preference", "answer-style")
    assert got["body"]["value"] == "short, direct"
    assert got["category"] == "preference"
    print("[3] entity set/get ok ->", got["body"])

    # COLD journal
    memory.write_event(acted=["remembered answer-style", "stored contractor-rate"])
    events = memory.read_events()
    assert len(events) >= 1
    print(f"[4] journal write/read ok ({len(events)} event(s))")

    # FTS search across everything
    hits = memory.search_entities("contractor")
    assert len(hits) >= 1
    print(f"[5] search ok -> {len(hits)} hit(s) for 'contractor'")

    # Persistence across reopen (the cold-start beat)
    del memory
    memory2 = MemoryClient.local(str(db_path))
    recalled = memory2.get_entity("agreement", "contractor-rate")
    assert recalled["body"]["rate_usd_hr"] == 40
    print(f"[6] cold-start recall ok -> {recalled['body']}")

    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
