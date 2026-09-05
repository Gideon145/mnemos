# Mnemos — Memory Model

## Principles

1. **Memory is the product.** Every core feature reads or writes memory; no
   core feature works without it.
2. **The user owns the memory.** All durable state is portable via Keepsakes.
3. **Recall over inference.** Mnemos answers from what it stored, not from
   guessing; it says when it does not know.

## Tiers

### Durable tier (Sibyl — primary namespace)

- User preferences ("short direct answers")
- Agreements ("contractor rate is $40/hr", "ship on Fridays")
- Identity and relationships
- Learned corrections

Written via explicit `remember()` calls; read via `recall()` on every relevant
turn. This tier is the **deletion-test dependency**: without it, Mnemos cannot
resolve any agreement or preference.

### Daily tier (Sibyl — date-scoped namespace)

- What happened and what was decided today
- Short-term context that ages out
- Feed for the daily recap ("what did we do yesterday?")

### Session tier (local)

- The current conversation's working set
- Never load-bearing; dropped at end of session

## Keepsake format (`.mne`)

```json
{
  "mnemos_version": "0.1.0",
  "exported_at": "2026-09-05T12:00:00Z",
  "namespaces": {
    "durable": [ { "key": "...", "value": "...", "updated_at": "..." } ],
    "daily":   [ { "key": "...", "value": "...", "updated_at": "..." } ]
  },
  "signature": "0x..."
}
```

Portable, human-inspectable, signed by the owner key. Import merges with
conflict metadata and never silently overwrites newer facts.

## Recall flow

```
question ──► classify (preference | agreement | decision | fact)
        ──► sibyl recall (first pass)
        ──► confidence check
             ├── high  ──► answer, cite tier
             └── low   ──► adaptive follow-up (search namespace, widen window)
                          └── still low ──► "I don't remember" (never fabricate)
```

## Agreement state machine (dynamic storage)

Agreements are the flagship dynamic-storage pattern. One entity per agreement,
with `state` evolving on the critical path:

```
draft ──confirm──► agreed ──delegate──► delegated ──outcome──► delivered ──pay──► paid
```

- Each transition = `set_entity` update + `write_event` journal entry
- The payment gate reads `state` and `amount` from memory at execution time
- No memory → no agreement → no payment (the deletion test)
- References link agreements to remembered preferences ("use my remembered
  style guide") so memory entities compose, they don't just sit

## Revision (correction with blast radius)

When a fact is corrected, the past does not silently disappear. `revise`
walks the recorded dependencies and marks everything contaminated:

1. The entity's old value is appended to `body.history` (append-only) and
   the new value is written.
2. A revision event is journaled and its event id becomes the revision id.
3. Blast radius (deterministic, no model):
   - decisions: journal events whose `evaluated.sources` cite the fact;
   - one hop: agreements/tasks whose `body.linked` contains the fact;
   - two hops: entities linked from an affected entity.
4. Each affected entity gets a `tainted_by` entry carrying the revision id.
5. The payment gate refuses suspect agreements with the exact reason until
   `reconsider` reviews each revision: `valid` clears that taint, `invalid`
   keeps the gate closed. Reviews are journaled per revision id.

An entity is suspect while any taint entry lacks a valid review, so two
revisions of the same fact need two reconsiderations. Nothing is deleted:
history, revisions, suspicion, and reviews are all journal records.

## Coordination

Two or more agents (Mnemos + Virtuals specialists) share state exclusively
through Sibyl tiers. Task state, handoffs, and outcomes are memory records.
There is no coordination path outside memory.

## Anti-goals

- No hidden cloud copy of user memory
- No recall answers without a stored source
- No feature that works better with memory deleted (that would fail the gate)
