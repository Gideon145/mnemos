"""One-shot end-to-end flow over the five new capabilities."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from core.agent import RecallEngine
from core.memory.doctor import run_doctor
from core.memory.dream import dream, pending
from core.memory.embed import HashEmbedder, embed_store, hybrid_rank
from core.memory.entities import annotate, index
from core.memory.revision import revise
from core.memory.rewind import rewind
from core.memory.store import MemoryStore


def main() -> int:
    db = Path(tempfile.mkdtemp()) / "memory.db"
    store = MemoryStore(db)
    try:
        # 1. remember with entity annotation
        store.remember_durable("preference", "style", {"value": "I like short direct answers from Alice"})
        found = annotate(store, "preference", "style", "I like short direct answers from Alice")
        print(f"1 remember+entities: {found}")

        # 2. recall with entity boost
        answer = RecallEngine(store).ask("what do I know about Alice")
        lines = answer.answer.splitlines()
        print(f"2 recall boost: found={answer.found_anything}, answer={lines[-1].strip() if lines else answer.answer}")

        # 3. dream
        store.record_event(acted=["asked for a status report"])
        store.record_event(acted=["asked for a status report"])
        report = dream(store)
        print(f"3 dream: scanned={report['events_scanned']} proposals={len(report['proposals'])} pending={[r.get('name') for r in pending(store)]}")

        # 4. revise then rewind
        revise(store, "preference", "style", "I like long answers", reason="flow test")
        creation_ts = str(
            store.recall_durable("preference", "style").get("created_at") or ""
        )
        before = rewind(store, creation_ts + "1")
        after = rewind(store, "2999-01-01T00:00:00Z")
        print(f"4 rewind: before_revision_changed={before['changed_count']} now_changed={after['changed_count']}")
        print(f"   changed entries: {[(c['name'], c['at'], c['now']) for c in after['changed']]}")

        # 5. embed + hybrid + doctor
        summary = embed_store(store, HashEmbedder())
        ranked = hybrid_rank(store, "what does Alice want", HashEmbedder())
        report5 = run_doctor()
        print(f"5 embed: {summary['embedded']} vectors, hybrid top={ranked[0].get('name') if ranked else None}")
        print(f"5 doctor: {len(report5.checks)} checks healthy={report5.healthy}")

        print("ENTITIES:", index(store))
        return 0 if report5.healthy and summary["embedded"] >= 2 else 1
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main())
