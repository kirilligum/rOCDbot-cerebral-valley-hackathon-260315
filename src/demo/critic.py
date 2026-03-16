"""Nebius-backed order critic with deterministic cache fallback."""

from __future__ import annotations

import json
import os
import re
import sys
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
    if "model" in payload:
        raise ValueError("unexpected model field in critic payload")
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
        debug: bool = False,
    ) -> None:
        self.transport = transport or self._live_transport
        self.cache_path = Path(cache_path)
        self.debug = debug

    def evaluate(self, scene: SceneState) -> CriticDecision:
        payload = self._request_payload(scene)
        try:
            self._debug("=== NebiusCritic request ===")
            self._debug(json.dumps(payload, indent=2))
            response = self.transport(payload)
            self._debug("=== NebiusCritic response ===")
            self._debug(json.dumps(response, indent=2))
            response = self._normalize_critic_payload(response, scene=scene)
            decision = validate_critic_payload(response)
            return decision.model_copy(update={"source": "live", "fallback_used": False, "error_code": None})
        except TimeoutError:
            return self._load_cache(scene=scene, error_code="ERR_NEBIUS_TIMEOUT")
        except (ValueError, urllib.error.URLError, urllib.error.HTTPError):
            return self._load_cache(scene=scene, error_code="ERR_NEBIUS_SCHEMA")

    def _validate_cache_response(self, payload: dict[str, Any]) -> CriticDecision:
        decision = validate_critic_payload(payload)
        if decision.source != "cache":
            raise ValueError(f"invalid cached decision source: {decision.source}")
        return decision

    def _load_cache(self, *, scene: SceneState, error_code: str) -> CriticDecision:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return self._fallback_decision(scene=scene, error_code=error_code)

        if not isinstance(payload, dict):
            return self._fallback_decision(scene=scene, error_code=error_code)

        payload.setdefault("source", "cache")
        try:
            payload = self._normalize_critic_payload(payload, scene=scene)
            decision = self._validate_cache_response(payload)
            return decision.model_copy(update={"source": "cache", "fallback_used": True, "error_code": error_code})
        except ValueError:
            return self._fallback_decision(scene=scene, error_code=error_code)

    def _fallback_decision(self, *, scene: SceneState, error_code: str) -> CriticDecision:
        return CriticDecision(
            is_disordered=True,
            reason="Falling back to default correction plan due critic schema/transport error.",
            target_object=scene.object_id,
            plan=ALLOWED_PLAN,
            source="cache",
            fallback_used=True,
            error_code=error_code,
        )

    def _normalize_critic_payload(self, payload: Any, scene: SceneState) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("critic payload must be a JSON object")

        normalized = dict(payload)

        if isinstance(normalized.get("plan"), str):
            normalized["plan"] = ALLOWED_PLAN
        elif normalized.get("plan") is None:
            raise ValueError("missing critic plan")
        elif not isinstance(normalized["plan"], list):
            raise ValueError("critic plan must be a list")

        normalized["is_disordered"] = self._coerce_bool(
            normalized.get("is_disordered"), default=True
        )
        normalized.setdefault("source", "live")
        normalized.setdefault("target_object", scene.object_id)
        normalized.setdefault("reason", "Fallback: using default reason.")

        if not normalized["target_object"]:
            normalized["target_object"] = scene.object_id

        return normalized

    @staticmethod
    def _coerce_bool(value: object, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            text = value.strip().lower()
            if text in {"true", "1", "yes", "y", "on"}:
                return True
            if text in {"false", "0", "no", "n", "off"}:
                return False
        return default

    def _request_payload(self, scene: SceneState) -> dict[str, Any]:
        return {
            "model": os.environ.get("NEBIUS_TOKEN_FACTORY_TEXT_MODEL", "moonshotai/Kimi-K2.5"),
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
            "max_tokens": 32000,
        }

    def _live_transport(self, payload: dict[str, Any]) -> dict[str, Any]:
        api_key = self._env("NEBIUS_TOKEN_FACTORY_API_KEY")
        base_url = self._env("NEBIUS_TOKEN_FACTORY_BASE_URL").rstrip("/") + "/chat/completions"
        timeout_s = float(os.environ.get("NEBIUS_CRITIC_TIMEOUT_S", "20.0"))

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

        message = parsed.get("choices", [{}])[0].get("message", {})
        if not isinstance(message, dict):
            raise ValueError("invalid critic response message format")
        if "content" not in message and "reasoning" not in message:
            raise ValueError("invalid critic response message format")

        self._debug("=== Nebius API raw message ===")
        self._debug(json.dumps(message, indent=2))

        content = message.get("content", "")
        if isinstance(content, str) and content.strip():
            return self._parse_content_as_json(content)

        if isinstance(message.get("reasoning"), str):
            return self._parse_content_as_json(message["reasoning"])

        raise ValueError("invalid critic response content")

    @staticmethod
    def _parse_content_as_json(raw_content: Any) -> dict[str, Any]:
        if isinstance(raw_content, dict):
            return raw_content
        if not isinstance(raw_content, str):
            raise ValueError("invalid critic response content type")

        text = raw_content.strip()
        if not text:
            raise ValueError("empty critic content")

        candidates: list[str] = [text]
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        candidates.extend(fenced)

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidates.append(text[start : end + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        raise ValueError("unable to parse critic content as JSON")

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

    def _debug(self, message: str) -> None:
        if not self.debug:
            return
        print(message, file=sys.stderr)
