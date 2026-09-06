# Mnemos — Demo Script (word for word, ~4 minutes)

You speak everything in quotes. The [brackets] are clicks and screen
actions, not spoken. One continuous take. Practice the two terminal
beats once before recording.

Total beats: 8. The wow moments are Beat 5 (live money on Base), Beat
6 (cold start with timestamp on screen), and Beat 7 (proof on the
explorer).

---

## Beat 1 — Cold open (~20s)

> Every AI assistant has amnesia. Close the tab, the conversation dies,
> and tomorrow you teach it everything again. Forgetting is a bug. This
> is Mnemos. An agent whose memory is the product. Built on Sibyl
> Memory, with Base and Virtuals doing real work. And this thing is
> live, my friends are using it right now.

[Open trymnemos.xyz, scroll the hero once, let the badge row show.]

> Four numbers I will prove in the next three minutes. 147 tests,
> green. Two partner stacks, live. One revision gate. Seventeen memory
> tools. Nothing on this page is faked, every number is verifiable.

## Beat 2 — The pain, and who has it (~25s)

[Scroll to "What memory improves".]

> Here is the problem in four cards. Money: agents re-explain themselves
> and burn tokens. Decisions: agents agree to one thing and do another.
> Failures: they make the same mistake twice. Corrections: you fix a
> fact and nothing changes, because the old decision keeps running.
> These are real leaks, and builders who run agents that pay people feel
> every one of them.

## Beat 3 — Live use, on camera (~20s)

[Scroll to the bottom CTA, point at the live counts.]

> This is not a demo island. Four people are on the waitlist right now.
> Five devices have built private memories here. The counts update live.
> If a judge signs up during review, the number moves. That is real
> usage, not a slide.

## Beat 4 — Teach it, ask it (~35s)

[Scroll up to the playground. Click "Teach me two facts", wait, click
"What do you know about me?".]

> Two facts go into Sibyl Memory as durable entities. I like short
> direct answers. My contractor rate is forty per hour. Now I ask what
> it knows about me. It answers only from memory. If memory held
> nothing, it would say so. No invented memories, ever. Recall is the
> floor, not the ceiling.

## Beat 5 — The load-bearing moment: wrong memory stops the money (~50s)

[Click "Revise my contractor rate", then "Run blast radius".]

> Now the part nobody builds. I correct my rate from forty to sixty.
> Mnemos does not just update the fact. It walks every decision and
> every agreement that depended on that fact. They become suspect. The
> payment gate refuses them until each one is reviewed. A wrong memory
> can no longer keep paying out. That is memory changing what the agent
> may do, not just what it says.

[Open a terminal next to the browser. Type and run:]

```
mnemos agree banner-job --with alex --amount 160
mnemos pay banner-job 160 --live --network mainnet
```

> Same story live. I create an agreement for 160. I try to pay. Refused.
> The gate read the agreement, saw it is not delivered, and broadcast
> nothing. Memory just stopped a premature payment, on mainnet, on
> camera.

[Run:]

```
mnemos advance banner-job --to delegated
mnemos advance banner-job --to delivered
mnemos pay banner-job 160 --live --network mainnet
```

> One state at a time, delivered. Now the same command executes. A real
> transaction on Base mainnet, signed because memory said so. [If it
> fails on camera: "The network is being slow, and that is fine, here is
> the same flow executed earlier today" and open Beat 7's explorer link.]

## Beat 6 — Cold start, with the clock on screen (~45s)

[In the terminal, run `date` and `git rev-parse --short HEAD`. Leave
the terminal visible. Then close the browser tab, open trymnemos.xyz
again, and click "What do you know about me?".]

> Fresh session, timestamp on screen, commit hash on screen, same
> browser. Watch it recall. My preferences, my rate, the revised fact,
> all back from memory. No re-teaching. This is the cold start beat the
> rules ask for, and it is real: every browser gets a private store, and
> reopening brings it back.

## Beat 7 — Both partner stacks, verifiable (~30s)

[Open the Base tx on basescan: the one from Beat 5 if it went through,
else https://basescan.org/tx/0x1ed5b2674123e70a4de87ca9ceebad38f961fc6612c2206bb1456356ae46d194]

> That payment is on the explorer. Status one. The only copy of the
> agreement lived in Sibyl Memory. There is no fallback in the code. No
> memory, no payment.

[Back in the terminal:]

```
cat docs/evidence/dispatch.json
```

> And the second stack: the agent runs inference on Virtuals compute,
> dispatched from a remembered agent id. Claude Fable five, 256 tokens,
> billed. And the model said the line that started all of this: "I have
> no durable memory between conversations." That is the gap Mnemos
> closes.

## Beat 8 — The deletion test, and the close (~25s)

> Last proof. If I delete the memory layer, recall empties, the gate
> closes, and the journal seal breaks. The doctor runs that test for
> you, on demand. Memory here is not decoration. It is the critical
> path.

[Scroll to the bottom CTA.]

> Mnemos is live at trymnemos.xyz. Add your email and you will be told
> when new memory features ship. Give your agent a memory it cannot
> lose.

---

## Before you record

1. One practice run of Beats 5 and 6, no camera.
2. Terminal font large enough to read on a phone.
3. Payer key must have a few dollars of ETH on Base mainnet for Beat 5.
4. If Beat 5's live tx fails on camera, use the fallback line and the
   Sep 5 explorer link. Never fake a success.

