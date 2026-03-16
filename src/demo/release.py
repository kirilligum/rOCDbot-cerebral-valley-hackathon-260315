"""Release packaging helpers for the hackathon demo."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.demo.judge_story import write_judge_story_package
from src.demo.presentation import write_demo_presentation
from src.demo.run_live import run_demo


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RELEASE_ROOT = ROOT / "artifacts" / "release"
DEFAULT_CACHE_PATH = ROOT / "cache" / "critic_response.json"


def package_release(*, seed: int, release_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(release_root or DEFAULT_RELEASE_ROOT)
    root.mkdir(parents=True, exist_ok=True)

    runs_root = root / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    canonical = run_demo(mode="release", seed=seed, artifact_root=runs_root)
    cache_only = run_demo(mode="cache-only", seed=seed, artifact_root=runs_root)

    canonical_dir = Path(canonical["artifact_dir"])
    cache_dir = Path(cache_only["artifact_dir"])
    canonical_payload = json.loads((canonical_dir / "demo_run.json").read_text(encoding="utf-8"))
    cache_payload = json.loads((cache_dir / "demo_run.json").read_text(encoding="utf-8"))

    canonical_before = root / "canonical_before.png"
    canonical_intermediate = root / "canonical_intermediate.png"
    canonical_aligned = root / "canonical_aligned.png"
    canonical_after = root / "canonical_after.png"
    cache_snapshot = root / "cached_critic_response.json"
    operator_notes = root / "operator_notes.md"
    manifest_path = root / "demo_manifest.json"

    canonical_step_frames = canonical_payload.get("execution", {}).get("step_frames", [])
    shutil.copy2(canonical_dir / "before.png", canonical_before)
    if canonical_step_frames:
        first_step = Path(canonical_step_frames[0])
        second_step = Path(canonical_step_frames[1]) if len(canonical_step_frames) > 1 else None
        third_step = Path(canonical_step_frames[2]) if len(canonical_step_frames) > 2 else None

        if first_step.exists():
            shutil.copy2(first_step, canonical_intermediate)
        elif (canonical_dir / "step_01.png").exists():
            shutil.copy2(canonical_dir / "step_01.png", canonical_intermediate)
        else:
            shutil.copy2(canonical_dir / "after.png", canonical_intermediate)

        if second_step and second_step.exists():
            shutil.copy2(second_step, canonical_aligned)
        elif (canonical_dir / "step_02.png").exists():
            shutil.copy2(canonical_dir / "step_02.png", canonical_aligned)
        else:
            shutil.copy2(canonical_dir / "after.png", canonical_aligned)

        if third_step and third_step.exists():
            shutil.copy2(third_step, canonical_after)
        else:
            shutil.copy2(canonical_dir / "after.png", canonical_after)
    elif (canonical_dir / "step_01.png").exists():
        shutil.copy2(canonical_dir / "step_01.png", canonical_intermediate)
        shutil.copy2(canonical_dir / "step_01.png", canonical_aligned)
        shutil.copy2(canonical_dir / "after.png", canonical_after)
    elif (canonical_dir / "step_1_frame.png").exists():
        shutil.copy2(canonical_dir / "step_1_frame.png", canonical_intermediate)
        if (canonical_dir / "step_2_frame.png").exists():
            shutil.copy2(canonical_dir / "step_2_frame.png", canonical_aligned)
        else:
            shutil.copy2(canonical_dir / "step_1_frame.png", canonical_aligned)
        shutil.copy2(canonical_dir / "after.png", canonical_after)
    else:
        shutil.copy2(canonical_dir / "after.png", canonical_intermediate)
        shutil.copy2(canonical_dir / "after.png", canonical_aligned)
        shutil.copy2(canonical_dir / "after.png", canonical_after)
    shutil.copy2(DEFAULT_CACHE_PATH, cache_snapshot)
    operator_notes.write_text(_build_operator_notes(seed), encoding="utf-8")
    judge_assets = write_judge_story_package(
        root,
        demo_run=canonical_payload,
        before_image=canonical_before,
        after_image=canonical_after,
    )
    conversation = json.loads(Path(judge_assets["judge_conversation"]).read_text(encoding="utf-8"))

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "canonical_run": {
            "artifact_dir": str(canonical_dir),
            "demo_run_path": str(canonical_dir / "demo_run.json"),
            "decision_source": canonical["decision_source"],
            "fallback_used": canonical_payload["fallback_used"],
        },
        "cache_only_run": {
            "artifact_dir": str(cache_dir),
            "demo_run_path": str(cache_dir / "demo_run.json"),
            "decision_source": cache_only["decision_source"],
            "fallback_used": cache_payload["fallback_used"],
        },
        "files": {
            "manifest": str(manifest_path),
            "operator_notes": str(operator_notes),
            "canonical_before": str(canonical_before),
            "canonical_intermediate": str(canonical_intermediate),
            "canonical_aligned": str(canonical_aligned),
            "canonical_after": str(canonical_after),
            "cache_snapshot": str(cache_snapshot),
            **judge_assets,
        },
    }
    is_default_release = root == DEFAULT_RELEASE_ROOT
    presentation_path = ROOT / "README.md" if is_default_release else root / "demo_presentation.md"
    presentation_asset_prefix = "artifacts/release" if is_default_release else ""
    presentation_path = write_demo_presentation(
        presentation_path,
        demo_run=canonical_payload,
        conversation=conversation,
        judge_log_path=judge_assets["judge_log"],
        asset_prefix=presentation_asset_prefix,
    )
    manifest["files"]["demo_presentation"] = presentation_path
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _build_operator_notes(seed: int) -> str:
    return "\n".join(
        [
            "# rOCDbot Demo Operator Notes",
            "",
            f"- Launch command: `python3 scripts/run_demo.py --mode release --seed {seed}`",
            "- Backup command: `python3 scripts/run_demo.py --mode cache-only --seed 7`",
            "- Canonical story beat: detect a rotated tabletop object, explain the disorder, correct it, then show the yaw-error delta.",
            "- Use `judge_script.md` and `judge_story.gif` from the release bundle for the 60-second judge walkthrough.",
            "- Live sequence timing: 5s wrong scene, 10s critique overlay, 25s correction, 10s before/after freeze frame, 10s buffer.",
            "- If Nebius is slow or unavailable, use the packaged cache-only release artifacts and continue the explanation from the manifest.",
        ]
    )
