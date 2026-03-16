# TEST-018
from __future__ import annotations

import time

import pytest

from src.demo.run_live import run_demo


@pytest.mark.parametrize("case_name", [pytest.param("loop_budget", id="TEST-018")])
def test_loop_budget_guard(case_name: str) -> None:
    assert case_name == "loop_budget"

    starts = time.perf_counter()
    artifacts = [run_demo(mode="mocked-nebius", seed=seed) for seed in (7, 13)]
    wall_clock = time.perf_counter() - starts

    max_steps = max(len(run["correction_steps"]) for run in artifacts)
    assert wall_clock <= 45.0
    assert max_steps <= 3
