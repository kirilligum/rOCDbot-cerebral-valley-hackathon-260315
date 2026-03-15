# TEST-002
from __future__ import annotations

import json

import pytest

from tests.conftest import REPO_ROOT


@pytest.mark.parametrize("case_name", [pytest.param("metrics", id="TEST-002")])
def test_metrics_unit_and_error_contract(case_name: str) -> None:
    assert case_name == "metrics"

    from src.demo.metrics import compute_metrics

    prepared_path = REPO_ROOT / "tests" / "fixtures" / "scene_state" / "prepared_seed_7.json"
    corrected_path = REPO_ROOT / "tests" / "fixtures" / "scene_state" / "corrected_seed_7.json"
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    corrected = json.loads(corrected_path.read_text(encoding="utf-8"))

    result = compute_metrics(prepared, corrected, critic_latency_ms=640, execution_latency_ms=18200)

    assert result["yaw_before_deg"] == pytest.approx(28.0)
    assert result["yaw_after_deg"] == pytest.approx(2.0)
    assert result["position_error_before_cm"] == pytest.approx(1.5)
    assert result["position_error_after_cm"] == pytest.approx(0.6)
    assert result["critic_latency_ms"] == 640
    assert result["execution_latency_ms"] == 18200
    assert result["error_code"] is None
