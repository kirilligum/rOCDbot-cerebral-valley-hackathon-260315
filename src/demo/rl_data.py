"""RL episode trace conversion utilities."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.demo.contracts import LOOP_POSITION_ERROR_CM_THRESHOLD, LOOP_YAW_ERROR_DEG_THRESHOLD


def write_rl_episode_trace(
    artifact_dir: str | Path,
    *,
    run_id: str,
    seed: int,
    mode: str,
    decision_source: str,
    fallback_used: bool,
    error_code: str | None,
    run_status: str,
    before_scene: dict[str, Any],
    correction_steps: list[dict[str, Any]],
    plan: list[str],
) -> Path:
    artifact_root = Path(artifact_dir)
    artifact_root.mkdir(parents=True, exist_ok=True)

    transitions = _build_rl_transitions(
        run_id=run_id,
        seed=seed,
        mode=mode,
        decision_source=decision_source,
        fallback_used=fallback_used,
        error_code=error_code,
        run_status=run_status,
        before_scene=before_scene,
        correction_steps=correction_steps,
        plan=plan,
    )

    path = artifact_root / "rl_episode.jsonl"
    with path.open("w", encoding="utf-8") as file:
        for transition in transitions:
            file.write(json.dumps(transition, ensure_ascii=False, sort_keys=True))
            file.write("\n")

    return path


def _build_rl_transitions(
    *,
    run_id: str,
    seed: int,
    mode: str,
    decision_source: str,
    fallback_used: bool,
    error_code: str | None,
    run_status: str,
    before_scene: dict[str, Any],
    correction_steps: list[dict[str, Any]],
    plan: list[str],
) -> list[dict[str, Any]]:
    previous_state = dict(before_scene)
    transitions: list[dict[str, Any]] = []

    if not correction_steps:
        transitions.append(
            _build_transition(
                run_id=run_id,
                seed=seed,
                mode=mode,
                decision_source=decision_source,
                fallback_used=fallback_used,
                error_code=error_code,
                run_status=run_status,
                step=0,
                state=previous_state,
                action={"type": "noop", "plan": plan, "loop_iteration": 0},
                next_state=previous_state,
                step_metrics=None,
                done=_is_complete_state(previous_state),
            )
        )
        return transitions

    for step_index, step_payload in enumerate(correction_steps, start=1):
        next_state = dict(step_payload["scene_state"])
        done = _is_complete_state(next_state) and step_index == len(correction_steps)
        transitions.append(
            _build_transition(
                run_id=run_id,
                seed=seed,
                mode=mode,
                decision_source=decision_source,
                fallback_used=fallback_used,
                error_code=error_code,
                run_status=run_status,
                step=step_index,
                state=previous_state,
                action={
                    "type": "scripted_plan",
                    "stage": step_payload.get("stage"),
                    "plan": plan,
                    "loop_iteration": step_payload.get("loop_iteration", 0),
                },
                next_state=next_state,
                step_metrics=step_payload.get("step_metrics"),
                done=done,
            )
        )
        previous_state = next_state

    return transitions


def _build_transition(
    *,
    run_id: str,
    seed: int,
    mode: str,
    decision_source: str,
    fallback_used: bool,
    error_code: str | None,
    run_status: str,
    step: int,
    state: dict[str, Any],
    action: dict[str, Any],
    next_state: dict[str, Any],
    step_metrics: dict[str, Any] | None,
    done: bool,
) -> dict[str, Any]:
    reward = _compute_step_reward(state, next_state, step_metrics)
    return {
        "schema_version": "1.0",
        "record_type": "transition",
        "trace_id": run_id,
        "recorded_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "mode": mode,
        "decision_source": decision_source,
        "fallback_used": fallback_used,
        "error_code": error_code,
        "run_status": run_status,
        "step": step,
        "state": state,
        "action": action,
        "next_state": next_state,
        "step_metrics": step_metrics or {},
        "reward": reward,
        "done": bool(done),
    }


def _compute_step_reward(
    state: dict[str, Any],
    next_state: dict[str, Any],
    step_metrics: dict[str, Any] | None,
) -> dict[str, float]:
    state_yaw = float(state["yaw_before_deg"])
    next_yaw = float(next_state["yaw_before_deg"])
    state_pos_err = float(state["position_error_before_cm"])
    next_pos_err = float(next_state["position_error_before_cm"])

    yaw_improvement = state_yaw - next_yaw
    position_improvement = state_pos_err - next_pos_err
    if step_metrics:
        if "yaw_after_deg" in step_metrics:
            yaw_improvement = state_yaw - float(step_metrics["yaw_after_deg"])
        if "position_error_after_cm" in step_metrics:
            position_improvement = state_pos_err - float(step_metrics["position_error_after_cm"])

    total_reward = round(yaw_improvement + (2.0 * position_improvement), 4)

    return {
        "yaw_improvement_deg": round(yaw_improvement, 3),
        "position_improvement_cm": round(position_improvement, 3),
        "total_reward": total_reward,
    }


def _is_complete_state(state: dict[str, Any]) -> bool:
    yaw_error = abs(float(state["yaw_before_deg"]) - float(state["target_yaw_deg"]))
    pos_error = float(state["position_error_before_cm"])
    return (
        yaw_error <= LOOP_YAW_ERROR_DEG_THRESHOLD
        and pos_error <= LOOP_POSITION_ERROR_CM_THRESHOLD
    )
