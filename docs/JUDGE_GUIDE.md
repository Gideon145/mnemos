# Judge Guide — Mnemos (5 minutes)

Every claim below maps to a file, a test, or a live artifact. No claim on
this page is asserted without one of the three.

## The 60 second version

1. Mnemos stores facts, agreements, lessons, and tasks in Sibyl Memory.
2. A fresh session recalls them and the recall changes what the agent may do.
3. Money moves only when a remembered, delivered agreement covers it.
4. Correcting a memory computes the blast radius, taints dependents, and the
   gate refuses until each is reconsidered.
5. Deleting the memory breaks recall, the gate, and the journal seal.

## Load-bearing map (memory is the critical path)

| Claim | Code | Test |
|---|---|---|
| Durable facts survive sessions | `core/memory/store.py` | `tests/test_memory.py` |
| Recall changes answers, says when empty | `core/agent/recall.py` | `tests/test_recall.py` |
| Gate refuses without a delivered agreement | `core/memory/gate.py` | `tests/test_payments.py` |
| Scar gate vetoes unresolved lessons | `core/memory/gate.py` `_unresolved_scars` | `tests/test_scar_gate.py` |
| Revision taints dependents, closes the gate | `core/memory/revision.py` | `tests/test_revision.py` (19 cases) |
| Reconsider reopens the gate | `core/memory/revision.py` `reconsider` | `tests/test_revision.py` |
| Payment claims block duplicate broadcast | `core/payments/executor.py` `_intent_key` | `tests/test_payments.py` |
| Journal is tamper-evident | `core/memory/seal.py` | `tests/test_seal.py` |
| Deletion empties recall and closes the gate | `core/memory/doctor.py` | `tests/test_doctor.py` |
| Fresh-machine keepsake restores the agent | `core/memory/keepsake.py` | `tests/test_keepsake.py` |
| Tasks survive restarts | `core/memory/tasks.py` | `tests/test_tasks.py` |
| Causal replay | `core/agent/replay.py` | `tests/test_replay.py` |

## Measured, not marketed

`scripts/ablation.py` runs the real gate on seeded trials (12, seed 1337):

| Arm | Allowed | Refused |
|---|---|---|
| Memory on: remembered, delivered agreement | 12 | 0 |
| Memory off: same request, wiped store | 0 | 12 |
| Revision on: suspect until reconsider | 0 | 12 |
| Revision off: same agreement, no suspect check | 12 | 0 |

Reproduce: `python scripts/ablation.py`. Pinned by `tests/test_ablation.py`.

## Live artifacts

- Base mainnet payment from a memory-gated decision: `0x1ed5b2...46d194`
  (Sep 5), plus the original `0xb685f5fd...d68a84`. See `docs/VERIFICATION.md`.
- Virtuals ACP dispatch, billed, with the model honestly refusing the
  no-memory roleplay: `gen-1788586150-ntsOrSusCzLVFjEMdJfE`. See
  `docs/VERIFICATION.md`.
- Hosted MCP endpoint (11 tools, typed outputs):
  `https://mnemos-production-2572.up.railway.app/mcp`
- Live playground: `https://mnemos-production-2572.up.railway.app/`

## Honest limits

- No vector/semantic search. Recall uses Sibyl FTS plus a deterministic
  lexical fallback, on purpose.
- No production authentication on the hosted endpoint. It is a demo surface.
- The hosted memory is shared across visitors, wiped per page load.
- No distributed multi-agent propagation; keepsakes carry state between
  agents.
- Revision is a user-issued command; no auth layer beyond the journal.
