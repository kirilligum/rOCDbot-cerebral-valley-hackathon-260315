# TEST-014
from __future__ import annotations

import json

import pytest

from tests.conftest import REPO_ROOT


@pytest.mark.parametrize("case_name", [pytest.param("critic_schema", id="TEST-014")])
def test_critic_schema_contract(case_name: str) -> None:
    assert case_name == "critic_schema"

    from src.demo.critic import NebiusCritic, validate_critic_payload
    from src.demo.scene_state import SceneState

    prepared = json.loads((REPO_ROOT / "tests" / "fixtures" / "scene_state" / "prepared_seed_7.json").read_text(encoding="utf-8"))
    scene = SceneState.model_validate(prepared)

    invalid = json.loads((REPO_ROOT / "tests" / "fixtures" / "critic" / "invalid_decision.json").read_text(encoding="utf-8"))

    with pytest.raises(ValueError):
        validate_critic_payload(invalid)

    def invalid_transport(_: dict) -> dict:
        return invalid

    critic = NebiusCritic(transport=invalid_transport)
    decision = critic.evaluate(scene)
    assert decision.source == "cache"
    assert decision.error_code == "ERR_NEBIUS_SCHEMA"
