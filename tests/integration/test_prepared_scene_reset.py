# TEST-003
from __future__ import annotations

import pytest


@pytest.mark.parametrize("case_name", [pytest.param("prepared_reset", id="TEST-003")])
def test_prepared_scene_reset_determinism(case_name: str) -> None:
    assert case_name == "prepared_reset"

    from src.demo.isaac_adapter import PreparedSceneAdapter

    adapter = PreparedSceneAdapter()
    first = adapter.reset_scene(seed=7)
    second = adapter.reset_scene(seed=7)

    assert first.model_dump() == second.model_dump()
    assert first.yaw_before_deg == pytest.approx(28.0)
    assert first.object_center_xy_cm == pytest.approx((2.0, 1.0))
