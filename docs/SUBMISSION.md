# Submission copy (draft)

Ready-to-paste text for the hackathon entry form. Written Sep 2 so the
final day is a copy job, not a writing job.

## Repo

https://github.com/Gideon145/mnemos

## Primitives to tick

- recall
- entities
- temporal / time-travel
- summarization
- reflection
- consolidation

(Semantic search intentionally NOT ticked: Mnemos uses Sibyl FTS plus a
deterministic lexical fallback, not embeddings.)

## What breaks when memory is deleted

Delete the Sibyl database and every core function stops:

- recall returns nothing and the agent says it does not remember
- agreements disappear, so the payment gate refuses everything
- keepsakes and tasks are gone, so nothing can resume
- replay finds no causal chain
- `mnemos doctor` demonstrates all of this on demand

There is no fallback path. The agent holds no in-process copy of
durable facts. Memory is the single source of truth, and removing it is
the deletion test proving the build is load-bearing.

## Memory walkthrough

1. The agent is taught preferences and a contractor agreement, both
   written to Sibyl as durable entities.
2. The agreement advances one state at a time, each transition
   journaled.
3. A payment is attempted while the agreement is only agreed. The gate
   refuses it. Nothing is broadcast.
4. The agreement reaches delivered. The same payment now passes, and
   the agent signs and broadcasts a real transaction on Base mainnet.
   The agreement advances to paid and the tx hash is journaled.
5. A keepsake exports everything. A fresh agent on a fresh machine
   imports it and recalls the same facts.
6. The journal is reflected into proposals, which are accepted or
   rejected explicitly.
7. `mnemos doctor` deletes the memory and shows recall emptying and the
   gate closing.

## How memory improves the build

- Money: recall and keepsake cold starts cost zero model calls; the same
  fact costs nothing to re-read forever.
- Decisions: the gate refused a payment while the agreement was agreed,
  then executed the same request once delivered. The decision changed
  because memory state changed.
- Failures: a high severity lesson vetoes linked payments until
  resolved, so repeat mistakes are blocked by construction.
- Time: tasks are durable and resume lists unfinished work.

## The two partner stacks

- Base: a live mainnet transaction authorized by remembered agreement
  state, linked in docs/VERIFICATION.md.
- Virtuals: the agent's identity and delegation records live in memory;
  live delegation execution through Virtuals (see docs).
