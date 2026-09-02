"""Payment execution behind the memory gate.

The gate decides; the executor acts. `pay` first asks the deterministic
gate whether a remembered, delivered agreement covers the amount. Only
then does it hand a PaymentIntent to an executor.

Every outcome is journaled: refusals leave an audit trail, and a
successful payment advances the agreement to 'paid', so memory reflects
what the agent did. There is no code path that sends money without a
passing gate.

Executors
---------
DryRunExecutor
    Journals the intent, sends nothing. Default, offline, testable.
BaseExecutor
    Submits a real transaction on Base Sepolia. Requires the `web3`
    package and a private key in MNEMOS_PAYER_KEY. One unit of payment
    amount maps to one gwei on testnet, so demos stay cheap.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

from ..memory.agreement import Agreement
from ..memory.gate import evaluate_payment
from ..memory.store import MemoryStore


@dataclass(frozen=True)
class PaymentIntent:
    agreement: str
    amount: float
    counterparty: str | None
    note: str | None


@dataclass(frozen=True)
class PaymentOutcome:
    allowed: bool
    reason: str
    agreement: str
    amount: float
    transaction: str | None = None
    executor: str | None = None


class Executor(Protocol):
    name: str

    def submit(self, intent: PaymentIntent) -> dict[str, Any]: ...


class DryRunExecutor:
    """Journals the intent and sends nothing."""

    name = "dry-run"

    def submit(self, intent: PaymentIntent) -> dict[str, Any]:
        return {
            "transaction": None,
            "network": None,
            "note": f"dry run for {intent.agreement} {intent.amount}",
        }


NETWORKS = {
    "sepolia": {"rpc": "https://sepolia.base.org", "chain_id": 84532},
    "mainnet": {"rpc": "https://mainnet.base.org", "chain_id": 8453},
}


def _resolve_key(value: str) -> str:
    """Env value may be a raw hex key or a path to a key file."""
    candidate = os.path.expanduser(value)
    if os.path.isfile(candidate):
        return open(candidate, encoding="utf-8").read().strip()
    return value


class BaseExecutor:
    """Submits a real transaction on Base."""

    def __init__(
        self,
        *,
        private_key: str | None = None,
        network: str = "sepolia",
    ) -> None:
        if network not in NETWORKS:
            raise RuntimeError(f"unknown network {network!r}")
        config = NETWORKS[network]
        self.name = f"base-{network}"
        self._rpc_url = config["rpc"]
        self._chain_id = config["chain_id"]
        self._private_key = _resolve_key(
            private_key or os.environ.get("MNEMOS_PAYER_KEY") or ""
        )
        if not self._private_key:
            raise RuntimeError(
                "BaseExecutor needs a private key: set MNEMOS_PAYER_KEY"
            )
        payee = os.environ.get("MNEMOS_PAYEE_ADDRESS")
        self._payee = payee or None
        payee_file = os.environ.get("MNEMOS_PAYEE_KEY")
        if not self._payee and payee_file:
            candidate = os.path.expanduser(payee_file)
            if os.path.isfile(candidate):
                try:
                    from eth_account import Account

                    raw = open(candidate, encoding="utf-8").read().strip()
                    self._payee = Account.from_key(raw).address
                except Exception:  # pragma: no cover
                    self._payee = None

    def submit(self, intent: PaymentIntent) -> dict[str, Any]:
        try:
            from web3 import Web3
        except ImportError as error:  # pragma: no cover
            raise RuntimeError(
                "web3 is required for live payments: pip install web3"
            ) from error

        w3 = Web3(Web3.HTTPProvider(self._rpc_url))
        if not w3.is_connected():  # pragma: no cover
            raise RuntimeError(f"cannot reach {self._rpc_url}")

        account = w3.eth.account.from_key(self._private_key)
        wei = int(intent.amount * 1_000_000_000)  # 1 unit = 1 gwei
        to_address = self._payee or account.address
        tx = {
            "from": account.address,
            "to": to_address,
            "value": wei,
            "gas": 21000,
            "maxFeePerGas": int(w3.eth.gas_price * 1.5),
            "maxPriorityFeePerGas": 1_000_000,  # 0.001 gwei tip
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": self._chain_id,
        }
        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        return {
            "transaction": tx_hash.hex(),
            "network": self._rpc_url,
            "note": f"sent {intent.amount} units from {account.address} to {to_address}",
        }


def pay(
    store: MemoryStore,
    agreement_name: str,
    amount: float,
    *,
    executor: Executor | None = None,
) -> PaymentOutcome:
    """Execute a payment only if memory authorizes it."""
    executor = executor or DryRunExecutor()

    result = evaluate_payment(store, agreement_name, amount)
    if not result.allowed:
        store.record_event(
            evaluated={"agreement": agreement_name, "amount": amount},
            acted=[f"payment refused: {result.reason}"],
        )
        return PaymentOutcome(
            allowed=False,
            reason=result.reason,
            agreement=agreement_name,
            amount=amount,
        )

    agreement = Agreement.open(store, agreement_name)
    body = agreement.body if agreement is not None else {}
    intent = PaymentIntent(
        agreement=agreement_name,
        amount=amount,
        counterparty=body.get("counterparty"),
        note=body.get("note"),
    )
    receipt = executor.submit(intent)
    transaction = receipt.get("transaction")

    if agreement is not None:
        agreement.advance("paid")

    action = f"payment sent: {agreement_name} {amount}"
    if transaction:
        action += f" tx={transaction}"
    else:
        action += " (dry run)"
    store.record_event(
        evaluated={"agreement": agreement_name, "amount": amount},
        acted=[action],
        extra={"transaction": transaction, "executor": executor.name},
    )

    return PaymentOutcome(
        allowed=True,
        reason=result.reason,
        agreement=agreement_name,
        amount=amount,
        transaction=transaction,
        executor=executor.name,
    )
