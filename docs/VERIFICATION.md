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
