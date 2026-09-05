# Mnemos

> **Forgetting is a bug. Mnemos is the fix.**

Mnemos is a local-first personal agent whose durable memory runs on
[Sibyl Memory](https://docs.sibyllabs.org/memory/). Everything you tell it —
preferences, agreements, lessons, tasks — lives in memory you own, and you can
take it anywhere.

![Mnemos banner](docs/images/banner.jpg)

<p align="center">
  <a href="https://mnemos-production-2572.up.railway.app/">
    <img src="https://img.shields.io/badge/LIVE-playground-3CB878?style=for-the-badge" alt="Live playground" />
  </a>
  <a href="https://mnemos-production-2572.up.railway.app/mcp">
    <img src="https://img.shields.io/badge/MCP-hosted_endpoint-0f766e?style=for-the-badge" alt="Hosted MCP" />
  </a>
  <a href="https://smithery.ai/servers/mnemos/mnemos">
    <img src="https://img.shields.io/badge/Smithery-mnemos%2Fmnemos-FF6B00?style=for-the-badge" alt="Smithery" />
  </a>
  <a href="https://x.com/mnemos_agent">
    <img src="https://img.shields.io/badge/X-@mnemos__agent-1DA1F2?style=for-the-badge&logo=x&logoColor=white" alt="X" />
  </a>
  <a href="https://basescan.org/tx/0x1ed5b2674123e70a4de87ca9ceebad38f961fc6612c2206bb1456356ae46d194">
    <img src="https://img.shields.io/badge/Base-mainnet_tx-0052FF?style=for-the-badge" alt="Base mainnet tx" />
  </a>
  <a href="docs/VERIFICATION.md">
    <img src="https://img.shields.io/badge/Virtuals-ACP_live_dispatch-8B5CF6?style=for-the-badge" alt="Virtuals ACP" />
  </a>
</p>

Built for the Sibyl Memory Hackathon, Sep 1 to 10, 2026. One design
principle throughout: recall answers only from what memory actually
holds, and nothing acts until memory says so. A forgotten fact is
answered honestly, a refused payment is journaled as loudly as a paid
one, and the journal is sealed with a hash chain anyone can verify.

## Verified live

Both partner stacks ran on the final code, on real rails. Full captures and
reproduction steps: [docs/VERIFICATION.md](docs/VERIFICATION.md).

| Stack | What ran | Live proof |
|---|---|---|
| Base | The payment gate read a remembered agreement, refused it while the agreement was not delivered, then executed it once delivered | [mainnet tx `0x1ed5b2...46d194`](https://basescan.org/tx/0x1ed5b2674123e70a4de87ca9ceebad38f961fc6612c2206bb1456356ae46d194), Sep 5, status 1 |
| Virtuals | ACP compute dispatch from a remembered console agent id on `compute.virtuals.io/v1` | `anthropic/claude-fable-5`, response `gen-1788586150-...`, 256 tokens, $0.01104 billed |

## Table of Contents

- [Verified live](#verified-live)
- [Why](#why)
- [What memory improves](#what-memory-improves)
- [What it does](#what-it-does)
- [Use Mnemos from any agent (MCP)](#use-mnemos-from-any-agent-mcp)
- [Endpoints](#endpoints)
- [Install](#install)
- [The load-bearing map](#the-load-bearing-map)
- [Testing](#testing)
- [The proof in one take](#the-proof-in-one-take)
- [The gate and payment lifecycle](#the-gate-and-payment-lifecycle)
- [Measured](#measured)
- [Architecture](#architecture)
- [Project layout](#project-layout)
- [Invariants](#invariants)
- [Honest status](#honest-status)
- [Building in public](#building-in-public)
- [License](#license)

### Supplemental docs

- ⚖️ [Judge Guide](docs/JUDGE_GUIDE.md): 5-minute review, every claim mapped to file, test, and live artifact
- ✅ [Verification](docs/VERIFICATION.md): Base mainnet tx + Virtuals ACP proof, reproducible
- 🏛️ [Architecture](docs/ARCHITECTURE.md): full system design and data flow
- 🧠 [Memory Model](docs/MEMORY_MODEL.md): entities, journals, gates
- 📈 [PMF](docs/PMF.md): why Mnemos has to exist
- 📐 [Build Plan](docs/PLAN.md): the plan, day by day
- 📆 [Build Phases](docs/PHASES.md): phase-by-phase breakdown
- 🧾 [Build Log](docs/BUILD_LOG.md): what was built and when
- 🎬 [Demo Script](docs/DEMO_SCRIPT.md): 2 to 5 minute, one unedited take
- 📤 [Public Submission](docs/PUBLIC_SUBMISSION.md): submission status
- ⏮️ [Prior Work](docs/PRIOR_WORK.md): prior work declaration

## Why

Old computers had almost no RAM, and memory is what held them back,
not CPU power. The same is happening with agents: models keep getting
smarter while memory still gets lost or costs tokens.

Mnemos is the RAM upgrade for agents. The full case is in
[docs/PMF.md](docs/PMF.md).

## What memory improves

Memory is not the feature. What memory changes is the feature.

- **Money.** Recall answers without a single model call. The same fact
  costs zero tokens forever, and a keepsake restores a full agent with no
  re-teaching.
- **Decisions.** The payment gate refused a real request while the
  agreement was only agreed, then executed it once delivered. Same
  request, opposite outcomes, caused by memory state alone.
- **Failures.** A high severity lesson linked to an agreement vetoes its
  payments until the lesson is resolved. Mistakes stop repeating.
- **Corrections.** When a remembered fact is revised, everything that
  depended on it becomes suspect and the payment gate closes until each
  affected item is explicitly reconsidered. A wrong memory can no longer
  keep paying out.
- **Time.** Tasks survive restarts and `resume` lists what is left, so
  work never dies with the session.

## What it does

- **Remembers you, honestly.** Recall answers only from what memory actually
  holds, and says so when it holds nothing. No invented memories, ever.
- **Agreements with teeth.** A state machine (`draft -> agreed -> delegated ->
  delivered -> paid`) that moves one step at a time, never backward.
- **Memory-gated payments.** Nothing pays out unless a remembered, delivered
  agreement covers the amount. The gate reads memory before it allows anything.
- **Keepsakes.** One command exports everything into a portable `.mne` pack.
  A fresh agent on a fresh machine imports it and remembers you. Packs are
  plain JSON with a sha256 digest: commit them to git like any backup.
- **Lessons.** Failures are stored with severity, so the same mistake stays
  wrong only once.
- **Revision with blast radius.** `revise` corrects a fact, computes what
  depended on it deterministically, and marks affected agreements and tasks
  suspect. The payment gate refuses them until `reconsider` reviews each one.
  History is append-only: every superseded value stays in the journal.
- **Tasks that survive restarts.** `resume` lists unfinished work, work first.
- **Causal replay.** Every write, recall, and refusal is journaled. `replay`
  shows the chain that changed a decision.
- **The deletion test, on demand.** `doctor` proves memory is load-bearing.

## Use Mnemos from any agent (MCP)

`mnemos mcp` serves the same 12 tools (remember, ask, lessons, tasks, replay,
revise, blast, reconsider, suspect, reset, and more) to any MCP client over stdio.

```bash
pip install '.[mcp]'
mnemos mcp --db ~/.mnemos/memory.db
```

Claude Desktop / VS Code / Cursor:

```json
{
  "mcpServers": {
    "mnemos": {
      "command": "mnemos",
      "args": ["mcp", "--db", "C:\\Users\\you\\.mnemos\\memory.db"]
    }
  }
}
```

Remote / hosted: `mnemos mcp --http` serves streamable HTTP on port 8000
(`/mcp`), which is what the Dockerfile and `smithery.yaml` deploy. Live
endpoints: [Railway](https://mnemos-production-2572.up.railway.app/mcp) and
[Smithery](https://smithery.ai/servers/mnemos/mnemos).

## Endpoints

The hosted app at https://mnemos-production-2572.up.railway.app serves
everything:

| Path | What |
|---|---|
| `/` | The live playground site |
| `/chat` | Agentic chat. Facts are extracted and stored before the model answers |
| `/mcp` | Streamable HTTP MCP: 12 tools with typed outputs |
| `/assets` `/css` `/js` | Static site assets |

CORS is open on the hosted app, the MCP client reconnects automatically
on session expiry, and `mnemos mcp` runs the same surface over stdio
locally.

## Install

```bash
pip install .
mnemos --db ~/.mnemos/memory.db remember "I like short direct answers"
mnemos ask "how do I like answers?"
```

## The load-bearing map

Every capability below breaks without Sibyl Memory. Judges can reach any call
site in under two minutes.

| Capability | Command | Where the memory call lives |
|---|---|---|
| Durable facts | `mnemos remember` / `ask` | `core/memory/store.py` |
| Honest recall | `mnemos ask` | `core/agent/recall.py` |
| Agreements | `mnemos agree` / `advance` / `delegate` | `core/memory/agreement.py` |
| Payment gate | `mnemos pay` | `core/memory/gate.py`, `core/payments/executor.py` |
| Portable memory | `mnemos keepsake export/import` | `core/memory/keepsake.py` |
| Lessons | `mnemos learn` / `lessons` | `core/memory/lessons.py` |
| Tasks | `mnemos task` / `work` / `block` / `resume` | `core/memory/tasks.py` |
| Causal replay | `mnemos replay` | `core/agent/replay.py` |
| Day summary | `mnemos recap` | `core/agent/recap.py` |
| Reflection | `mnemos reflect` / `proposals` / `accept` | `core/memory/reflection.py` |
| Revision | `mnemos revise` / `blast` / `reconsider` / `suspect` | `core/memory/revision.py` |
| MCP surface | `mnemos mcp` | `core/mcp.py` |
| Deletion test | `mnemos doctor` | `core/memory/doctor.py` |

## Testing

```bash
python -m pytest tests -q      # 111 passing
```

| Suite | Tests | Focus |
|---|---|---|
| `test_revision` | 19 | blast radius, suspect gates, reconsider |
| `test_mcp` | 14 | the 12 tools over stdio, fact extraction, reset |
| `test_memory` | 10 | tiers, agreements, keepsakes, gates, deletion test |
| `test_virtuals` | 9 | registration and dispatch, memory write-back |
| `test_recall` | 7 | recall honesty, including the empty-memory case |
| `test_payments` | 6 | pending claims, duplicate refusal, paid only on receipt |
| `test_reflection` | 5 | journal patterns become proposals, not preferences |
| `test_tasks` | 5 | work that survives a restart |
| `test_keepsake` | 4 | a fresh machine gets the agent back |
| `test_lessons` | 4 | failures remembered so they are not repeated |
| `test_links` | 4 | breadcrumbs between durable entities |
| `test_replay` | 4 | the causal chain as the journal recorded it |
| `test_recap` | 4 | the journal reported back as an audit |
| `test_scar_gate` | 4 | memory of failure vetoes future actions |
| `test_seal` | 4 | journal seal, deletions break the chain |
| `test_delegation` | 3 | handing work to another agent, remembered |
| `test_doctor` | 2 | the deletion test, on demand |
| `test_handoff` | 2 | give another agent your memory, on purpose |
| `test_ablation` | 1 | pins the measured numbers below |

The suites are written from the attacker's side: duplicate payments,
tampered journals, suspected agreements, deleted memory.

## The proof in one take

```bash
mnemos remember "I like short direct answers; contractor rate is 40 per hour"
mnemos agree contractor --with alice --amount 160
mnemos delegate contractor --to agent-42 --task "fix the fence"
mnemos keepsake export my-mnemos.mne
# fresh machine, fresh install
mnemos keepsake import my-mnemos.mne
mnemos ask "how do I like answers and what is the contractor rate"
mnemos advance contractor --to delivered
mnemos pay contractor 160
mnemos revise preference contractor_rate_is_40_per_hour 60 --reason corrected
mnemos pay contractor 160   # refused: agreement is suspect, reconsider first
mnemos reconsider agreement contractor --valid --reason "fixed price"
mnemos pay contractor 160   # gate reopened, payment sent
mnemos doctor
```

`pay` is dry-run by default and journals everything. With `--live` and
`MNEMOS_PAYER_KEY` set, it submits a real transaction on Base.

A live Base mainnet payment from a memory-gated decision is recorded in
[docs/VERIFICATION.md](docs/VERIFICATION.md), with the explorer link.

## The gate and payment lifecycle

Nothing pays out unless a remembered, delivered agreement covers the
amount.

- **One state at a time.** Agreements move `draft -> agreed -> delegated
  -> delivered -> paid`, one transition per command, never backward.
  Every transition is journaled.
- **The gate reads memory first.** `pay` asks the deterministic gate
  whether a delivered agreement covers the amount before any executor
  is handed an intent.
- **Claim before broadcast.** The intent is claimed in working state
  with compare-and-set before any signature exists. A pending or paid
  claim refuses duplicates, so the same intent can never be broadcast
  twice. A submit exception marks the claim failed for a clean retry;
  only a receipt marks it paid.
- **Dry-run by default.** `pay` journals the intent and sends nothing
  unless `--live` and `MNEMOS_PAYER_KEY` are set. Refusals are journaled
  like fills, so every stand-down is replayable with `mnemos replay`.

## Measured

Seeded ablation, 12 trials per arm, all arms running the real gate code
on temporary databases (`scripts/ablation.py`, pinned by
`tests/test_ablation.py`, raw results in `docs/evidence/ablation.json`).

| Arm | Payments allowed | Payments refused |
|---|---|---|
| Memory on | 12 | 0 |
| Memory off (memory deleted) | 0 | 12 |
| Revision on, while suspect | 0 | 12 |
| Revision on, after reconsider | 12 | 0 |
| Revision off (counterfactual, no suspect check) | 12 | 0 |

The revision-off arm is a counterfactual of the same delivered agreement
without the suspect check, so the difference is the revision gate alone.

## Architecture

```
you / any MCP client
        |
        v
   playground & hosted MCP   -------- stdio: mnemos mcp
        |
        v
     core (one memory path)
        |        |
        |        +--- recall engine (FTS + lexical, honest empty answer)
        |        +--- agreements (draft -> agreed -> delegated -> delivered -> paid)
        |        +--- lessons (severity + scar gate)
        |        +--- revision (blast radius -> suspect -> reconsider)
        |        +--- keepsakes (.mne portable packs)
        |        +--- journal seal (tamper-evident hash chain)
        |
   Sibyl Memory        PostgreSQL-free, local SQLite + FTS5
        |
        +----------> payment gate ----------> Base (mainnet, verified tx)
        +----------> dispatch ---------------> Virtuals ACP (live, billed)
```

## Project layout

```
core/
  mcp.py                12 tools, agentic chat, static site server
  cli.py                the command line surface
  agent/
    recall.py           FTS + lexical recall, honest empty answer
    recap.py            deterministic day summary from the journal
    replay.py           causal replay of every write and refusal
  memory/
    store.py            durable entities on Sibyl Memory
    agreement.py        agreements, one state at a time
    gate.py             deterministic gates, memory read first
    lessons.py          failures with severity
    tasks.py            tasks that survive restarts
    keepsake.py         portable .mne packs with sha256 digest
    revision.py         revise, blast radius, suspect, reconsider
    seal.py             journal seal hash chain
    doctor.py           the deletion test, on demand
    handoff.py          give another agent your memory
    links.py            relational breadcrumbs between entities
    reflection.py       journal patterns become proposed preferences
  payments/
    executor.py         dry-run and Base executors, claim-before-broadcast
  integrations/
    virtuals.py         Virtuals registration and dispatch, memory write-back
scripts/                 ablation, evidence capture, deploy checks
site/                    the static playground site
tests/                   111 tests
docs/                    all the supplemental docs
```

## Invariants

Properties that must hold or the premise collapses. All are covered by
tests.

- Recall never invents. An empty store yields an honest empty answer.
- No payment without a remembered, delivered agreement covering the
  amount.
- One transition per command. State never moves backward.
- An intent is claimed in memory before any signature exists, so it
  cannot broadcast twice.
- A revised fact makes everything that depended on it suspect, and the
  gate stays closed until each item is reconsidered.
- Appending, editing, or deleting journal events breaks the seal.
- A keepsake pack restores a fresh agent on a fresh machine.

## Honest status

| Area | Status | Proof |
|---|---|---|
| Memory core, recall, gate, lessons, tasks, revision | shipped, 111 tests green | `pytest` |
| Base mainnet payment from a gated decision | verified live | `docs/VERIFICATION.md` |
| Virtuals ACP dispatch | verified live, billed | `docs/VERIFICATION.md` |
| Hosted MCP endpoint, Smithery, Railway | live | badges above |
| Playground with agentic chat | live | badge above |
| Tamper-evident journal seal | shipped | `mnemos seal`, `mnemos doctor` |
| Pending payment claims | shipped | `tests/test_payments.py` |
| Measured ablation numbers | shipped, seeded | `scripts/ablation.py` |
| Demo video | pending | script in `docs/DEMO_SCRIPT.md` |
| Semantic/vector search | deliberately not shipped | recall is FTS + deterministic fallback |
| Production auth on the hosted endpoint | deliberately not claimed | demo surface |

## Building in public

One post per build day on X at
[@mnemos_agent](https://x.com/mnemos_agent), each pointing at what
shipped that day. The ground rule is the same as the README: a post
claims only what is live and verified, and links the live playground
and the hosted MCP.

## License

MIT — see [LICENSE](LICENSE).
