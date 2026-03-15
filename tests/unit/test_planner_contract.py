# TEST-004
from __future__ import annotations

import json

import pytest

from tests.conftest import REPO_ROOT


@pytest.mark.parametrize("case_name", [pytest.param("planner_contract", id="TEST-004")])
def test_critic_and_planner_json_contract(case_name: str) -> None:
    assert case_name == "planner_contract"

    from src.demo.critic import validate_critic_payload
    from src.demo.planner import map_decision_to_plan

    valid_path = REPO_ROOT / "tests" / "fixtures" / "critic" / "valid_decision.json"
    invalid_path = REPO_ROOT / "tests" / "fixtures" / "critic" / "invalid_decision.json"

    valid_payload = json.loads(valid_path.read_text(encoding="utf-8"))
    invalid_payload = json.loads(invalid_path.read_text(encoding="utf-8"))

    decision = validate_critic_payload(valid_payload)
    assert map_decision_to_plan(decision) == ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]

    with pytest.raises(ValueError):
        validate_critic_payload(invalid_payload)
