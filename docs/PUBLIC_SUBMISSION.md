# Mnemos — Public Submission

Team: The Muses
Repo: https://github.com/Gideon145/mnemos
Live: https://mnemos-production-2572.up.railway.app/ (playground, hosted MCP)
Build window: Sep 1-10, 2026

## What breaks when memory is deleted

Delete the Sibyl database and every core function stops:

- recall returns nothing and the agent says it does not remember
- agreements disappear, so the payment gate refuses everything
- revision taints and reconsideration state vanish with the entities
- the journal seal cannot verify against a wiped store
- keepsakes and tasks are gone, so nothing can resume
- `mnemos doctor` demonstrates all of this on demand

There is no fallback path. The agent holds no in-process copy of durable
facts. Memory is the single source of truth, and removing it is the
deletion test proving the build is load-bearing.

## Primitives shipped

recall, entities, temporal (timeline + replay + as-of journal), summarization
(recap), reflection (journal to proposals), consolidation (keepsake + handoff),
correction/revision (blast radius + suspect + reconsider), dynamic storage
(agreement state machine), coordination (MCP, handoff), payments gated by
memory on Base, Virtuals ACP dispatch.

## Honest status

| Area | Status |
|---|---|
| Memory core, recall, gate, lessons, tasks, revision | shipped, 110 tests green |
| Base mainnet payment from a gated decision | verified live (2 txs, docs/VERIFICATION.md) |
| Virtuals ACP dispatch | verified live, billed (docs/VERIFICATION.md) |
| Hosted MCP endpoint, Smithery, Railway | live |
| Playground with agentic chat | live |
| Tamper-evident journal seal | shipped, doctor-checked |
| Pending payment claims | shipped, tested |
| Semantic/vector search | deliberately not shipped |
| Production auth on the hosted endpoint | deliberately not claimed |
| Demo video | not yet recorded; script finalized in docs/DEMO_SCRIPT.md (7 beats) |

## Prior work

All code was written during the build window. The Sibyl Memory SDK, Base,
and Virtuals are used per their public docs. The revision primitive was
designed against published research; the closest work (arXiv:2608.10502)
does post-failure computation recovery, not execution gating. See
docs/PRIOR_WORK.md.
