"""Create a testnet payer wallet and print its address.

The private key is written to .mnemos-payer.key in the repo root and
never printed or committed (it is gitignored). Fund the printed address
from a Base Sepolia faucet, then run:

    MNEMOS_PAYER_KEY=.mnemos-payer.key mnemos pay contractor 160 --live
"""
from __future__ import annotations

from pathlib import Path

from eth_account import Account

KEY_FILE = Path(__file__).resolve().parent.parent / ".mnemos-payer.key"


def main() -> int:
    if KEY_FILE.exists():
        print("payer key already exists, not overwriting")
        print("address:", Account.from_key(KEY_FILE.read_text().strip()).address)
        return 1
    account = Account.create()
    KEY_FILE.write_text(account.key.hex(), encoding="utf-8")
    print("created .mnemos-payer.key (gitignored)")
    print("fund this address on Base Sepolia:")
    print(account.address)
    print()
    print("then run:")
    print("MNEMOS_PAYER_KEY=.mnemos-payer.key mnemos pay contractor 160 --live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
