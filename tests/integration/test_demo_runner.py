# TEST-008
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.parametrize("case_name", [pytest.param("demo_runner", id="TEST-008")])
def test_demo_runner_artifact_bundle(case_name: str, tmp_path: Path) -> None:
    assert case_name == "demo_runner"

    from src.demo.run_live import run_demo

    result = run_demo(mode="dry-run", seed=7, artifact_root=tmp_path)

    artifact_dir = Path(result["artifact_dir"])
    assert result["status"] == "success"
    assert artifact_dir.exists()
    assert (artifact_dir / "demo_run.json").exists()
    assert (artifact_dir / "overlay.json").exists()
    assert (artifact_dir / "before.png").exists()
    assert (artifact_dir / "after.png").exists()
    assert Path("scripts/run_demo.py").exists()
