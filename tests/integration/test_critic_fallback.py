# TEST-005
from __future__ import annotations

import pytest


@pytest.mark.parametrize("case_name", [pytest.param("critic_fallback", id="TEST-005")])
def test_critic_timeout_cache_fallback(case_name: str) -> None:
    assert case_name == "critic_fallback"

    from src.demo.critic import NebiusCritic
    from src.demo.isaac_adapter import PreparedSceneAdapter

    adapter = PreparedSceneAdapter()
    scene = adapter.reset_scene(seed=7)

    def timeout_transport(_: dict) -> dict:
        raise TimeoutError("forced timeout")

    critic = NebiusCritic(transport=timeout_transport)
    decision = critic.evaluate(scene)

    assert decision.source == "cache"
    assert decision.fallback_used is True
    assert decision.error_code == "ERR_NEBIUS_TIMEOUT"
    assert decision.plan == ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]
