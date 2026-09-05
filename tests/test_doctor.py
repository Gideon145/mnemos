"""Doctor tests: the deletion test proves memory is load-bearing."""
from __future__ import annotations

from core.memory.doctor import run_doctor


def test_doctor_is_healthy_on_a_clean_system():
    report = run_doctor()
    assert report.healthy is True
    names = [name for name, _, _ in report.checks]
    assert names == [
        "durable write and recall",
        "gate opens on a remembered agreement",
        "journal seal verifies",
        "deletion empties recall",
        "deletion closes the gate",
        "deletion breaks the journal seal",
    ]


def test_doctor_deletion_check_closes_the_gate():
    report = run_doctor()
    gate_check = next(
        (ok, detail)
        for name, ok, detail in report.checks
        if name == "deletion closes the gate"
    )
    assert gate_check[0] is True
    assert "no remembered agreement" in gate_check[1]
