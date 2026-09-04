# Virtuals proof: the compute model admits the bug

Live dispatch from Mnemos to the Virtuals compute service, captured to
`virtuals-dispatch.txt` in this folder.

## What ran

- Agent (Virtuals console): 01a06610-3c31-7e84-928f-27c9f87f5c5a
- Endpoint: https://compute.virtuals.io/v1 (OpenAI-compatible)
- Model: anthropic/claude-fable-5, provider Google
- Response id: gen-1788493170-zuedmqtHCxu8Uz3mTClq
- Cost billed to the agent wallet: 0.00954 USD
- Prompt tokens 44, completion tokens 182

## The response

The model refused the roleplay and stated the bug Mnemos fixes:

> I can't confirm that — I'm Claude, and I don't have durable memory
> between conversations; my context window is genuinely all I work
> from.

The smartest model in the room says, on the record, that it has no
memory. Mnemos is the memory layer that makes it remember.

## Reproduce

```bash
export VIRTUALS_API_KEY=<key>
export VIRTUALS_COMPUTE_URL=https://compute.virtuals.io/v1
export VIRTUALS_MODEL=anthropic-claude-fable-5
mnemos register --agent-id 01a06610-3c31-7e84-928f-27c9f87f5c5a
mnemos dispatch "You are Mnemos, an agent with durable memory. Confirm in one line that memory, not context, is your source of truth."
```
