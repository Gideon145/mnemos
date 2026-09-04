# Mnemos — Demo Script (2–5 min, one unedited take)

Scoring target: **recall is table stakes → we show it, then go past it.**
The beats that top the band: **dynamic storage** (an agreement state machine
that drives an on-chain payment gate), **coordination** (handoff to a Virtuals
agent through memory), and the **deletion test**. Every beat ends with what
memory improved, because that is the crux of the scoring.

---

## Beat 0 — Cold open (~20s)

> "Every assistant forgets. Close the tab, lose the context, teach it all
> again tomorrow. Forgetting is a bug. This is Mnemos — an agent whose memory
> is the product. And the memory is yours."

## Beat 1 — Teach (~25s)

```
mnemos remember "I like short, direct answers"
mnemos remember "contractor rate is 40 per hour"
```

> "Two durable facts, written to Sibyl Memory as entities. Recall is the
> floor. What memory improves comes next: these answers cost zero tokens
> forever, because Mnemos never re-explains itself to a model."

## Beat 2 — Dynamic storage: the agreement (~40s)

```
mnemos agree banner-job --with alex --amount 160
mnemos pay banner-job 160
```

> "An agreement entity, state agreed. The payment gate reads it: state is not
> delivered, so the payment is refused. Nothing was broadcast. Memory just
> stopped a premature payment. That is an improved decision, caused by memory."

## Beat 3 — Coordination: handoff through memory (~40s)

```
mnemos advance banner-job --to delegated
mnemos delegate banner-job --to <virtuals-agent-id> --task "design the banner"
mnemos dispatch "design the banner in the remembered style"
```

> "The handoff is written to memory: agent id, task, timestamp. Then the
> remembered agent id is read back and the task is dispatched to the Virtuals
> compute service. Two runtimes, one memory surface. Coordination, not chat."

## Beat 4 — Keepsake + cold start (~35s)

```
mnemos keepsake export mnemos.mne
# close everything, fresh session, fresh machine
mnemos keepsake import mnemos.mne
mnemos ask "how do I like answers? what is my contractor rate?"
```

> "Fresh machine. The agent recalls from memory. Cold start, zero tokens, no
> re-teaching. Memory improved the setup cost from forever to one command."

## Beat 5 — The gate executes, with a real receipt (~30s)

```
mnemos advance banner-job --to delivered
mnemos pay banner-job 160 --live --network mainnet
```

> "Same request as before, but now the agreement is delivered. The gate reads
> memory, checks the amount, and Mnemos signs a real transaction on Base
> mainnet. The on-chain action happened because memory said so. The receipt is
> in the repo."

## Beat 6 — The deletion test (~20s)

```
mnemos doctor
```

> "Delete the store and every gate closes. Recall empties, payments refuse.
> Memory was not a feature — it was the product. Load-bearing, proven."

## Close (~15s)

> "Recall is table stakes. Mnemos adds coordination between agents, a payment
> gate that cannot run without memory, and lessons that veto repeat failures.
> The agent can be wrong. The gate can't."

---

Total ≈ 3m30s. One take, no cuts — exactly what the gate requires.
