#!/usr/bin/env python3
"""Smoke-test Nebius Token Factory and Nebius Cloud access."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")


def load_dotenv(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key, value)


def require_env(*names: str) -> None:
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


def http_json(url: str, method: str = "GET", headers: dict[str, str] | None = None, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, method=method, headers=headers or {}, data=body)
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc


def tf_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['NEBIUS_TOKEN_FACTORY_API_KEY']}",
        "Content-Type": "application/json",
    }


def tf_url(path: str) -> str:
    return os.environ["NEBIUS_TOKEN_FACTORY_BASE_URL"].rstrip("/") + "/" + path.lstrip("/")


def summarize_message(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(text.strip())
        if parts:
            return " ".join(parts)
    reasoning = message.get("reasoning")
    if isinstance(reasoning, str) and reasoning.strip():
        first_line = reasoning.strip().splitlines()[0]
        return f"[reasoning-only] {first_line}"
    return "[empty assistant message]"


def check_token_factory_models() -> None:
    data = http_json(tf_url("models"), headers=tf_headers())
    model_ids = {item["id"] for item in data.get("data", [])}
    expected = {
        os.environ.get("NEBIUS_TOKEN_FACTORY_TEXT_MODEL", ""),
        os.environ["NEBIUS_TOKEN_FACTORY_MODEL"],
        os.environ.get("NEBIUS_TOKEN_FACTORY_MODEL_FAST", ""),
    }
    missing = sorted(model for model in expected if model and model not in model_ids)
    if missing:
        raise RuntimeError(f"Expected Nebius models not found: {', '.join(missing)}")
    print(f"[ok] Token Factory models reachable; found {os.environ['NEBIUS_TOKEN_FACTORY_MODEL']}")


def check_token_factory_text() -> None:
    model = os.environ.get("NEBIUS_TOKEN_FACTORY_TEXT_MODEL") or os.environ.get("NEBIUS_TOKEN_FACTORY_MODEL_FAST") or os.environ["NEBIUS_TOKEN_FACTORY_MODEL"]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with exactly CONNECTED."},
            {"role": "user", "content": "Reply now."},
        ],
        "max_tokens": 80,
        "temperature": 0,
    }
    data = http_json(tf_url("chat/completions"), method="POST", headers=tf_headers(), payload=payload)
    message = data["choices"][0]["message"]
    print(f"[ok] Token Factory text completion via {model}: {summarize_message(message)}")


def check_token_factory_vision(require_vision: bool) -> None:
    payload = {
        "model": os.environ["NEBIUS_TOKEN_FACTORY_MODEL"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What is in this image? Answer in one short sentence."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
                        },
                    },
                ],
            }
        ],
        "max_tokens": 80,
        "temperature": 0,
    }
    try:
        data = http_json(tf_url("chat/completions"), method="POST", headers=tf_headers(), payload=payload)
        message = data["choices"][0]["message"]
        print(f"[ok] Token Factory vision completion via {os.environ['NEBIUS_TOKEN_FACTORY_MODEL']}: {summarize_message(message)}")
    except RuntimeError as exc:
        if require_vision:
            raise
        print(f"[warn] Token Factory vision attempt via {os.environ['NEBIUS_TOKEN_FACTORY_MODEL']} did not complete: {exc}")


def nebius_cli() -> str:
    explicit = os.environ.get("NEBIUS_CLOUD_CLI")
    if explicit:
        return explicit
    for candidate in ("nebius", os.path.expanduser("~/.nebius/bin/nebius")):
        resolved = shutil.which(candidate) if candidate == "nebius" else candidate
        if resolved and os.path.exists(resolved):
            return resolved
    raise RuntimeError("Nebius CLI not found. Install it or set NEBIUS_CLOUD_CLI.")


def run_cli(*args: str) -> dict:
    cmd = [nebius_cli()]
    profile = os.environ.get("NEBIUS_CLOUD_PROFILE")
    if profile:
        cmd.extend(["-p", profile])
    cmd.extend(args)
    if "--format" not in args:
        cmd.extend(["--format", "json"])
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {completed.stderr.strip() or completed.stdout.strip()}")
    stdout = completed.stdout.strip()
    return {} if not stdout else json.loads(stdout)


def check_cloud_cli() -> None:
    whoami = run_cli("iam", "whoami")
    project = run_cli("iam", "project", "get", os.environ["NEBIUS_CLOUD_PROJECT_ID"])
    instances = run_cli("compute", "instance", "list")
    email = whoami["user_profile"]["attributes"]["email"]
    name = project["metadata"]["name"]
    region = project["status"]["region"]
    instance_count = len(instances.get("items", []))
    print(f"[ok] Nebius Cloud CLI auth works for {email}")
    print(f"[ok] Project {name} ({os.environ['NEBIUS_CLOUD_PROJECT_ID']}) is reachable in {region}")
    print(f"[ok] Compute instance list succeeded; current instances: {instance_count}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-vision", action="store_true", help="Skip the Token Factory vision request.")
    parser.add_argument("--require-vision", action="store_true", help="Fail if the Token Factory vision request fails.")
    args = parser.parse_args()

    load_dotenv(ENV_PATH)
    require_env(
        "NEBIUS_TOKEN_FACTORY_API_KEY",
        "NEBIUS_TOKEN_FACTORY_BASE_URL",
        "NEBIUS_TOKEN_FACTORY_MODEL",
        "NEBIUS_CLOUD_PROJECT_ID",
    )

    check_token_factory_models()
    check_token_factory_text()
    if not args.skip_vision:
        check_token_factory_vision(require_vision=args.require_vision)
    check_cloud_cli()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"[error] {exc}", file=sys.stderr)
        raise SystemExit(1)
