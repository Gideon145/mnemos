# Mnemos — Demo Script (2–5 min, one unedited take)

Scoring target: **recall is table stakes → we show it, then go past it.**
The two beats that top the band: **coordination** (multi-agent handoff through
memory) and **dynamic storage** (an agreement state machine that drives an
on-chain payment gate). The deletion test closes it.

---

## Beat 0 — Cold open (~20s)

> "Every assistant forgets. Close the tab, lose the context, teach it all again
> tomorrow. Forgetting is a bug. This is Mnemos — an agent whose memory is the
> product. And the memory is yours."

## Beat 1 — Teach (~30s)

Terminal:

```
mnemos remember "I like short, direct answers"
mnemos remember "contractor rate is $40/hr"
mnemos remember "I ship on Fridays"
```

> "Three durable facts, written to Sibyl Memory as entities. That's the floor —
> recall. Watch what we build on top of it."

## Beat 2 — Dynamic storage: the agreement state machine (~45s)

> "Memory here isn't a notepad. It's live state."

```
mnemos agree "designer alex" "banner job" "60 usdc fixed" "use my remembered style guide"
```

> "Mnemos creates an agreement entity — state `draft` — and links it to the
> remembered style guide. I confirm, state flips to `agreed`. The agreement
> lives in memory, and its state changes as the world changes. Delete the store
> and the agreement itself is gone."

## Beat 3 — Coordination: handoff through memory (~45s)

> "Now the coordination beat. Mnemos delegates the job to a specialist agent on
> Virtuals."

```
mnemos delegate banner-job to @designer-agent
```

> "The handoff is written to memory: task state `delegated`, agent id, timestamp.
> The specialist works, returns — Mnemos writes the outcome to the journal and
> updates the agreement to `delivered`. Two agents, one shared memory surface.
> That's coordination, not chat."

## Beat 4 — Keepsake + cold start (~40s)

```
mnemos keepsake export mnemos.mne
# close everything, fresh session / fresh machine
mnemos keepsake import mnemos.mne
mnemos ask "how do I like answers? what's my contractor rate?"
```

> "Fresh session. The agent recalls from Sibyl. The floor, done cold."

## Beat 5 — The gate reads memory, then acts (~30s)

```
mnemos pay "banner job"
```

> "Mnemos reads the agreement from memory — amount, recipient, state. State is
> `delivered`, so it executes the x402 payment on Base: sixty USDC. The on-chain
> action happened *because memory said so*. The agent proposes; the remembered
> agreement gates it."

## Beat 6 — The deletion test (~20s)

> "Now the test your rules actually ask for."

Remove the Sibyl store. Repeat the questions. Nothing. Try the payment:

> "No agreement found. Gate closed. Memory wasn't a feature — it was the
> product. Load-bearing, proven on camera."

## Close (~15s)

> "Recall is table stakes. We built coordination between agents and a payment
> gate that cannot run without memory. The oracle has a memory now — and the
> memories belong to you."

---

Total ≈ 3m30s. One take, no cuts — exactly what the gate requires.
