# TEST-001
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT


@pytest.mark.parametrize("case_name", [pytest.param("scene_state", id="TEST-001")])
def test_scene_state_schema_contract(case_name: str) -> None:
    assert case_name == "scene_state"

    from src.demo.scene_state import SceneState

    fixture_path = REPO_ROOT / "tests" / "fixtures" / "scene_state" / "prepared_seed_7.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    scene = SceneState.model_validate(payload)

    assert scene.seed == 7
    assert scene.object_id == "book_1"
    assert scene.table_axis_deg == 0.0
    assert scene.yaw_before_deg == pytest.approx(28.0)
    assert scene.target_yaw_deg == pytest.approx(0.0)
    assert scene.position_error_before_cm >= 0
    assert scene.mode in {"fixture", "headless-scripted", "live-or-cache", "release"}
    assert scene.schema_version == "1.0"
