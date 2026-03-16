"""Shared contracts for critic planning and prompt generation."""

from __future__ import annotations


ALLOWED_PLAN = ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]
CRITIC_SYSTEM_PROMPT = (
    "You are an order critic for a tabletop robot. "
    "Return strict JSON with keys is_disordered, reason, target_object, and plan."
)

DEFAULT_LOOP_STEPS = 3
LOOP_YAW_ERROR_DEG_THRESHOLD = 5.0
LOOP_POSITION_ERROR_CM_THRESHOLD = 2.0

ALLOWED_CRITIC_ERROR_CODES = {
    None,
    "ERR_NEBIUS_TIMEOUT",
    "ERR_NEBIUS_SCHEMA",
    "ERR_EXECUTION_FAIL",
}
