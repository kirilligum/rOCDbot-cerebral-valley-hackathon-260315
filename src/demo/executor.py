"""Scripted correction executor for the prepared-scene demo."""

from __future__ import annotations

from pathlib import Path

from src.demo.isaac_adapter import PreparedSceneAdapter


DEFAULT_PLAN = ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]


def run_scripted_correction(
    adapter: PreparedSceneAdapter,
    *,
    plan: list[str] | None = None,
    artifact_dir: str | Path | None = None,
) -> dict:
    executed_plan = list(plan or DEFAULT_PLAN)
    before = adapter.read_scene_state()
    artifact_paths: dict[str, str] = {}
    if artifact_dir is not None:
        artifact_root = Path(artifact_dir)
        artifact_root.mkdir(parents=True, exist_ok=True)
        before_path = adapter.capture_frame(artifact_root / "before.png", title="Before correction")
        artifact_paths["before_frame"] = str(before_path)

    corrected = adapter.execute_plan(executed_plan)

    if artifact_dir is not None:
        artifact_root = Path(artifact_dir)
        after_path = adapter.capture_frame(artifact_root / "after.png", title="After correction")
        artifact_paths["after_frame"] = str(after_path)

    return {
        "status": "success",
        "before_scene": before,
        "corrected_scene": corrected,
        "executed_plan": executed_plan,
        "artifacts": artifact_paths,
    }
