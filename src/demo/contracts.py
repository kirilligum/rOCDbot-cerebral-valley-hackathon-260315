"""Shared contracts for critic planning and prompt generation."""

from __future__ import annotations


ALLOWED_PLAN = ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]
CRITIC_SYSTEM_PROMPT = (
    "You are an order critic for a tabletop robot. "
    "Return strict JSON with keys is_disordered, reason, target_object, and plan."
)
