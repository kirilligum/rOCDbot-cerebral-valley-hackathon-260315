"""Planner mapping from critic decisions to executable primitives."""

from __future__ import annotations

from src.demo.contracts import ALLOWED_PLAN
from src.demo.critic import CriticDecision


def map_decision_to_plan(decision: CriticDecision) -> list[str]:
    if not decision.is_disordered:
        return []
    if decision.plan != ALLOWED_PLAN:
        raise ValueError(f"unsupported plan: {decision.plan}")
    return list(decision.plan)
