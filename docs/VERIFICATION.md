# Verification: memory authorizes real money

The Base partner stack is verified by a live transaction on Base
mainnet. The payment gate read a remembered agreement, refused while the
agreement was not delivered, and executed once it was.

## The transaction

- Explorer: https://basescan.org/tx/0xb685f5fd1c9aa52f356d1c62bdf29776ace0355e59004b037d0017e7e6d68a84
- Network: Base mainnet (chain id 8453), block 50812564
- From (Mnemos payer): 0x800709d50ccb0780DF35670D04d584B95adC7ef7
- To (contractor): 0xFb50Ae86438Ad67bb382d63fB1881302316BD76b
- Value: 160 gwei, status 1, 21000 gas

An earlier proof transaction from the same flow: https://basescan.org/tx/0x6c4688248c06d91ef23548d7916124737aef981e6564c73df8e491808e8fa6bf

## Fresh verification run (Sep 5)

The same flow was re-run end to end on the final code to prove the
stack still gates real money after the revision work:

- Explorer: https://basescan.org/tx/0x1ed5b2674123e70a4de87ca9ceebad38f961fc6612c2206bb1456356ae46d194
- Agreement `hardening`, amount 50, state advanced to `delivered`
  through the state machine, then paid live on mainnet.
- Capture: docs/evidence/payment.json, reproducible with
  `scripts/evidence_pay.py` (requires MNEMOS_PAYER_KEY / MNEMOS_PAYEE_KEY).

## The decision, from memory

1. `mnemos agree contractor --with alice --amount 160` wrote the
   agreement as a durable entity.
2. `mnemos pay contractor 160 --live --network mainnet` while the
   agreement was only `agreed` was refused by the gate. Nothing was
   broadcast.
3. `mnemos advance contractor --to delegated` then `--to delivered`
   moved the agreement state, one step at a time, each transition
   journaled.
4. The same payment was then authorized: the gate read the delivered
   agreement, checked the amount against it, and the executor signed and
   broadcast the transaction above. The agreement advanced to `paid`.

The chain is reproducible with `mnemos replay contractor`.

## What proves the stack is real work

- The transaction exists on Base mainnet and succeeded.
- The only copy of the agreement lived in Sibyl Memory. There is no
  in-process fallback; the executor holds no terms.
- The refusal step proves memory gates actions, not just records them.

## Reproduce

```bash
pip install '.[payments]'
scripts/make_payer.py   # fund the printed address with a few dollars of ETH on Base
scripts/make_payee.py
export MNEMOS_PAYER_KEY=.mnemos-payer.key
export MNEMOS_PAYEE_KEY=.mnemos-payee.key
mnemos agree contractor --with alice --amount 160
mnemos pay contractor 160 --live --network mainnet   # refused
mnemos advance contractor --to delegated
mnemos advance contractor --to delivered
mnemos pay contractor 160 --live --network mainnet   # real tx
mnemos replay contractor
```

# The Virtuals partner stack

The agent runs real inference on Virtuals compute, dispatched from
memory. The console agent id is stored as a durable identity entity and
read back by `mnemos dispatch` before anything is sent.

- Agent: 01a06610-3c31-7e84-928f-27c9f87f5c5a (created in the Virtuals
  console, Agent Compute)
- Endpoint: https://compute.virtuals.io/v1 (OpenAI-compatible)
- First dispatch ran Claude Fable 5 through the compute service and
  returned a completion (usage recorded, cost billed to the agent
  wallet).

The first response was the model honestly refusing the roleplay:

> I can't confirm that truthfully. I have no durable memory between
> conversations; this context window is my only source of truth.

That is exactly the gap Mnemos exists to close: the compute is smart,
and the memory layer is what makes it remember.

## Reproduce the Virtuals stack

```bash
pip install '.[virtuals]'
mnemos register --agent-id <console agent id>
export VIRTUALS_API_KEY=<key from the agent's Compute settings>
export VIRTUALS_COMPUTE_URL=https://compute.virtuals.io/v1
mnemos dispatch "a task for the agent"
```

## Fresh verification run (Sep 5)

A new dispatch through the ACP endpoint on the final code:

- Response id: gen-1788586150-ntsOrSusCzLVFjEMdJfE
- Model: anthropic/claude-fable-5, 256 tokens, cost 0.01104 USD billed
  to the agent wallet
- Capture: docs/evidence/dispatch.json, reproducible with
  `scripts/capture_dispatch.py`

The model again stated it has no durable memory between conversations:

> I can't confirm that, because it isn't true: I have no durable memory
> between conversations - this context window is my only source of truth.

## Partner stacks, both verified (x1.25)

| Partner | Stack | Live proof |
|---|---|---|
| Base | Payment executor behind the memory gate | mainnet tx 0x1ed5b2...46d194 (Sep 5, status 1) |
| Virtuals | ACP compute dispatch from remembered identity | response gen-1788586150-ntsOrSusCzLVFjEMdJfE (Sep 5, billed) |

Both integrations are exercised on the final code, both produce
artifacts committed to docs/evidence/, and both reproduce with the
scripts named above. This submission claims the x1.25 multiplier.
