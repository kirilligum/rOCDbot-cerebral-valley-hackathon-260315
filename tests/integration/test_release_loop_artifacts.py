# TEST-017
from __future__ import annotations

from pathlib import Path

import json

import pytest


@pytest.mark.parametrize("case_name", [pytest.param("release_loop", id="TEST-017")])
def test_release_loop_artifacts(case_name: str, tmp_path: Path) -> None:
    assert case_name == "release_loop"

    from src.demo.release import package_release

    manifest = package_release(seed=7, release_root=tmp_path)
    canonical_path = Path(manifest["canonical_run"]["demo_run_path"])
    payload = json.loads(canonical_path.read_text(encoding="utf-8"))

    assert payload["execution"]["status"] == "success"
    assert len(payload["correction_steps"]) >= 1
    required = {"loop_iteration", "decision_source", "step_metrics", "image_path", "scene_state"}

    for step in payload["correction_steps"]:
        assert required.issubset(set(step.keys()))
        assert "yaw_after_deg" in step["step_metrics"]
        assert "position_error_after_cm" in step["step_metrics"]

    files = manifest["files"]
    for path_value in files.values():
        assert Path(path_value).exists()
