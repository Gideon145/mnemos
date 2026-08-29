# Mnemos

> **Forgetting is a bug. Mnemos is the fix.**

Mnemos is a local-first personal AI agent whose durable memory runs on
[Sibyl Memory](https://docs.sibyllabs.org/memory/). Everything you tell it —
preferences, agreements, decisions, tastes — lives in a memory you own, and you
can take it anywhere.

Built for the **Sibyl Labs Hackathon** (build window Sep 1–10, 2026).
Team: **The Muses**.

## What it does

- **Remembers you.** Durable facts, day-to-day context, and decisions are
  written to Sibyl Memory and recalled across sessions and machines.
- **Keepsakes.** One-command portable memory packs. Export what Mnemos has
  learned, import it anywhere, and a fresh agent recalls you instantly.
- **Acts on memory.** Mnemos holds an onchain wallet on Base and executes
  x402/USDC payments from remembered agreements — "pay him $40/hr for 4 hours,
  as we agreed."
- **Runs as an agent.** Registered as a transacting agent on Virtuals Protocol,
  able to delegate to specialist agents and remember the outcomes.

## Where memory is load-bearing

Sibyl Memory is on the critical path of every core function. Delete the Sibyl
layer and Mnemos cannot recall preferences, cannot resolve agreements, and
cannot execute remembered payments. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
for the exact read/write call sites.

**Past table stakes:** recall is the floor. Mnemos also runs a memory-resident
**agreement state machine** (dynamic storage: `draft → agreed → delegated →
delivered → paid`) and a **coordination surface** where Mnemos and specialist
agents hand work off through memory alone. The payment gate executes only when
the remembered agreement says so.

## Stacks

| Stack | Role |
|---|---|
| **Sibyl Memory** | Durable memory system of record (mandatory core) |
| **Base** | Deployment + onchain agent actions (x402/USDC, B20 reads) |
| **Virtuals Protocol** | Agent runtime, registration, coordination |

## Quick links

- [Architecture](docs/ARCHITECTURE.md)
- [Memory model](docs/MEMORY_MODEL.md)
- [Build plan](docs/PLAN.md)
- [Prior work declaration](docs/PRIOR_WORK.md)

## License

MIT — see [LICENSE](LICENSE).
