"""Shared contracts for critic planning and prompt generation."""

from __future__ import annotations


ALLOWED_PLAN = ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]
CRITIC_SYSTEM_PROMPT = (
    "You are an order critic for a tabletop robot. "
    "Return strict JSON only. "
    "Required keys: is_disordered (boolean), reason (string), target_object (string), "
    "plan (array). The plan must be exactly [\"approach\", \"grasp\", \"lift\", \"rotate_to_target\", \"place\", \"settle\"]. "
    "Do not add surrounding prose or markdown. "
    "Set is_disordered to true when either abs(yaw_before_deg - target_yaw_deg) > 3.0 "
    "or position_error_before_cm > 1.0. "
    "If neither condition holds, set is_disordered false."
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
