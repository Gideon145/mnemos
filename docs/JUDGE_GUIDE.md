# Judge Guide - Mnemos (4 minutes)

An agent whose memory is the product. Durable memory on Sibyl. Money gates
on remembered agreements on Base. Compute dispatches from remembered
identity on Virtuals. When a fact is corrected, everything built on it
becomes suspect and the gate closes until each dependent is reconsidered.
147 tests. One Base mainnet tx. One billed Virtuals dispatch. Everything
on this page is clickable in four minutes.

---

## 1. See it work (60 seconds)

Go to **[trymnemos.xyz](https://trymnemos.xyz)**
(alt: **[mnemos-production-2572.up.railway.app](https://mnemos-production-2572.up.railway.app)**).

- Click **Teach me two facts** - the chips run raw MCP tools, not
  canned text.
- Click **What do you know about me?** - the answer comes from memory
  only.
- Type in chat: `my name is alex`, then `what is my name` - the answer
  is grounded in what memory holds, never invented.
- Each browser gets a **private store**: a device id in localStorage
  scopes every call, and reopening the page keeps that browser's memory.

## 2. The load-bearing moment (60 seconds)

In the playground, click **Revise my contractor rate** then **Run blast
radius**.

Or on the CLI:

```bash
pip install .
mnemos agree contractor --with alice --amount 160
mnemos pay contractor 160 --live --network mainnet   # refused: not delivered
mnemos advance contractor --to delegated
mnemos advance contractor --to delivered
mnemos pay contractor 160 --live --network mainnet   # executed
mnemos revise preference contractor_rate 60 --reason corrected
mnemos pay contractor 160                            # refused: suspect
mnemos reconsider agreement contractor --valid --reason "fixed price"
mnemos pay contractor 160                            # gate reopened
mnemos doctor                                       # deletion breaks everything
```

## 3. Verify the partner stacks (60 seconds)

| Stack | What ran | Proof |
|---|---|---|
| Base | Payment gate refused while `agreed`, executed once `delivered` | [mainnet tx `0x1ed5b2...46d194`](https://basescan.org/tx/0x1ed5b2674123e70a4de87ca9ceebad38f961fc6612c2206bb1456356ae46d194), status 1 |
| Virtuals | ACP dispatch from a remembered console agent id | response `gen-1788586150-ntsOrSusCzLVFjEMdJfE`, `anthropic/claude-fable-5`, 256 tokens, $0.01104 billed |

Both reproduce from `docs/VERIFICATION.md`:
`scripts/evidence_pay.py` and `scripts/capture_dispatch.py`.

## 4. CLI + MCP (30 seconds)

```bash
pip install '.[mcp]'
mnemos mcp --db ~/.mnemos/memory.db
```

Remote MCP: `https://mnemos-production-2572.up.railway.app/mcp`
(17 tools, typed outputs). One-click install:
[Smithery](https://smithery.ai/servers/mnemos/mnemos).

## 5. Numbers you can verify

| Metric | Value | Proof |
|---|---|---|
| Tests | 147, all green | `python -m pytest tests -q` |
| Ablation, memory off | 0/12 allowed | `scripts/ablation.py` |
| Ablation, revision on | 0/12 while suspect, 12/12 after reconsider | `scripts/ablation.py` |
| Doctor checks | 9 | `mnemos doctor` |
| MCP tools | 17 | `mnemos mcp` |
| Device isolation | one store per browser, survives reopen | `tests/test_mcp.py` |
| Waitlist | live, verifiable: sign up and watch the count move | `POST /waitlist`, `GET /waitlist/count` |
| Waitlist signups | the actual emails, newest first | [`GET /waitlist/list`](https://mnemos-production-2572.up.railway.app/waitlist/list) |
| Real usage | distinct devices on the playground | `GET /stats` |
| Pain point validated | the Sibyl account on the revision gap | [X reply](https://x.com/sibylcap/status/2096360556244435138) |
| Journal seal | breaks on append, edit, delete | `tests/test_seal.py` |

## 6. What makes this a Sibyl build

- **Coordination patterns:** revision blast radius, suspect gate,
  reconsider. Memory changes what the agent may do, not just what it
  says.
- **Dynamic storage:** dream (review-gated consolidation), rewind (time
  travel with diff), pulse (proactive queue), owner profile (curated
  summary).
- **Tamper-evident journal:** chained SHA-256 seal.
- **Memory-gated payments:** a remembered delivered agreement is the
  only thing that authorizes money.

## Honest limits

- Recall is FTS plus a deterministic fallback; the optional hybrid
  embedder is off by default and behind an env flag.
- The hosted surface has no authentication; device isolation is by
  browser id, not credentials.
- Single-agent memory: no multi-agent shared store yet.
- Revision is user-issued; nothing rewrites memory on its own except
  the review-gated proposals.
