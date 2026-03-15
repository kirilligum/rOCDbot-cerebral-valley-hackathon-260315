"""Release presentation markdown generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_demo_presentation(
    root: str | Path,
    *,
    manifest: dict[str, Any],
    demo_run: dict[str, Any],
    conversation: list[dict[str, Any]],
    judge_log_path: str | Path,
) -> str:
    root_path = Path(root)
    output_path = root_path / "demo_presentation.md"
    judge_log_text = Path(judge_log_path).read_text(encoding="utf-8").strip()

    metrics = demo_run["metrics"]
    critic = demo_run["critic"]
    scene = demo_run["scene_state"]

    content = f"""# rOCDbot Judge Demo Presentation

Robots can restore visual order, not just execute motions.

rOCDbot is a simulation-first robotics demo for a one-minute judge interaction: we show a tabletop scene with one clearly misaligned object, ask an OCD-style question about what looks wrong, convert that judgment into robot instructions, execute a constrained correction plan, and then evaluate whether the result would satisfy a person who wants the environment to feel ordered. The packaged bundle below includes the actual images, the prompt-response sequence, the agent log, the release storyboard GIF, and the run metadata used to explain the system in a live demo.

## Demo Summary

- Run ID: `{demo_run['run_id']}`
- Seed: `{demo_run['seed']}`
- Decision source: `{critic['source']}`
- Fallback used: `{demo_run['fallback_used']}`
- Yaw error: `{metrics['yaw_before_deg']:.1f} deg -> {metrics['yaw_after_deg']:.1f} deg`
- Position error after action: `{metrics['position_error_after_cm']:.1f} cm`
- Robot plan: `{" -> ".join(critic['plan'])}`

## Visual Storyboard

![Judge Story GIF](judge_story.gif)

### Before

![Before Scene](canonical_before.png)

### After

![After Scene](canonical_after.png)

## Judge-Facing Prompt and Response Flow

### 1. What looks out of place?

Prompt:
> {conversation[0]["user_prompt"]}

Response:
> {conversation[0]["assistant_response"]}

### 2. What should the robot do?

Prompt:
> {conversation[1]["user_prompt"]}

Response:
> {conversation[1]["assistant_response"]}

### 3. Was the action successful?

Prompt:
> {conversation[2]["user_prompt"]}

Response:
> {conversation[2]["assistant_response"]}

## Agent Logs

```json
{judge_log_text}
```

## Metrics to Say Out Loud

- The object `{scene['object_id']}` starts visibly misaligned at `{metrics['yaw_before_deg']:.1f} deg`.
- The robot reorients it to `{metrics['yaw_after_deg']:.1f} deg`, which is inside the demo success threshold.
- Final position error is `{metrics['position_error_after_cm']:.1f} cm`.
- The run used the `{critic['source']}` critic path with `fallback_used={demo_run['fallback_used']}`.

## System Architecture

```mermaid
flowchart LR
    A[Scene Image + Structured State] --> B[Prompt 1: OCD-style scene critique]
    B --> C[NebiusCritic.evaluate]
    C --> D[map_decision_to_plan]
    D --> E[run_scripted_correction]
    E --> F[Post-action image]
    F --> G[Prompt 3: success evaluation]
    C --> H[Artifacts and Logs]
    E --> H
    H --> I[Judge Story GIF + Presentation Markdown]
```

## Files to Show During the Demo

- Storyboard GIF: [judge_story.gif](judge_story.gif)
- Prompt/response JSON: [judge_conversation.json](judge_conversation.json)
- Judge script: [judge_script.md](judge_script.md)
- Agent logs: [judge_agent_log.jsonl](judge_agent_log.jsonl)
- Manifest: [demo_manifest.json](demo_manifest.json)

## Sponsor and Framework Usage Details

- Nebius Token Factory:
  - The sponsor-facing reasoning integration is implemented in `src/demo/critic.py`.
  - `NebiusCritic._live_transport()` builds the request with `NEBIUS_TOKEN_FACTORY_API_KEY`, `NEBIUS_TOKEN_FACTORY_BASE_URL`, and `NEBIUS_TOKEN_FACTORY_TEXT_MODEL`.
  - The API call uses `urllib.request.Request(...)` and `urllib.request.urlopen(...)` against the OpenAI-compatible `/chat/completions` endpoint.
  - `NebiusCritic.evaluate()` enforces schema validation and falls back to `cache/critic_response.json` with `ERR_NEBIUS_TIMEOUT` or `ERR_NEBIUS_SCHEMA`.
- Robotics runtime abstraction:
  - `PreparedSceneAdapter.reset_scene()`, `PreparedSceneAdapter.read_scene_state()`, `PreparedSceneAdapter.execute_plan()`, and `PreparedSceneAdapter.capture_frame()` define the simulator contract in `src/demo/isaac_adapter.py`.
  - `run_scripted_correction()` in `src/demo/executor.py` executes the primitive plan `["approach", "grasp", "lift", "rotate_to_target", "place", "settle"]`.
- Agent loop and orchestration:
  - `run_demo()` in `src/demo/run_live.py` orchestrates reset, reasoning, planning, execution, metrics, and artifact writing.
  - `map_decision_to_plan()` in `src/demo/planner.py` constrains language-model output to allowed robot primitives from `ALLOWED_PLAN`.
  - `compute_metrics()` in `src/demo/metrics.py` computes `yaw_before_deg`, `yaw_after_deg`, `position_error_after_cm`, `order_score_before`, and `order_score_after`.
- Packaging and presentation:
  - `package_release()` in `src/demo/release.py` generates the canonical run, cache-only backup run, operator notes, and release manifest.
  - `build_judge_conversation()` and `write_judge_story_package()` in `src/demo/judge_story.py` generate the prompts, responses, logs, and `judge_story.gif`.
  - `write_demo_presentation()` in `src/demo/presentation.py` creates this markdown presentation from the packaged artifacts.
- Python frameworks and libraries:
  - `pydantic.BaseModel` is used in `SceneState`, `CriticDecision`, and scene asset models for contract enforcement.
  - `Pillow` (`PIL.Image`, `PIL.ImageDraw`, `PIL.ImageOps`) is used for image rendering and GIF generation.
  - `pytest` drives the contract, integration, and performance checks through the `TEST-000` to `TEST-012` suite.
"""
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)
