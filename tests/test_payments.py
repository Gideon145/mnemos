"""Payment executor tests: the gate decides, the executor acts."""
from __future__ import annotations

from core.memory.agreement import Agreement
from core.memory.store import MemoryStore
from core.payments.executor import DryRunExecutor, pay


def _delivered_agreement(store, name="contractor"):
    agreement = Agreement(store, name, amount=160, counterparty="alice")
    agreement.advance("agreed")
    agreement.advance("delegated")
    agreement.advance("delivered")
    return agreement


def test_blocked_payment_is_refused_and_journaled(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        outcome = pay(store, "nobody", 40)
        assert outcome.allowed is False
        assert outcome.executor is None
        assert any(
            "payment refused" in line
            for event in store.timeline(limit=5)
            for line in _acted_lines(event)
        )
    finally:
        store.close()


def test_dry_run_payment_advances_agreement_to_paid(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered_agreement(store)
        outcome = pay(store, "contractor", 160, executor=DryRunExecutor())

        assert outcome.allowed is True
        assert outcome.transaction is None
        assert outcome.executor == "dry-run"
        agreement = Agreement.open(store, "contractor")
        assert agreement.state == "paid"
    finally:
        store.close()


def test_paid_agreement_cannot_be_paid_twice(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered_agreement(store)
        pay(store, "contractor", 160)
        second = pay(store, "contractor", 160)
        assert second.allowed is False
        assert "delivered" in second.reason
    finally:
        store.close()


def test_dry_run_journals_executor_name(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered_agreement(store)
        pay(store, "contractor", 160, executor=DryRunExecutor())

        extras = [event.get("extra") for event in store.timeline(limit=5)]
        assert any(
            extra and extra.get("executor") == "dry-run" for extra in extras
        )
    finally:
        store.close()


def test_pending_claim_blocks_duplicate_intent(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    try:
        _delivered_agreement(store)
        store.set_working_state(
            "payment:contractor:160",
            {"status": "pending", "agreement": "contractor", "amount": 160},
        )
        outcome = pay(store, "contractor", 160)
        assert outcome.allowed is False
        assert "already claimed" in outcome.reason
        assert "duplicate" in outcome.reason
    finally:
        store.close()


def test_failed_submit_marks_claim_failed_and_retry_passes(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")

    class BrokenExecutor:
        name = "broken"

        def submit(self, intent):
            raise RuntimeError("rpc down")

    try:
        _delivered_agreement(store)
        try:
            pay(store, "contractor", 160, executor=BrokenExecutor())
        except RuntimeError:
            pass
        claim = store.get_working_state("payment:contractor:160")
        assert claim["status"] == "failed"

        outcome = pay(store, "contractor", 160)
        assert outcome.allowed is True
        assert store.get_working_state("payment:contractor:160")["status"] == "paid"
    finally:
        store.close()


def _acted_lines(event):
    acted = event.get("acted")
    if isinstance(acted, str):
        return [acted]
    return list(acted or [])
