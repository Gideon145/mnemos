# Mnemos — Build Plan (Sibyl Labs Hackathon)

Build window: **Sep 1–10, 2026**. Team: The Muses.

| Day | Milestone | Commits expected |
|---|---|---|
| Sep 1 | Repo foundation: scaffold `core/`, memory-tier interfaces, Sibyl connector stub, test harness | ~15 |
| Sep 2 | Durable tier: `remember()`/`recall()` against Sibyl; deletion-test harness green | ~15 |
| Sep 3 | Keepsake v1: export/import `.mne` packs, signature, conflict metadata | ~12 |
| Sep 4 | Base action executor: remembered-agreement gate → x402/USDC payment (testnet) | ~12 |
| Sep 5 | Virtuals registration + delegation memory write-back | ~8 |
| Sep 6 | Daily tier + recap; recall confidence + adaptive follow-up | ~10 |
| Sep 7 | CLI polish (`mnemos ask`, `mnemos remember`, `mnemos keepsake export`) | ~10 |
| Sep 8 | Demo video: fresh-session + fresh-machine recall, payment from memory | — |
| Sep 9 | README final (load-bearing map), public posts, buffer fixes | ~8 |
| Sep 10 | Final QA, second-run survival, submission | — |

## The demo (one unedited take)

1. `mnemos remember "I like short direct answers; contractor rate is $40/hr; ship on Fridays"`
2. `mnemos keepsake export my-mnemos.mne`
3. Fresh machine, fresh install: `mnemos keepsake import my-mnemos.mne`
4. `mnemos ask "how do I like answers? what's my contractor rate?"` → answers from Sibyl
5. `mnemos pay contractor 4h` → x402 payment on Base, terms read from memory
6. Deletion test: remove Sibyl layer → same questions now fail → load-bearing proven

## Submission checklist

- [ ] Public repo, MIT, real commit history
- [ ] README with load-bearing memory map (judges can find call sites in <2 min)
- [ ] 2–5 min demo with cold-start recall beat
- [ ] Two public posts tagging @sibylcap + partners
- [ ] Prior Work declaration (see docs/PRIOR_WORK.md)
