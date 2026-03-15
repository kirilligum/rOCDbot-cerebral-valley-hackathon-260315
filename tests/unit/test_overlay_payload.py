# TEST-007
from __future__ import annotations

import json

import pytest

from tests.conftest import REPO_ROOT


@pytest.mark.parametrize("case_name", [pytest.param("overlay", id="TEST-007")])
def test_overlay_payload_legibility(case_name: str) -> None:
    assert case_name == "overlay"

    from src.demo.critic import validate_critic_payload
    from src.demo.metrics import compute_metrics
    from src.demo.overlay import build_overlay_payload

    prepared = json.loads((REPO_ROOT / "tests" / "fixtures" / "scene_state" / "prepared_seed_7.json").read_text(encoding="utf-8"))
    corrected = json.loads((REPO_ROOT / "tests" / "fixtures" / "scene_state" / "corrected_seed_7.json").read_text(encoding="utf-8"))
    decision = validate_critic_payload(json.loads((REPO_ROOT / "tests" / "fixtures" / "critic" / "valid_decision.json").read_text(encoding="utf-8")))
    metrics = compute_metrics(prepared, corrected, critic_latency_ms=640, execution_latency_ms=18200)

    payload = build_overlay_payload(prepared, decision, metrics)

    assert payload["headline"].startswith("Detected disorder")
    assert "rotated away from the table axis" in payload["reason"]
    assert "approach -> grasp" in payload["plan"]
    assert "28.0" in payload["metric_delta"]
