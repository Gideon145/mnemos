# Mnemos — Build Phases

Build order: product core in four phases, then external integrations.

## Phase 1 — Memory core (day 1)

- Tiered store over the Sibyl SDK: durable entities, daily journal, session state
- Agreement entities with an explicit state machine
  (draft, agreed, delegated, delivered, paid) riding the entity status field
- Keepsake export/import (portable `.mne` packs)
- Deletion test: remove the store and recall plus gates must fail

## Phase 2 — Agent core (day 2)

- CLI loop: `remember`, `ask`, `agree`, `delegate`, `pay`, `recap`
- Recall engine: classify, first-pass recall, confidence, honest
  "I don't remember" when the store has nothing
- Daily recap via the x402-gated summarizer shipped with the SDK
- Reflection: repeated patterns become proposed standing rules

## Phase 3 — Gates and actions (day 3)

- Payment gate: only a remembered agreement in the delivered state can execute
- x402/USDC payment executor on Base, testnet first
- Delegation records written to memory (coordination surface)

## Phase 4 — Product shell (day 4)

- Configuration, error handling, deterministic demo tooling
- Final README with the load-bearing walkthrough
- Public posts scheduled alongside each milestone

## Integration phase (days 5+)

- Virtuals: register Mnemos and run a live delegation demo
- Base: mainnet-ready payment flow
- MCP: expose Mnemos memory as an MCP server
- x402-gated summarizer for recaps (already in the SDK)
