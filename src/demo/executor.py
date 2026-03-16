"""Scripted correction executor for the prepared-scene demo."""

from __future__ import annotations

import shutil
from pathlib import Path

from src.demo.isaac_adapter import PreparedSceneAdapter


DEFAULT_PLAN = ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]


def run_scripted_correction(
    adapter: PreparedSceneAdapter,
    *,
    plan: list[str] | None = None,
    artifact_dir: str | Path | None = None,
    start_step: int = 1,
    capture_before: bool = True,
) -> dict:
    executed_plan = list(plan or DEFAULT_PLAN)
    before = adapter.read_scene_state()
    artifact_paths: dict[str, str | list[str]] = {}
    correction_steps: list[dict[str, object]] = []
    if artifact_dir is not None:
        artifact_root = Path(artifact_dir)
        artifact_root.mkdir(parents=True, exist_ok=True)
        if capture_before:
            before_path = adapter.capture_frame(artifact_root / "before.png", title="Before correction")
            artifact_paths["before_frame"] = str(before_path)

    step_states = adapter.execute_plan_with_steps(executed_plan)
    step_titles = {
        1: "intermediate",
        2: "aligned",
        3: "final",
    }
    step_labels = {
        1: "Rotated but off position",
        2: "Aligned orientation",
        3: "Corner-aligned final",
    }
    for local_index, scene_state in enumerate(step_states, start=0):
        index = start_step + local_index
        if artifact_dir is not None:
            adapter.restore_scene_state(scene_state)
            step_path = adapter.capture_frame(
                artifact_root / f"step_{index:02d}.png",
                title=f"Step {index}: {step_labels.get(index, f'step {index}')}",
            )
        else:
            step_path = Path(f"/tmp/step_{index:02d}.png")
        correction_steps.append(
            {
                "step": index,
                "stage": step_titles.get(index, "intermediate"),
                "image_path": str(step_path),
                "scene_state": scene_state.model_dump(mode="json"),
            }
        )

    if artifact_dir is not None:
        after_path = Path(artifact_root / "after.png")
        final_step_path = Path(correction_steps[-1]["image_path"])
        if final_step_path != after_path:
            shutil.copy2(final_step_path, after_path)
        artifact_paths["after_frame"] = str(after_path)
        artifact_paths["step_frames"] = [entry["image_path"] for entry in correction_steps]
        if len(correction_steps) >= 1:
            artifact_paths["intermediate_frame"] = correction_steps[0]["image_path"]
            artifact_paths["step_1_frame"] = correction_steps[0]["image_path"]
        if len(correction_steps) >= 2:
            artifact_paths["aligned_frame"] = correction_steps[1]["image_path"]
            artifact_paths["step_2_frame"] = correction_steps[1]["image_path"]
        if len(correction_steps) >= 3:
            artifact_paths["final_frame"] = correction_steps[2]["image_path"]
            artifact_paths["step_3_frame"] = correction_steps[2]["image_path"]

    corrected = step_states[-1]
    return {
        "status": "success",
        "before_scene": before,
        "corrected_scene": corrected,
        "executed_plan": executed_plan,
        "artifacts": artifact_paths,
        "step_artifacts": correction_steps,
    }
