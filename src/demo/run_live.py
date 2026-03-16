"""Single-command demo orchestration."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from src.demo.contracts import (
    DEFAULT_LOOP_STEPS,
    LOOP_POSITION_ERROR_CM_THRESHOLD,
    LOOP_YAW_ERROR_DEG_THRESHOLD,
)
from src.demo.critic import NebiusCritic
from src.demo.executor import run_scripted_correction
from src.demo.isaac_adapter import PreparedSceneAdapter
from src.demo.metrics import compute_metrics, compute_step_metrics, is_complete_state
from src.demo.overlay import build_overlay_payload
from src.demo.planner import map_decision_to_plan
from src.demo.scene_state import SceneState

ROOT = Path(__file__).resolve().parents[2]
VALID_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "critic" / "valid_decision.json"


def _mocked_transport(_: dict) -> dict:
    return json.loads(VALID_FIXTURE_PATH.read_text(encoding="utf-8"))


def _timeout_transport(_: dict) -> dict:
    raise TimeoutError("forced cache-only mode")


def run_demo(
    *,
    mode: str,
    seed: int,
    artifact_root: str | Path | None = None,
    critic: NebiusCritic | None = None,
    adapter: PreparedSceneAdapter | None = None,
    max_loop_steps: int | None = None,
) -> dict:
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + f"-{mode}-seed{seed}"
    artifact_base = Path(artifact_root or ROOT / "artifacts")
    artifact_dir = artifact_base / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    adapter = adapter or PreparedSceneAdapter()
    before_scene = adapter.reset_scene(seed=seed)
    current_scene = before_scene

    critic = critic or _build_critic(mode)
    max_steps = _resolve_loop_limit(max_loop_steps)
    loop_iterations = 0
    next_step_index = 1
    correction_steps: list[dict[str, object]] = []

    total_critic_latency_ms = 0.0
    total_execution_latency_ms = 0.0
    run_status = "success"

    latest_decision = _build_default_decision(before_scene)
    latest_plan: list[str] = []

    while loop_iterations < max_steps:
        if _is_complete_state(current_scene):
            break

        loop_iterations += 1
        loop_start = time.perf_counter()
        latest_decision = critic.evaluate(current_scene)
        total_critic_latency_ms += _elapsed_ms(loop_start)

        if not latest_decision.is_disordered:
            break

        try:
            latest_plan = map_decision_to_plan(latest_decision)
        except ValueError as exc:
            run_status = "ERR_EXECUTION_FAIL"
            raise ValueError(f"unsupported critic plan: {latest_decision.plan}") from exc

        if not latest_plan:
            break

        executed_start = time.perf_counter()
        correction = run_scripted_correction(
            adapter,
            plan=latest_plan,
            artifact_dir=artifact_dir,
            start_step=next_step_index,
            capture_before=loop_iterations == 1,
        )
        total_execution_latency_ms += _elapsed_ms(executed_start)

        if correction["status"] != "success":
            run_status = "ERR_EXECUTION_FAIL"
            break

        step_state_payload = current_scene.model_dump(mode="json")
        for step_payload in correction["step_artifacts"]:
            next_step_index += 1
            step_scene = SceneState.model_validate(step_payload["scene_state"])
            step_metrics = compute_step_metrics(step_state_payload, step_scene.model_dump(mode="json"))
            step_payload["decision_source"] = latest_decision.source
            step_payload["loop_iteration"] = loop_iterations
            step_payload["step_metrics"] = step_metrics
            step_state_payload = step_scene.model_dump(mode="json")
            current_scene = scene_state = step_scene
            correction_steps.append(step_payload)

            if _is_complete_state(scene_state):
                break

        if _is_complete_state(current_scene):
            break

    if correction_steps and not _is_complete_state(current_scene):
        run_status = "ERR_EXECUTION_FAIL"

    metrics = compute_metrics(
        before_scene.model_dump(mode="json"),
        current_scene.model_dump(mode="json"),
        critic_latency_ms=int(total_critic_latency_ms),
        execution_latency_ms=int(total_execution_latency_ms),
        fallback_used=latest_decision.fallback_used,
        error_code=latest_decision.error_code,
    )
    metrics["run_status"] = run_status

    overlay_payload = build_overlay_payload(before_scene.model_dump(mode="json"), latest_decision, metrics)

    demo_run = {
        "run_id": run_id,
        "seed": seed,
        "mode": mode,
        "loop_iterations": loop_iterations,
        "scene_state": before_scene.model_dump(mode="json"),
        "decision_source": latest_decision.source,
        "fallback_used": latest_decision.fallback_used,
        "error_code": latest_decision.error_code,
        "correction_steps": correction_steps,
        "critic": {
            "source": latest_decision.source,
            "reason": latest_decision.reason,
            "target_object": latest_decision.target_object,
            "plan": latest_plan,
            "fallback_used": latest_decision.fallback_used,
            "error_code": latest_decision.error_code,
            "latency_ms": metrics["critic_latency_ms"],
            "run_status": run_status,
        },
        "execution": {
            "status": run_status,
            "total_steps": len(correction_steps),
            "step_frames": [step["image_path"] for step in correction_steps],
            "execution_latency_ms": metrics["execution_latency_ms"],
        },
        "metrics": metrics,
        "overlay": overlay_payload,
        "run_status": run_status,
    }

    (artifact_dir / "scene_before.json").write_text(
        json.dumps(before_scene.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "scene_after.json").write_text(
        json.dumps(current_scene.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "scene_steps.json").write_text(
        json.dumps(correction_steps, indent=2),
        encoding="utf-8",
    )
    (artifact_dir / "overlay.json").write_text(json.dumps(overlay_payload, indent=2), encoding="utf-8")
    (artifact_dir / "demo_run.json").write_text(json.dumps(demo_run, indent=2), encoding="utf-8")

    return {
        "status": run_status,
        "artifact_dir": str(artifact_dir),
        "run_id": run_id,
        "decision_source": latest_decision.source,
        "correction_steps": correction_steps,
    }


def _build_default_decision(scene: SceneState):
    from src.demo.critic import CriticDecision

    return CriticDecision(
        is_disordered=False,
        reason="scene already ordered",
        target_object=scene.object_id,
        plan=[],
    )


def _is_complete_state(scene: SceneState) -> bool:
    return is_complete_state(
        yaw_deg=scene.yaw_before_deg,
        target_yaw_deg=scene.target_yaw_deg,
        position_error_cm=scene.position_error_before_cm,
        yaw_threshold_deg=LOOP_YAW_ERROR_DEG_THRESHOLD,
        position_error_threshold_cm=LOOP_POSITION_ERROR_CM_THRESHOLD,
    )


def _resolve_loop_limit(max_loop_steps: int | None) -> int:
    if max_loop_steps is not None:
        limit = max_loop_steps
    else:
        raw = os.environ.get("NEBIUS_MAX_LOOP_STEPS", str(DEFAULT_LOOP_STEPS))
        try:
            limit = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid NEBIUS_MAX_LOOP_STEPS value") from exc

    if limit < 1:
        raise ValueError("max_loop_steps must be >= 1")
    return limit


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


def _build_critic(mode: str) -> NebiusCritic:
    if mode in {"dry-run", "mocked-nebius"}:
        return NebiusCritic(transport=_mocked_transport)
    if mode == "cache-only":
        return NebiusCritic(transport=_timeout_transport)
    if mode in {"live-nebius", "live-or-cache", "release"}:
        return NebiusCritic()
    raise ValueError(f"unsupported mode: {mode}")
