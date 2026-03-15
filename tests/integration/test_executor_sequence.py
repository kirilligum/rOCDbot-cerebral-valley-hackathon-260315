# TEST-006
from __future__ import annotations

import pytest


@pytest.mark.parametrize("case_name", [pytest.param("executor", id="TEST-006")])
def test_scripted_executor_sequence(case_name: str) -> None:
    assert case_name == "executor"

    from src.demo.executor import DEFAULT_PLAN, run_scripted_correction
    from src.demo.isaac_adapter import PreparedSceneAdapter

    adapter = PreparedSceneAdapter()
    adapter.reset_scene(seed=7)
    result = run_scripted_correction(adapter, plan=DEFAULT_PLAN)
    corrected = result["corrected_scene"]

    assert result["status"] == "success"
    assert corrected.yaw_before_deg <= 5.0
    assert corrected.position_error_before_cm <= 2.0
    assert result["executed_plan"] == DEFAULT_PLAN
