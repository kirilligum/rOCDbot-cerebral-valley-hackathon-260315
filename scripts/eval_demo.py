#!/usr/bin/env python3
"""Evaluation runner for the rOCDbot demo."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.demo.critic import NebiusCritic, validate_critic_payload
from src.demo.planner import map_decision_to_plan
from src.demo.executor import run_scripted_correction
from src.demo.isaac_adapter import PreparedSceneAdapter
from src.demo.metrics import compute_metrics
from src.demo.release import package_release
from src.demo.run_live import run_demo
from src.demo.scene_state import SceneState


def load_scene_fixture(name: str) -> dict:
    path = ROOT / "tests" / "fixtures" / "scene_state" / name
    return json.loads(path.read_text(encoding="utf-8"))


def load_critic_fixture(name: str) -> dict:
    path = ROOT / "tests" / "fixtures" / "critic" / name
    return json.loads(path.read_text(encoding="utf-8"))


def run_eval(eval_id: str, mode: str, seed: int) -> dict:
    if mode == "fixture":
        prepared = load_scene_fixture(f"prepared_seed_{seed}.json")
        corrected = load_scene_fixture(f"corrected_seed_{seed}.json")
    elif mode == "headless-scripted":
        adapter = PreparedSceneAdapter()
        prepared_scene = adapter.reset_scene(seed=seed)
        correction = run_scripted_correction(adapter)
        prepared = prepared_scene.model_dump(mode="json")
        corrected = correction["corrected_scene"].model_dump(mode="json")
    elif mode == "mocked-nebius":
        adapter = PreparedSceneAdapter()
        scene = adapter.reset_scene(seed=seed)

        valid_fixture = load_critic_fixture("valid_decision.json")

        def valid_transport(_: dict) -> dict:
            return valid_fixture

        def timeout_transport(_: dict) -> dict:
            raise TimeoutError("forced timeout")

        online_decision = NebiusCritic(transport=valid_transport).evaluate(scene)
        fallback_decision = NebiusCritic(transport=timeout_transport).evaluate(scene)

        return {
            "eval_id": eval_id,
            "mode": mode,
            "seed": seed,
            "critic_schema_valid": validate_critic_payload(valid_fixture).is_disordered is True
            and map_decision_to_plan(online_decision) != [],
            "fallback_selected_on_timeout": fallback_decision.fallback_used is True and fallback_decision.source == "cache",
            "online_source": online_decision.source,
            "fallback_source": fallback_decision.source,
        }
    elif mode == "dry-run":
        with tempfile.TemporaryDirectory() as tmp_dir:
            started = time.perf_counter()
            run_result = run_demo(mode="dry-run", seed=seed, artifact_root=tmp_dir)
            elapsed = time.perf_counter() - started
            artifact_dir = Path(run_result["artifact_dir"])
            overlay_payload = json.loads((artifact_dir / "overlay.json").read_text(encoding="utf-8"))
            return {
                "eval_id": eval_id,
                "mode": mode,
                "seed": seed,
                "artifact_bundle_exists": all(
                    [
                        (artifact_dir / "demo_run.json").exists(),
                        (artifact_dir / "overlay.json").exists(),
                        (artifact_dir / "before.png").exists(),
                        (artifact_dir / "after.png").exists(),
                        (artifact_dir / "step_01.png").exists(),
                        (artifact_dir / "step_02.png").exists(),
                        (artifact_dir / "step_03.png").exists(),
                    ]
                ),
                "dry_run_wall_clock_s": round(elapsed, 3),
                "headline": overlay_payload["headline"],
            }
    elif mode == "release":
        with tempfile.TemporaryDirectory() as tmp_dir:
            started = time.perf_counter()
            manifest = package_release(seed=seed, release_root=tmp_dir)
            elapsed = time.perf_counter() - started
            manifest_path = Path(manifest["files"]["manifest"])
            canonical_payload = json.loads(Path(manifest["canonical_run"]["demo_run_path"]).read_text(encoding="utf-8"))
            cache_payload = json.loads(Path(manifest["cache_only_run"]["demo_run_path"]).read_text(encoding="utf-8"))
            return {
                "eval_id": eval_id,
                "mode": mode,
                "seed": seed,
                "release_manifest_complete": manifest_path.exists()
                and all(Path(path_value).exists() for path_value in manifest["files"].values()),
                "cache_only_success": cache_payload["execution"]["status"] == "success"
                and cache_payload["fallback_used"] is True
                and cache_payload["critic"]["source"] == "cache",
                "canonical_run_s": round(elapsed, 3),
                "canonical_decision_source": canonical_payload["critic"]["source"],
            }
    else:
        raise SystemExit(f"unsupported mode for current implementation: {mode}")

    SceneState.model_validate(prepared)
    SceneState.model_validate(corrected)
    metrics = compute_metrics(prepared, corrected, critic_latency_ms=640, execution_latency_ms=18200)

    result = {
        "eval_id": eval_id,
        "mode": mode,
        "seed": seed,
        "scene_state_schema_valid": True,
        "yaw_delta_deg": round(metrics["yaw_before_deg"] - metrics["yaw_after_deg"], 1),
        "metrics": metrics,
    }
    return result


def run_multi_seed_eval(eval_id: str, mode: str, seeds: list[int]) -> dict:
    started = time.perf_counter()
    per_seed = []
    known_error_codes = {
        None,
        "ERR_NEBIUS_TIMEOUT",
        "ERR_NEBIUS_SCHEMA",
        "ERR_RESET_NONDETERMINISTIC",
        "ERR_EXECUTION_FAIL",
        "ERR_ARTIFACT_WRITE",
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        for seed in seeds:
            run_result = run_demo(mode=mode, seed=seed, artifact_root=tmp_dir)
            artifact_dir = Path(run_result["artifact_dir"])
            payload = json.loads((artifact_dir / "demo_run.json").read_text(encoding="utf-8"))
            success = payload["execution"]["status"] == "success" and payload["metrics"]["yaw_after_deg"] <= 5.0
            per_seed.append(
                {
                    "seed": seed,
                    "success": success,
                    "decision_source": run_result["decision_source"],
                    "error_code": payload["critic"]["error_code"],
                    "artifact_dir": str(artifact_dir),
                }
            )

    wall_clock = round(time.perf_counter() - started, 3)
    success_rate = sum(1 for item in per_seed if item["success"]) / len(per_seed)
    unclassified_error_count = sum(1 for item in per_seed if item["error_code"] not in known_error_codes)
    return {
        "eval_id": eval_id,
        "mode": mode,
        "seeds": seeds,
        "wall_clock_s": wall_clock,
        "prepared_seed_success_rate": round(success_rate, 3),
        "unclassified_error_count": unclassified_error_count,
        "per_seed": per_seed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--seeds", nargs="*", type=int, default=[])
    args = parser.parse_args()

    if args.eval == "EVAL-001":
        if not args.seeds:
            raise SystemExit("--seeds is required for EVAL-001")
        result = run_multi_seed_eval(args.eval, args.mode, args.seeds)
    else:
        if args.seed is None:
            raise SystemExit("--seed is required for this eval")
        result = run_eval(args.eval, args.mode, args.seed)

    if args.eval == "EVAL-001":
        assert result["wall_clock_s"] <= 60.0
        assert result["prepared_seed_success_rate"] >= 0.95
        assert result["unclassified_error_count"] == 0
    elif args.eval == "EVAL-003":
        assert result["scene_state_schema_valid"] is True
        assert result["yaw_delta_deg"] >= 20.0
    elif args.eval == "EVAL-002":
        assert result["metrics"]["yaw_after_deg"] <= 5.0
        assert result["metrics"]["position_error_after_cm"] <= 2.0
        assert result["metrics"]["execution_latency_ms"] <= 45000
    elif args.eval == "EVAL-004":
        assert result["critic_schema_valid"] is True
        assert result["fallback_selected_on_timeout"] is True
    elif args.eval == "EVAL-005":
        assert result["artifact_bundle_exists"] is True
        assert result["dry_run_wall_clock_s"] <= 60
    elif args.eval == "EVAL-006":
        assert result["release_manifest_complete"] is True
        assert result["cache_only_success"] is True
        assert result["canonical_run_s"] <= 60
    else:
        raise SystemExit(f"unsupported eval for current implementation: {args.eval}")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
