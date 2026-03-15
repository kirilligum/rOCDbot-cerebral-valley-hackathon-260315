# TEST-012
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT


@pytest.mark.parametrize("case_name", [pytest.param("judge_story", id="TEST-012")])
def test_judge_story_contains_prompts_responses_and_images(case_name: str, tmp_path: Path) -> None:
    assert case_name == "judge_story"

    from src.demo.judge_story import write_judge_story_package

    manifest_path = REPO_ROOT / "artifacts" / "release" / "demo_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        demo_run_file = Path(manifest["canonical_run"]["demo_run_path"])
        before_image = Path(manifest["files"]["canonical_before"])
        after_image = Path(manifest["files"]["canonical_after"])
        payload = json.loads(demo_run_file.read_text(encoding="utf-8"))
    else:
        from src.demo.run_live import run_demo

        result = run_demo(mode="dry-run", seed=7, artifact_root=tmp_path / "run")
        artifact_dir = Path(result["artifact_dir"])
        payload = json.loads((artifact_dir / "demo_run.json").read_text(encoding="utf-8"))
        before_image = artifact_dir / "before.png"
        after_image = artifact_dir / "after.png"

    files = write_judge_story_package(tmp_path / "story", demo_run=payload, before_image=before_image, after_image=after_image)

    conversation = json.loads(Path(files["judge_conversation"]).read_text(encoding="utf-8"))
    script_text = Path(files["judge_script"]).read_text(encoding="utf-8")
    log_text = Path(files["judge_log"]).read_text(encoding="utf-8")

    assert len(conversation) == 3
    assert "What looks out of place" in conversation[0]["user_prompt"]
    assert "Robot plan:" in conversation[1]["assistant_response"]
    assert "Evaluate how successful the action was" in conversation[2]["user_prompt"]
    assert "Judge Demo Script" in script_text
    assert '"event": "post_action_evaluated"' in log_text
    assert Path(files["judge_story_gif"]).exists()
