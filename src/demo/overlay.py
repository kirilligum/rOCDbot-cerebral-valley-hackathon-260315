"""Overlay payload generation for the rOCDbot demo."""

from __future__ import annotations

from typing import Any

from src.demo.critic import CriticDecision


def build_overlay_payload(prepared: dict[str, Any], decision: CriticDecision, metrics: dict[str, Any]) -> dict[str, str]:
    before = metrics["yaw_before_deg"]
    after = metrics["yaw_after_deg"]
    return {
        "headline": f"Detected disorder: {prepared['object_id']} rotated {before:.1f} deg off axis",
        "reason": decision.reason,
        "plan": " -> ".join(decision.plan),
        "metric_delta": f"yaw error {before:.1f} deg -> {after:.1f} deg | score {metrics['order_score_before']:.2f} -> {metrics['order_score_after']:.2f}",
    }
