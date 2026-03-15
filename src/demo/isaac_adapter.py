"""Prepared-scene adapter matching the future Isaac runtime contract.

The current workspace does not expose an NVIDIA/Isaac runtime, so this module
implements the same contract with a deterministic local prepared-scene backend.
The orchestration layer can later swap to a real Isaac-backed adapter without
changing planner, metrics, or artifact code.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw
from pydantic import BaseModel, ConfigDict

from src.demo.scene_state import SceneState


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ASSET_PATH = ROOT / "assets" / "scenes" / "prepared_tabletop_alignment.json"


class SeedConfig(BaseModel):
    object_center_xy_cm: tuple[float, float]
    yaw_deg: float


class RenderConfig(BaseModel):
    width_px: int
    height_px: int
    scale_px_per_cm: int
    origin_px: tuple[int, int]


class PreparedSceneAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    scene_id: str
    object_id: str
    table_axis_deg: float
    target_yaw_deg: float
    target_center_xy_cm: tuple[float, float]
    settled_offset_xy_cm: tuple[float, float]
    settled_yaw_deg: float
    render: RenderConfig
    seeds: dict[str, SeedConfig]


class PreparedSceneAdapter:
    """Deterministic prepared-scene backend for local testing and demo generation."""

    def __init__(self, asset_path: str | Path | None = None) -> None:
        asset_source = Path(asset_path or DEFAULT_ASSET_PATH)
        payload = json.loads(asset_source.read_text(encoding="utf-8"))
        self.asset = PreparedSceneAsset.model_validate(payload)
        self._scene: SceneState | None = None
        self._grasped = False
        self._last_seed: int | None = None

    def reset_scene(self, seed: int) -> SceneState:
        seed_key = str(seed)
        if seed_key not in self.asset.seeds:
            raise KeyError(f"unsupported prepared seed: {seed}")
        state = self.asset.seeds[seed_key]
        self._grasped = False
        self._last_seed = seed
        self._scene = SceneState(
            schema_version=self.asset.schema_version,
            seed=seed,
            mode="headless-scripted",
            object_id=self.asset.object_id,
            table_axis_deg=self.asset.table_axis_deg,
            yaw_before_deg=state.yaw_deg,
            target_yaw_deg=self.asset.target_yaw_deg,
            position_error_before_cm=self._distance_cm(state.object_center_xy_cm, self.asset.target_center_xy_cm),
            object_center_xy_cm=state.object_center_xy_cm,
            target_center_xy_cm=self.asset.target_center_xy_cm,
        )
        return self.read_scene_state()

    def read_scene_state(self) -> SceneState:
        if self._scene is None:
            raise RuntimeError("scene has not been reset")
        return SceneState.model_validate(self._scene.model_dump())

    def execute_plan(self, plan: Iterable[str]) -> SceneState:
        expected = ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]
        plan_list = list(plan)
        if plan_list != expected:
            raise ValueError(f"unsupported plan sequence: {plan_list}")
        if self._scene is None:
            raise RuntimeError("scene has not been reset")

        self._grasped = True
        settled_xy = (
            round(self.asset.target_center_xy_cm[0] + self.asset.settled_offset_xy_cm[0], 1),
            round(self.asset.target_center_xy_cm[1] + self.asset.settled_offset_xy_cm[1], 1),
        )
        self._scene = SceneState(
            schema_version=self.asset.schema_version,
            seed=self._scene.seed,
            mode="headless-scripted",
            object_id=self.asset.object_id,
            table_axis_deg=self.asset.table_axis_deg,
            yaw_before_deg=self.asset.settled_yaw_deg,
            target_yaw_deg=self.asset.target_yaw_deg,
            position_error_before_cm=self._distance_cm(settled_xy, self.asset.target_center_xy_cm),
            object_center_xy_cm=settled_xy,
            target_center_xy_cm=self.asset.target_center_xy_cm,
        )
        self._grasped = False
        return self.read_scene_state()

    def capture_frame(self, path: str | Path, *, title: str | None = None) -> Path:
        scene = self.read_scene_state()
        render = self.asset.render
        image = Image.new("RGB", (render.width_px, render.height_px), "#f6f1e8")
        draw = ImageDraw.Draw(image, "RGBA")

        self._draw_table(draw, render)
        self._draw_axis(draw, render, self.asset.target_center_xy_cm, self.asset.table_axis_deg, "#6e7d71")
        self._draw_object(draw, render, self.asset.target_center_xy_cm, self.asset.target_yaw_deg, fill="#b7d9f5", outline="#6288aa", alpha=80)
        self._draw_object(draw, render, scene.object_center_xy_cm, scene.yaw_before_deg, fill="#d97941", outline="#71361b", alpha=255)

        if title:
            draw.text((24, 24), title, fill="#1a1a1a")
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        return output_path

    @staticmethod
    def _distance_cm(a: tuple[float, float], b: tuple[float, float]) -> float:
        return round(math.hypot(a[0] - b[0], a[1] - b[1]), 1)

    @staticmethod
    def _to_px(render: RenderConfig, xy_cm: tuple[float, float]) -> tuple[float, float]:
        ox, oy = render.origin_px
        return ox + xy_cm[0] * render.scale_px_per_cm, oy - xy_cm[1] * render.scale_px_per_cm

    def _draw_table(self, draw: ImageDraw.ImageDraw, render: RenderConfig) -> None:
        ox, oy = render.origin_px
        half_w = 320
        half_h = 180
        draw.rounded_rectangle((ox - half_w, oy - half_h, ox + half_w, oy + half_h), radius=20, fill="#d4be98", outline="#8d6e4e", width=4)

    def _draw_axis(self, draw: ImageDraw.ImageDraw, render: RenderConfig, xy_cm: tuple[float, float], yaw_deg: float, color: str) -> None:
        cx, cy = self._to_px(render, xy_cm)
        line_len = 140
        theta = math.radians(-yaw_deg)
        dx = math.cos(theta) * line_len
        dy = math.sin(theta) * line_len
        draw.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=color, width=3)

    def _draw_object(
        self,
        draw: ImageDraw.ImageDraw,
        render: RenderConfig,
        xy_cm: tuple[float, float],
        yaw_deg: float,
        *,
        fill: str,
        outline: str,
        alpha: int,
    ) -> None:
        cx, cy = self._to_px(render, xy_cm)
        half_w = 70
        half_h = 35
        theta = math.radians(-yaw_deg)
        corners = [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]
        points: list[tuple[float, float]] = []
        for x, y in corners:
            rx = x * math.cos(theta) - y * math.sin(theta)
            ry = x * math.sin(theta) + y * math.cos(theta)
            points.append((cx + rx, cy + ry))
        rgba_fill = ImageColorCache.to_rgba(fill, alpha)
        draw.polygon(points, fill=rgba_fill, outline=outline)
        accent_start = points[0]
        accent_end = points[1]
        draw.line((accent_start, accent_end), fill="#fff7ec", width=6)


class ImageColorCache:
    @staticmethod
    def to_rgba(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[index : index + 2], 16) for index in (0, 2, 4)) + (alpha,)
