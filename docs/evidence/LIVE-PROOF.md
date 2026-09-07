# Live proof - open in any browser

Everything on this page is verifiable from a fresh machine with nothing
installed. No local files, no setup. The repo is the evidence.

## 1. Base mainnet transaction

https://basescan.org/tx/0x1ed5b2674123e70a4de87ca9ceebad38f961fc6612c2206bb1456356ae46d194

Status 1. The payment the gate refused while the agreement was only
agreed, then executed once the agreement was delivered. Same request,
opposite outcomes, memory state alone.

## 2. Virtuals ACP dispatch receipt

From [dispatch.json](dispatch.json), the response body of a live call to
`https://compute.virtuals.io/v1`:

- agent id: `01a06610-3c31-7e84-928f-27c9f87f5c5a`
- response id: `gen-1788586150-ntsOrSusCzLVFjEMdJfE`
- model: `anthropic/claude-fable-5`
- tokens: 44 prompt + 212 completion, 256 total
- billed to the agent wallet: 0.01104 USD

The model's own words, verbatim from the receipt:

> I can't confirm that, because it isn't true: I have no durable memory
> between conversations — this context window is my only source of truth.

The smartest model in the room states the bug on the record. Mnemos is
the memory layer that makes it remember.

## 3. Live right now

- Playground: https://trymnemos.xyz
- Usage stats: https://mnemos-production-2572.up.railway.app/stats
- Waitlist: https://mnemos-production-2572.up.railway.app/waitlist/list
- Hosted MCP: https://mnemos-production-2572.up.railway.app/mcp

## 4. Deletion test

Delete the memory and the payment path fails closed. Reproduction steps:
[../VERIFICATION.md](../VERIFICATION.md).
