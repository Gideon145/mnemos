# Mnemos Build Log

A public record of the build. Each day links to the public X post for that day, so the story can be followed chronologically.

## Day 1 (Sep 1, 2026)

Started the in-window build. Phase 1 memory core was finished and pushed, then the agent layer came together:

- recall engine that answers only from what memory actually holds, and says so when it holds nothing
- tiered store over the Sibyl SDK: durable entities, daily journal, session state
- agreements as a state machine: draft, agreed, delegated, delivered, paid, one step at a time
- payment executor behind the memory gate, dry run by default, Base Sepolia path ready
- keepsakes: portable memory packs with digest verification for cold-start recall
- reflection: repeated journal patterns become proposals you accept or reject
- recap: a deterministic day summary straight from the journal
- CLI for all of it: remember, ask, journal, recap, agree, advance, delegate, pay, keepsake, reflect, proposals, accept, reject, register

34 tests passing. Sibyl SDK pinned to 0.8.0.

Public post: https://x.com/mnemos_agent/status/2094635080257868128

## Day 2 (Sep 2, 2026)

Closed the gaps against the strongest competitor we found, and shipped the failure-memory idea:

- tasks as durable entities: queued, working, blocked, completed, with resume for unfinished work
- replay: the causal chain for any remembered subject, oldest first
- lessons: failures stored with severity, surfaced by recall and recap
- doctor: the deletion test as a command, proves memory is load-bearing
- handoff: one pack carries memory from agent A to agent B
- recall: stemmed tokens and identity triggers so reworded questions still find their facts
- pyproject.toml: real pip install and a mnemos console script
- README rewritten around the load-bearing map

51 tests passing.

Public post: https://x.com/mnemos_agent/status/2094996926517092619

## Day 3 (Sep 3, 2026)

Memory became the authority over real money.

- the payment gate executed a live transaction on Base mainnet: same request refused while the agreement was only agreed, then executed once delivered (block 50812564, link in docs/VERIFICATION.md)
- network flag and a real counterparty payee, so the payment goes to the contractor, not to ourselves
- relational breadcrumbs: mnemos link connects any two durable entities both ways
- docs lead with the three features users actually name: learns you, near-perfect recall, never hallucinates
- pmf case, submission copy, and the readme banner written early

55 tests passing.

Public post: https://x.com/mnemos_agent/status/2095390120341811415

## Day 4 (Sep 4, 2026)

The agent learns from pain, and runs on Virtuals compute.

- scar gate: a high severity lesson linked to an agreement vetoes its payments until resolved
- Virtuals ACP integration: console agent id recorded in memory, tasks dispatched to the OpenAI-compatible compute endpoint, with the legacy GAME SDK path kept as fallback
- first live dispatch captured as evidence: Claude Fable 5 refused the roleplay and stated it has no durable memory, billed 0.01074 USD to the agent wallet
- docs answer the official question: what memory improves (money, decisions, failures, time)
- demo script rewritten around the real CLI, every beat ends with what memory improved
- capture and render scripts turn a dispatch into a branded transcript

65 tests passing.

Public post: https://x.com/mnemos_agent/status/2095726174433325315

## Day 5 (Sep 5, 2026)

The agent's corrections now govern its actions: `mnemos revise`.

- deep research pass across shipped memory stacks, agent governance
  frameworks, and fresh papers to find a missing primitive; the gap was
  correction: nobody turns a corrected memory into an execution gate
- revise: correcting a fact computes the deterministic blast radius of
  that memory — decisions whose journaled sources cite it, entities
  linked to it (two hops), and their payments — and marks them suspect
- reconsider: a suspect entity is reviewed per revision; valid clears
  that taint and reopens the gate, invalid keeps it closed
- the payment gate refuses suspect agreements with an exact reason:
  "agreement 'fencing' is suspect: depends on revised memory
  preference:contractor_rate_is_40; reconsider first"
- append-only history: every superseded value stays in the entity, and
  every revision, suspicion, and review is journaled immutably
- 19-case test matrix: direct, two-hop, unrelated, multi-source,
  re-flag after reconsideration, history immutability, and more
- closest academic work cited honestly in docs/PRIOR_WORK.md
  (arXiv:2608.10502 does post-failure computation recovery, not gating)

84 tests passing.
