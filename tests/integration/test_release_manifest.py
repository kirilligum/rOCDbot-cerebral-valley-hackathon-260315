# TEST-011
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize("case_name", [pytest.param("release_manifest", id="TEST-011")])
def test_release_manifest_complete(case_name: str, tmp_path: Path) -> None:
    assert case_name == "release_manifest"

    release_root = tmp_path / "release"
    completed = subprocess.run(
        [
            "python3",
            "scripts/package_demo.py",
            "--seed",
            "7",
            "--release-root",
            str(release_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    manifest_path = release_root / "demo_manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest["files"]
    for path_value in files.values():
        assert Path(path_value).exists()

    assert manifest["canonical_run"]["decision_source"] in {"live", "cache"}
    assert manifest["cache_only_run"]["decision_source"] == "cache"
    assert manifest["cache_only_run"]["fallback_used"] is True
    assert "judge_conversation" in files
    assert "judge_script" in files
    assert "judge_log" in files
    assert "judge_story_gif" in files
    assert "demo_presentation" in files
    assert "canonical_intermediate" in files
    assert "canonical_aligned" in files
