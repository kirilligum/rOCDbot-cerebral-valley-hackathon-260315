# TEST-016
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize("case_name", [pytest.param("loop_safety", id="TEST-016")])
def test_loop_safety_gate(case_name: str, tmp_path: Path) -> None:
    assert case_name == "loop_safety"

    from src.demo.critic import CriticDecision
    from src.demo.run_live import run_demo
    from src.demo.scene_state import SceneState

    class BadCritic:
        def __init__(self, scene: SceneState) -> None:
            self.scene = scene
            self.calls = 0

        def evaluate(self, _: SceneState) -> CriticDecision:
            self.calls += 1
            return CriticDecision(
                is_disordered=True,
                reason="bad plan",
                target_object="book_1",
                plan=["teleport_object"],
            )

    class Adapter:
        def __init__(self, scene: SceneState) -> None:
            self._scene = scene
            self.calls = 0

        def reset_scene(self, seed: int) -> SceneState:
            return self._scene

        def read_scene_state(self) -> SceneState:
            return self._scene

        def restore_scene_state(self, scene_state: SceneState) -> None:
            self._scene = scene_state

        def execute_plan_with_steps(self, plan: list[str]) -> list[SceneState]:
            self.calls += 1
            raise AssertionError("executor must not run on unsupported plan")

        def capture_frame(self, path, *, title=None):
            Path(path).touch()
            return Path(path)

    fixture = {
        "schema_version": "1.0",
        "seed": 7,
        "mode": "headless-scripted",
        "object_id": "book_1",
        "table_axis_deg": 0.0,
        "yaw_before_deg": 28.0,
        "target_yaw_deg": 0.0,
        "position_error_before_cm": 1.5,
        "object_center_xy_cm": [2.0, 1.0],
        "target_center_xy_cm": [1.5, 1.2],
    }
    scene = SceneState.model_validate(fixture)

    adapter = Adapter(scene)
    critic = BadCritic(scene)

    with pytest.raises(ValueError, match="unsupported critic plan"):
        run_demo(
            mode="dry-run",
            seed=7,
            artifact_root=tmp_path,
            critic=critic,
            adapter=adapter,
        )

    assert adapter.calls == 0
