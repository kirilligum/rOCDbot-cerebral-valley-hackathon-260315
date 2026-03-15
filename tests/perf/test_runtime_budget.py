# TEST-009
from __future__ import annotations

import json
import subprocess

import pytest


@pytest.mark.parametrize("case_name", [pytest.param("runtime_budget", id="TEST-009")])
def test_runtime_budget_guard(case_name: str) -> None:
    assert case_name == "runtime_budget"

    completed = subprocess.run(
        [
            "python3",
            "scripts/eval_demo.py",
            "--eval",
            "EVAL-001",
            "--mode",
            "live-or-cache",
            "--seeds",
            "7",
            "13",
            "23",
            "37",
            "41"
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(completed.stdout)
    assert payload["wall_clock_s"] <= 60.0
