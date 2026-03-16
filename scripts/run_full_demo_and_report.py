#!/usr/bin/env python3
"""Run demo, build release bundle, and print judge-ready generated-file inventory."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.demo.release import DEFAULT_RELEASE_ROOT, package_release
from src.demo.run_live import run_demo


def _print_inventory(manifest: dict[str, object], run_result: dict[str, object]) -> None:
    files = manifest["files"]
    release_root = Path(files["manifest"]).parent

    def _ensure_step_alias(step_name: str, source: Path) -> Path:
        alias = release_root / f"{step_name}.png"
        if source.exists() and not alias.exists():
            try:
                shutil.copy2(source, alias)
            except OSError:
                alias = source
        return alias

    run_dir = Path(run_result["artifact_dir"])
    canonical_files = [
        ("demo run artifact bundle", run_dir),
        ("demo manifest bundle", Path(files["manifest"])),
        ("operator notes", Path(files["operator_notes"])),
        ("cached critic snapshot", Path(files["cache_snapshot"])),
        ("judge transcript", Path(files["judge_conversation"])),
        ("judge script", Path(files["judge_script"])),
        ("judge log", Path(files["judge_log"])),
        ("judge timeline image stream", Path(files["judge_story_gif"])),
        ("step_0 image", _ensure_step_alias("step_0", Path(files["canonical_before"]))),
        ("step_1 image", _ensure_step_alias("step_1", Path(files["canonical_intermediate"]))),
        ("step_2 image", _ensure_step_alias("step_2", Path(files["canonical_aligned"]))),
        ("step_3 image", _ensure_step_alias("step_3", Path(files["canonical_after"]))),
        ("run scene before", run_dir / "scene_before.json"),
        ("run scene after", run_dir / "scene_after.json"),
        ("run step trace", run_dir / "scene_steps.json"),
        ("run overlay", run_dir / "overlay.json"),
        ("run json payload", run_dir / "demo_run.json"),
    ]

    print("\nGenerated files:")
    for index, (label, path) in enumerate(canonical_files, start=1):
        exists = "exists" if path.exists() else "missing"
        print(f"{index:02d}. {label}: {exists}")
        print(f"    target: {path}")

    step_images = sorted(run_dir.glob("step_*.png"))
    if step_images:
        for position, path in enumerate(step_images, start=1):
            print(f"{len(canonical_files) + position:02d}. run step image {position}: exists")
            print(f"    target: {path}")

    # include release folder summary for judges that want everything exported
    print(f"{len(canonical_files) + len(step_images) + 1:02d}. release folder: exists")
    print(f"    target: {release_root}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["dry-run", "mocked-nebius", "live-nebius", "live-or-cache", "release", "cache-only"], default="live-or-cache")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--artifact-root", default=str(ROOT / "artifacts"))
    parser.add_argument("--release-root", default=str(DEFAULT_RELEASE_ROOT))
    args = parser.parse_args()

    print("1) Running demo...")
    run_result = run_demo(mode=args.mode, seed=args.seed, artifact_root=args.artifact_root)
    print(f"    status: {run_result['status']}")
    print(f"    run id: {run_result['run_id']}")
    print(f"    decision source: {run_result['decision_source']}")
    print(f"    run artifact dir: {run_result['artifact_dir']}")

    print("2) Building release bundle...")
    manifest = package_release(seed=args.seed, release_root=args.release_root)
    print(f"    manifest: {manifest['files']['manifest']}")

    print("3) Listing generated files with explanation")
    _print_inventory(manifest, run_result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
