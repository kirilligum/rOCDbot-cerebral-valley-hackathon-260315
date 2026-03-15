"""Nebius-backed order critic with deterministic cache fallback."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.demo.contracts import ALLOWED_PLAN, CRITIC_SYSTEM_PROMPT
from src.demo.scene_state import SceneState


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_PATH = ROOT / "cache" / "critic_response.json"


class CriticDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_disordered: bool
    reason: str
    target_object: str
    plan: list[str]
    source: str = Field(default="live")
    fallback_used: bool = False
    error_code: str | None = None


def validate_critic_payload(payload: dict[str, Any]) -> CriticDecision:
    try:
        decision = CriticDecision.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc
    if decision.plan != ALLOWED_PLAN:
        raise ValueError(f"unsupported primitive plan: {decision.plan}")
    return decision


class NebiusCritic:
    def __init__(
        self,
        *,
        transport: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        cache_path: str | Path = DEFAULT_CACHE_PATH,
    ) -> None:
        self.transport = transport or self._live_transport
        self.cache_path = Path(cache_path)

    def evaluate(self, scene: SceneState) -> CriticDecision:
        payload = self._request_payload(scene)
        try:
            response = self.transport(payload)
            decision = validate_critic_payload(response)
            return decision.model_copy(update={"source": "live", "fallback_used": False, "error_code": None})
        except TimeoutError:
            return self._load_cache(error_code="ERR_NEBIUS_TIMEOUT")
        except (ValueError, urllib.error.URLError, urllib.error.HTTPError):
            return self._load_cache(error_code="ERR_NEBIUS_SCHEMA")

    def _load_cache(self, *, error_code: str) -> CriticDecision:
        payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        decision = validate_critic_payload(payload)
        return decision.model_copy(update={"source": "cache", "fallback_used": True, "error_code": error_code})

    def _request_payload(self, scene: SceneState) -> dict[str, Any]:
        return {
            "model": os.environ.get("NEBIUS_TOKEN_FACTORY_TEXT_MODEL", "moonshotai/Kimi-K2-Instruct"),
            "messages": [
                {
                    "role": "system",
                    "content": CRITIC_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(scene.model_dump(mode="json"), sort_keys=True),
                },
            ],
            "temperature": 0,
            "max_tokens": 200,
        }

    def _live_transport(self, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = self._env("NEBIUS_TOKEN_FACTORY_API_KEY")
        base_url = self._env("NEBIUS_TOKEN_FACTORY_BASE_URL").rstrip("/") + "/chat/completions"
        timeout_s = float(os.environ.get("NEBIUS_CRITIC_TIMEOUT_S", "2.0"))
        request = urllib.request.Request(
            base_url,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
        )
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            parsed = json.load(response)

        content = parsed["choices"][0]["message"]["content"]
        if not content:
            raise ValueError("empty critic content")
        return json.loads(content)

    @staticmethod
    def _env(name: str) -> str:
        value = os.environ.get(name)
        if value:
            return value
        env_path = ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, raw_value = line.split("=", 1)
                if key == name:
                    return raw_value
        raise RuntimeError(f"missing environment variable: {name}")
