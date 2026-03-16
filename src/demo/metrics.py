"""Metric helpers for the rOCDbot demo."""

from __future__ import annotations

import math
from typing import Any


def _planar_distance_cm(object_xy: tuple[float, float], target_xy: tuple[float, float]) -> float:
    return math.hypot(object_xy[0] - target_xy[0], object_xy[1] - target_xy[1])


def _order_score(yaw_error_deg: float, position_error_cm: float) -> float:
    normalized = 1.0 - min(1.0, (abs(yaw_error_deg) / 30.0) * 0.7 + (position_error_cm / 5.0) * 0.3)
    return round(normalized, 2)


def compute_metrics(
    prepared: dict[str, Any],
    corrected: dict[str, Any],
    *,
    critic_latency_ms: int,
    execution_latency_ms: int,
    fallback_used: bool = False,
    error_code: str | None = None,
) -> dict[str, Any]:
    before_xy = tuple(prepared["object_center_xy_cm"])
    before_target_xy = tuple(prepared["target_center_xy_cm"])
    after_xy = tuple(corrected["object_center_xy_cm"])
    after_target_xy = tuple(corrected["target_center_xy_cm"])

    yaw_before_deg = float(prepared["yaw_before_deg"])
    yaw_after_deg = float(corrected["yaw_before_deg"])
    position_error_before_cm = float(prepared["position_error_before_cm"])
    position_error_after_cm = round(_planar_distance_cm(after_xy, after_target_xy), 1)

    return {
        "yaw_before_deg": yaw_before_deg,
        "yaw_after_deg": yaw_after_deg,
        "position_error_before_cm": position_error_before_cm,
        "position_error_after_cm": position_error_after_cm,
        "critic_latency_ms": int(critic_latency_ms),
        "execution_latency_ms": int(execution_latency_ms),
        "order_score_before": _order_score(yaw_before_deg, position_error_before_cm),
        "order_score_after": _order_score(yaw_after_deg, position_error_after_cm),
        "fallback_used": bool(fallback_used),
        "error_code": error_code,
        "run_status": "success",
    }


def compute_step_metrics(
    prepared: dict[str, Any],
    corrected: dict[str, Any],
) -> dict[str, Any]:
    full_metrics = compute_metrics(prepared, corrected, critic_latency_ms=0, execution_latency_ms=0)
    return {
        "yaw_before_deg": full_metrics["yaw_before_deg"],
        "yaw_after_deg": full_metrics["yaw_after_deg"],
        "position_error_before_cm": full_metrics["position_error_before_cm"],
        "position_error_after_cm": full_metrics["position_error_after_cm"],
    }


def is_complete_state(
    *,
    yaw_deg: float,
    target_yaw_deg: float,
    position_error_cm: float,
    yaw_threshold_deg: float,
    position_error_threshold_cm: float,
) -> bool:
    return (
        abs(yaw_deg - target_yaw_deg) <= yaw_threshold_deg
        and position_error_cm <= position_error_threshold_cm
    )
