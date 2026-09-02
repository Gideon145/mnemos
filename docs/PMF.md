# PMF: why Mnemos has to exist

This is the product-market-fit case, in the words we use publicly.

## The RAM analogy

Old computers had almost no RAM. The CPU was not the bottleneck; the
memory was. Advances stalled until memory got cheap and reliable.

The same thing is happening with agents. Models keep getting smarter,
but agent memory still sucks or gets super expensive in tokens.

Mnemos is the RAM upgrade for agents. Not a bigger context window.
Durable memory that survives the session, and recall that costs zero
tokens.

## The failure modes we fix

| Failure | What happens today | What Mnemos does |
|---|---|---|
| The reset | Every chat starts from zero, preferences get retyped forever | Durable facts on Sibyl, recalled in fresh sessions and on fresh machines |
| The repeat mistake | The agent forgets what went wrong and does it again | Lessons store the failure itself, with severity, and surface it next time |
| The amnesiac payer | An agent that forgets can agree to one thing and do another | Payments only execute when a remembered, delivered agreement covers them |
| The lost session | Unfinished work dies with the runtime | Tasks are durable entities; resume lists what is left |
| The unaccountable agent | Nobody knows why a decision changed | Every write, recall, and refusal is journaled; replay shows the chain |

## Why durable beats context stuffing

Context windows are rented memory. You pay tokens to re-read what you
already told the agent. Mnemos recall reads Sibyl and answers without a
single model call for the memory step. Memory stops being a per-message
cost and becomes an asset you own.

## The proof

- Deletion test: `mnemos doctor` proves recall and gates collapse when
  memory is removed.
- Cold start: a keepsake pack restores memory on a fresh machine.
- Real money: a memory-gated transaction on Base mainnet, linked in
  docs/VERIFICATION.md.
