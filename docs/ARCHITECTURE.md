# Mnemos — Architecture

## System overview

```
┌────────────────────────────────────────────────────────────┐
│  Mnemos agent                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ chat loop    │  │ recall engine│  │ action executor  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │ write/read      │ recall/search        │ act      │
│         ▼                 ▼                      ▼          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Memory layer (critical path)                        │   │
│  │  durable tier ──► Sibyl Memory (system of record)   │   │
│  │  daily tier    ──► Sibyl (scoped namespace)         │   │
│  │  session tier  ──► local working set               │   │
│  └─────────────────────────────────────────────────────┘   │
│         │ Keepsake export/import                            │
│         ▼                                                   │
│  ┌────────────┐      ┌──────────────┐      ┌─────────────┐ │
│  │ Base       │      │ Virtuals     │      │ Keepsake    │ │
│  │ wallet/x402│      │ registration │      │ packs (.mne)│ │
│  └────────────┘      └──────────────┘      └─────────────┘ │
└────────────────────────────────────────────────────────────┘
```

## Components

### 1. Memory layer — the critical path

Three tiers, all with explicit read/write call sites:

| Tier | Store | What lives there | Critical path |
|---|---|---|---|
| **Durable** | Sibyl Memory | Facts, preferences, agreements, identity | `recall()`, `remember()`, payment terms |
| **Daily** | Sibyl Memory (scoped) | Day-to-day context, decisions | context resolution |
| **Session** | Local only | Working set for the current turn | none (safe to drop) |

**Deletion test:** removing the Sibyl layer breaks `recall()` for durable facts,
so agreements cannot be resolved and remembered payments cannot fire. Memory is
load-bearing by construction — there is no fallback path that restores durable
recall without Sibyl.

### 2. Recall engine

1. Query routing: environment facts → durable tier, personal history → durable tier,
   recent decisions → daily tier.
2. First-pass recall from Sibyl, re-rank, adaptive follow-up when confidence is low.
3. Grounded answers cite which tier produced the answer (auditable).

### 3. Keepsakes

- Export: serializes durable + daily namespaces into a portable pack (`.mne`),
  signed with the owner key.
- Import: merges into a fresh Sibyl instance with conflict metadata (source,
  exported-at, version).
- Keepsakes are plain structured files — the memory is the artifact, owned by
  the user, not by a vendor.

### 4. Action executor (Base)

- Mnemos holds a Base account; actions are gated by memory:
  a remembered agreement must exist before a payment can be proposed.
- x402/USDC payments: read terms from durable tier → build tx → user confirm.
- B20 reads for onchain context answers.

### 5. Virtuals integration

- Mnemos registers as a transacting agent on Virtuals Protocol.
- Delegation: specialist agents are remembered (address, capability, outcome
  history) in the durable tier; outcomes are written back after each job.

## Directory layout (planned)

```
mnemos/
├── core/
│   ├── agent/            # chat loop, planning
│   ├── memory/           # tiers, recall, sibyl connector
│   ├── keepsake/         # export/import (.mne)
│   └── actions/          # base/x402 executor, gates
├── cli/                  # mnemos CLI
├── tests/                # unit + deletion-test harness
├── docs/
└── scripts/
```
