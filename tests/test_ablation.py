"""Pin the measured ablation numbers so regressions are caught."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.ablation import run

ROOT = Path(__file__).resolve().parent.parent


def test_ablation_numbers_are_exactly_what_we_publish():
    result = run()
    assert result["trials"] == 12
    assert result["memory_on"]["payments_allowed"] == 12
    assert result["memory_off"]["payments_allowed"] == 0
    assert result["revision_on"]["payments_blocked_while_suspect"] == 12
    assert result["revision_on"]["payments_allowed_after_reconsider"] == 12
    assert result["revision_off"]["payments_allowed"] == 12

    published = json.loads(
        (ROOT / "docs" / "evidence" / "ablation.json").read_text(encoding="utf-8")
    )
    assert published == result
