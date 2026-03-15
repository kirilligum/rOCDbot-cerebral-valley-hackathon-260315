"""Canonical scene-state contracts for the rOCDbot demo."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class SceneState(BaseModel):
    """Single-object tabletop state used by the demo critic and scorer."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0")
    seed: int
    mode: str
    object_id: str
    table_axis_deg: float
    yaw_before_deg: float
    target_yaw_deg: float
    position_error_before_cm: float
    object_center_xy_cm: tuple[float, float]
    target_center_xy_cm: tuple[float, float]

    @classmethod
    def from_path(cls, path: str | Path) -> "SceneState":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(payload)

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
