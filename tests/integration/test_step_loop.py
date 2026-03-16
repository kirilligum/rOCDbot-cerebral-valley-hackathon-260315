# TEST-015
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT


@pytest.mark.parametrize("case_name", [pytest.param("step_loop", id="TEST-015")])
def test_step_loop_progress(case_name: str, tmp_path: Path) -> None:
    assert case_name == "step_loop"

    from src.demo.critic import CriticDecision
    from src.demo.run_live import run_demo
    from src.demo.scene_state import SceneState

    before = json.loads((REPO_ROOT / "tests" / "fixtures" / "scene_state" / "prepared_seed_7.json").read_text(encoding="utf-8"))
    mid = before.copy()
    mid["yaw_before_deg"] = 11.0
    mid["position_error_before_cm"] = 1.2
    final = before.copy()
    final["yaw_before_deg"] = 0.0
    final["position_error_before_cm"] = 0.0

    before_scene = SceneState.model_validate(before)
    mid_scene = SceneState.model_validate(mid)
    final_scene = SceneState.model_validate(final)

    class Adapter:
        def __init__(self) -> None:
            self._scene = before_scene
            self.calls = 0

        def reset_scene(self, seed: int) -> SceneState:
            return self._scene

        def read_scene_state(self) -> SceneState:
            return self._scene

        def restore_scene_state(self, scene_state: SceneState) -> None:
            self._scene = scene_state

        def execute_plan_with_steps(self, plan: list[str]) -> list[SceneState]:
            self.calls += 1
            if self.calls == 1:
                return [mid_scene]
            if self.calls == 2:
                return [final_scene]
            return [final_scene]

        def capture_frame(self, path, *, title=None):
            resolved = Path(path)
            resolved.parent.mkdir(parents=True, exist_ok=True)
            resolved.touch()
            return resolved

    class SequenceCritic:
        def __init__(self) -> None:
            self.calls = 0

        def evaluate(self, _: SceneState) -> CriticDecision:
            self.calls += 1
            if self.calls == 1:
                is_disordered = True
            else:
                is_disordered = True
            return CriticDecision(
                is_disordered=is_disordered,
                reason="loop test",
                target_object="book_1",
                plan=["approach", "grasp", "lift", "rotate_to_target", "place", "settle"],
            )

    adapter = Adapter()
    critic = SequenceCritic()
    result = run_demo(
        mode="dry-run",
        seed=7,
        artifact_root=tmp_path,
        critic=critic,
        adapter=adapter,
        max_loop_steps=2,
    )

    assert result["status"] == "success"
    assert critic.calls >= 2
    assert adapter.calls >= 2
    assert len(result["correction_steps"]) == 2
    loop_iterations = {entry["loop_iteration"] for entry in result["correction_steps"]}
    assert loop_iterations == {1, 2}
    assert result["correction_steps"][0]["loop_iteration"] == 1
    assert result["correction_steps"][1]["loop_iteration"] == 2
