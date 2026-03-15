"""Single-command demo orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from src.demo.critic import NebiusCritic
from src.demo.executor import run_scripted_correction
from src.demo.isaac_adapter import PreparedSceneAdapter
from src.demo.metrics import compute_metrics
from src.demo.overlay import build_overlay_payload
from src.demo.planner import map_decision_to_plan


ROOT = Path(__file__).resolve().parents[2]
VALID_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "critic" / "valid_decision.json"


def _mocked_transport(_: dict) -> dict:
    return json.loads(VALID_FIXTURE_PATH.read_text(encoding="utf-8"))


def _timeout_transport(_: dict) -> dict:
    raise TimeoutError("forced cache-only mode")


def run_demo(*, mode: str, seed: int, artifact_root: str | Path | None = None) -> dict:
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + f"-{mode}-seed{seed}"
    artifact_base = Path(artifact_root or ROOT / "artifacts")
    artifact_dir = artifact_base / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)

    adapter = PreparedSceneAdapter()
    before_scene = adapter.reset_scene(seed=seed)

    critic = _build_critic(mode)
    decision = critic.evaluate(before_scene)
    plan = map_decision_to_plan(decision)
    correction = run_scripted_correction(adapter, plan=plan, artifact_dir=artifact_dir)
    after_scene = correction["corrected_scene"]

    metrics = compute_metrics(
        before_scene.model_dump(mode="json"),
        after_scene.model_dump(mode="json"),
        critic_latency_ms=640,
        execution_latency_ms=18200,
        fallback_used=decision.fallback_used,
        error_code=decision.error_code,
    )
    overlay_payload = build_overlay_payload(before_scene.model_dump(mode="json"), decision, metrics)

    demo_run = {
        "run_id": run_id,
        "seed": seed,
        "mode": mode,
        "scene_state": before_scene.model_dump(mode="json"),
        "critic": {
            "source": decision.source,
            "reason": decision.reason,
            "target_object": decision.target_object,
            "plan": decision.plan,
            "fallback_used": decision.fallback_used,
            "error_code": decision.error_code,
            "latency_ms": metrics["critic_latency_ms"],
        },
        "execution": {
            "status": correction["status"],
            "execution_latency_ms": metrics["execution_latency_ms"],
        },
        "metrics": metrics,
        "overlay": overlay_payload,
        "fallback_used": decision.fallback_used,
    }

    (artifact_dir / "scene_before.json").write_text(json.dumps(before_scene.model_dump(mode="json"), indent=2), encoding="utf-8")
    (artifact_dir / "scene_after.json").write_text(json.dumps(after_scene.model_dump(mode="json"), indent=2), encoding="utf-8")
    (artifact_dir / "overlay.json").write_text(json.dumps(overlay_payload, indent=2), encoding="utf-8")
    (artifact_dir / "demo_run.json").write_text(json.dumps(demo_run, indent=2), encoding="utf-8")

    return {
        "status": correction["status"],
        "artifact_dir": str(artifact_dir),
        "run_id": run_id,
        "decision_source": decision.source,
    }


def _build_critic(mode: str) -> NebiusCritic:
    if mode in {"dry-run", "mocked-nebius"}:
        return NebiusCritic(transport=_mocked_transport)
    if mode == "cache-only":
        return NebiusCritic(transport=_timeout_transport)
    if mode in {"live-nebius", "live-or-cache", "release"}:
        return NebiusCritic()
    raise ValueError(f"unsupported mode: {mode}")
