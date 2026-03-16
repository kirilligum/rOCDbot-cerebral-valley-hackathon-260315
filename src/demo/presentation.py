"""Release presentation markdown generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_demo_presentation(
    output_path: str | Path,
    *,
    demo_run: dict[str, Any],
    conversation: list[dict[str, Any]],
    judge_log_path: str | Path,
    asset_prefix: str = "",
) -> str:
    target_path = Path(output_path)
    judge_log_text = Path(judge_log_path).read_text(encoding="utf-8").strip()

    metrics = demo_run["metrics"]
    critic = demo_run["critic"]
    scene = demo_run["scene_state"]
    prefix = asset_prefix.strip("/")

    def asset_path(name: str) -> str:
        if not prefix:
            return name
        return f"{prefix}/{name}"

    prompt_flow = _build_prompt_flow(conversation)

    content = f"""# rOCDbot Judge Demo Presentation

One-liner: We use OCD-informed LLM reasoning to drive high-precision robotic correction of out-of-place objects.

Long description: rOCDbot combines a language model that understands OCD-style ordering preferences with a closed-loop robotics pipeline. The system identifies a scene disorder, executes iterative actions to move the object to a precise target state, and evaluates completion quality. We preserve the full trace of initial observations, decisions, and actions as structured data used to improve future behavior through reinforcement-learning feedback.

---

## Demo Summary

- Run ID: `{demo_run['run_id']}`
- Seed: `{demo_run['seed']}`
- Decision source: `{critic['source']}`
- Fallback used: `{demo_run['fallback_used']}`
- Yaw error: `{metrics['yaw_before_deg']:.1f} deg -> {metrics['yaw_after_deg']:.1f} deg`
- Position error after action: `{metrics['position_error_after_cm']:.1f} cm`
- Robot plan: `{" -> ".join(critic['plan'])}`

## Multi-Step Trace

### Step 0: Initial scene (before)

![Before Scene]({asset_path("canonical_before.png")})

### Step 1: Rotated object, position off (intermediate)

![Step 1 Scene]({asset_path("canonical_intermediate.png")})

### Step 2: Top and right edges partly aligned

![Step 2 Scene]({asset_path("canonical_aligned.png")})

### Step 3: Perfect corner alignment

![Step 3 Scene]({asset_path("canonical_after.png")})

### Trace Cards

![Judge Story GIF]({asset_path("judge_story.gif")})

## Judge-Facing Prompt and Response Flow

{prompt_flow}

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
    E --> F[Step 1 rotated/off image]
    F --> G[Step 1 instruction + eval]
    G --> H[Step 2 aligned image]
    H --> I[Step 2 instruction + eval]
    I --> J[Step 3 final image]
    J --> K[Step 3 instruction + eval]
    C --> M[Artifacts and Logs]
    E --> L[Judge Story GIF + Presentation Markdown]
```

## Files to Show During the Demo

- Trace GIF: [judge_story.gif]({asset_path("judge_story.gif")})
- Prompt/response JSON: [judge_conversation.json]({asset_path("judge_conversation.json")})
- Judge script: [judge_script.md]({asset_path("judge_script.md")})
- Agent logs: [judge_agent_log.jsonl]({asset_path("judge_agent_log.jsonl")})
- Manifest: [demo_manifest.json]({asset_path("demo_manifest.json")})

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
    
## Quick setup

1. Clone and enter this repository.
2. Create/activate a Python environment.
3. Install dependencies:
   - `python3 -m pip install -r requirements-dev.txt`
   - `python3 -m pip install pydantic pillow`
4. Copy `.env.example` to `.env` and fill Nebius credentials.

## Core run modes

- `python3 scripts/run_demo.py --mode dry-run --seed {demo_run['seed']}`
- `python3 scripts/run_demo.py --mode mocked-nebius --seed {demo_run['seed']}`
- `python3 scripts/run_demo.py --mode live-or-cache --seed {demo_run['seed']}`
- `python3 scripts/run_demo.py --mode live-nebius --seed {demo_run['seed']}` (requires live key/access)
- `python3 scripts/run_demo.py --mode cache-only --seed {demo_run['seed']}`
- `python3 scripts/run_demo.py --mode release --seed {demo_run['seed']}`

All runs write artifacts under `artifacts/<run-id>/` and print `run_id` + artifact path.

## Judge-ready packaging

```bash
python3 scripts/package_demo.py --seed {demo_run['seed']}
```

This creates a release bundle in `artifacts/release/` and updates this README.

Recommended judge files to show:
- `artifacts/release/judge_story.gif`
- `artifacts/release/judge_conversation.json`
- `artifacts/release/judge_script.md`
- `artifacts/release/judge_agent_log.jsonl`
- `artifacts/release/canonical_before.png`
- `artifacts/release/canonical_intermediate.png`
   - `artifacts/release/canonical_intermediate.png`
   - `artifacts/release/canonical_aligned.png`
   - `artifacts/release/canonical_after.png`
- `artifacts/release/demo_manifest.json`

## Validation checks

- `python3 scripts/test_nebius_access.py` validates Token Factory and Nebius CLI access.
- `pytest` runs all test suites.
- Add focused runs with paths, e.g. `pytest tests/unit`.

## Project structure

`src/demo/` contains the orchestration, critic, planner, executor, scene simulation adapter, metric logic, judge-script generation, and release packaging.  
`tests/` contains unit/integration/perf coverage tied to demo contracts.  
`assets/` contains prepared scene scene JSON used by the local adapter.  
`scripts/` contains CLI entrypoints for running and packaging demos.

## Notes

Keep secrets out of source control and never commit real API keys.
"""
    target_path.write_text(content, encoding="utf-8")
    return str(target_path)


def _build_prompt_flow(conversation: list[dict[str, Any]]) -> str:
    lines = []
    for index, turn in enumerate(conversation, start=1):
        lines.extend(
            [
                f"### {index}. {turn['stage'].replace('_', ' ').title()}",
                "",
                "Prompt:",
                f"> {turn['user_prompt']}",
                "",
                "Response:",
                f"> {turn['assistant_response']}",
                "",
            ]
        )
    return "\n".join(lines)
