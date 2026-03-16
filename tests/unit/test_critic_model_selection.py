# TEST-013
from __future__ import annotations

import json

import pytest

from tests.conftest import REPO_ROOT


@pytest.mark.parametrize("case_name", [pytest.param("critic_model", id="TEST-013")])
def test_critic_model_selection(case_name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    assert case_name == "critic_model"

    from src.demo.critic import NebiusCritic
    from src.demo.scene_state import SceneState

    monkeypatch.setenv("NEBIUS_TOKEN_FACTORY_TEXT_MODEL", "moonshotai/Kimi-K2.5")
    monkeypatch.setenv("NEBIUS_TOKEN_FACTORY_API_KEY", "demo")
    monkeypatch.setenv("NEBIUS_TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")

    scene_payload = json.loads((REPO_ROOT / "tests" / "fixtures" / "scene_state" / "prepared_seed_7.json").read_text(encoding="utf-8"))
    valid_decision = json.loads((REPO_ROOT / "tests" / "fixtures" / "critic" / "valid_decision.json").read_text(encoding="utf-8"))
    scene = SceneState.model_validate(scene_payload)

    captured: dict[str, object] = {}

    def transport(payload: dict) -> dict:
        captured["payload"] = payload
        return valid_decision

    critic = NebiusCritic(transport=transport)
    critic.evaluate(scene)

    request_payload = captured["payload"]
    assert isinstance(request_payload, dict)
    assert request_payload["model"] == "moonshotai/Kimi-K2.5"
