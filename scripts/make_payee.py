"""Create the payee wallet (the contractor who gets paid).

The private key is written to .mnemos-payee.key in the repo root and
never printed or committed (gitignored). The payee needs no funds:
receiving costs nothing. Point the payer at it with:

    MNEMOS_PAYEE_KEY=.mnemos-payee.key
"""
from __future__ import annotations

from pathlib import Path

from eth_account import Account

KEY_FILE = Path(__file__).resolve().parent.parent / ".mnemos-payee.key"


def main() -> int:
    if KEY_FILE.exists():
        print("payee key already exists, not overwriting")
        print("address:", Account.from_key(KEY_FILE.read_text().strip()).address)
        return 1
    account = Account.create()
    KEY_FILE.write_text(account.key.hex(), encoding="utf-8")
    print("created .mnemos-payee.key (gitignored)")
    print("payee address:")
    print(account.address)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
