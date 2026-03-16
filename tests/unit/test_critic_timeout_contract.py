# TEST-024
from __future__ import annotations

import json

import pytest

from tests.conftest import REPO_ROOT

from src.demo.contracts import ALLOWED_CRITIC_ERROR_CODES


@pytest.mark.parametrize("case_name", [pytest.param("critic_timeout", id="TEST-024")])
def test_critic_error_code_stability(case_name: str) -> None:
    assert case_name == "critic_timeout"

    from src.demo.critic import NebiusCritic
    from src.demo.scene_state import SceneState

    scene_payload = json.loads((REPO_ROOT / "tests" / "fixtures" / "scene_state" / "prepared_seed_7.json").read_text(encoding="utf-8"))
    scene = SceneState.model_validate(scene_payload)

    def timeout_transport(_: dict) -> dict:
        raise TimeoutError("forced timeout")

    def schema_transport(_: dict) -> dict:
        return {
            "unexpected": "schema mismatch"
        }

    timeout_decision = NebiusCritic(transport=timeout_transport).evaluate(scene)
    schema_decision = NebiusCritic(transport=schema_transport).evaluate(scene)

    assert timeout_decision.source == "cache"
    assert timeout_decision.fallback_used is True
    assert timeout_decision.error_code == "ERR_NEBIUS_TIMEOUT"
    assert timeout_decision.error_code in ALLOWED_CRITIC_ERROR_CODES

    assert schema_decision.source == "cache"
    assert schema_decision.fallback_used is True
    assert schema_decision.error_code == "ERR_NEBIUS_SCHEMA"
    assert schema_decision.error_code in ALLOWED_CRITIC_ERROR_CODES
