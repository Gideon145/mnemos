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
