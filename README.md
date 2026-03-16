# rOCDbot Judge Demo Presentation

## One-liner
Knowledge of OCD helps make robots more precise through image-text models and RL.

rOCDbot combines a language model that understands OCD-style ordering preferences with a closed-loop robotics pipeline. The system identifies a scene disorder, executes iterative actions to move the object to a precise target state, and evaluates completion quality. We preserve the full trace of initial observations, decisions, and actions as structured data used to improve future behavior through reinforcement-learning feedback.

---

## Demo Summary

- Run ID: `20260316T005925408041Z-release-seed7`
- Seed: `7`
- Decision source: `cache`
- Fallback used: `True`
- Yaw error: `28.0 deg -> 0.0 deg`
- Position error after action: `0.3 cm`
- Robot plan: `approach -> grasp -> lift -> rotate_to_target -> place -> settle`

## Multi-Step Trace

### Step 0: Initial scene (before)

![Before Scene](artifacts/release/canonical_before.png)

### Step 1: Rotated object, position off (intermediate)

![Step 1 Scene](artifacts/release/canonical_intermediate.png)

### Step 2: Top and right edges partly aligned

![Step 2 Scene](artifacts/release/canonical_aligned.png)

### Step 3: Perfect corner alignment

![Step 3 Scene](artifacts/release/canonical_after.png)

### Trace Cards

![Judge Story GIF](artifacts/release/judge_story.gif)

## Judge-Facing Prompt and Response Flow

### 1. Scene Critique

Prompt:
> I am a person with OCD. What looks out of place in this scene? Use the image and the structured scene summary. Focus on what would look visually wrong to someone who wants the table to feel ordered.

Response:
> The object `book_1` is the main disorder. It is rotated 28.0 deg from the table axis and shifted from the aligned corner.

### 2. Robot Instruction Step 1

Prompt:
> Step 1: What are the robot instructions to improve OCD-style order for this scene? Return short concrete actions.

Response:
> Step 1 action set: approach -> grasp -> lift -> rotate_to_target -> place -> settle. Goal: rotate `book_1` back to 0.0 deg and place it at the target corner.

### 3. Post Action Evaluation Step 1

Prompt:
> Evaluate step 1. If incomplete, propose one follow-up correction action.

Response:
> Result: yaw is now 28.0 deg and position error is 0.7 cm. Task incomplete. Refine placement and settle again.

### 4. Robot Instruction Step 2

Prompt:
> Step 2: What are the robot instructions to improve OCD-style order for this scene? Return short concrete actions.

Response:
> Step 2 action set: approach -> grasp -> lift -> rotate_to_target -> place -> settle. Goal: rotate `book_1` back to 0.0 deg and place it at the target corner.

### 5. Post Action Evaluation Step 2

Prompt:
> Evaluate step 2. If incomplete, propose one follow-up correction action.

Response:
> Result: yaw is now 0.0 deg and position error is 0.3 cm. Task incomplete. Refine placement and settle again.

### 6. Robot Instruction Step 3

Prompt:
> Step 3: What are the robot instructions to improve OCD-style order for this scene? Return short concrete actions.

Response:
> Step 3 action set: approach -> grasp -> lift -> rotate_to_target -> place -> settle. Goal: rotate `book_1` back to 0.0 deg and place it at the target corner.

### 7. Post Action Evaluation Step 3

Prompt:
> Evaluate step 3. If incomplete, propose one follow-up correction action.

Response:
> Result: yaw is now 0.0 deg and position error is 0.3 cm. Task incomplete. Refine placement and settle again.


## Agent Logs

```json
{"step": 1, "event": "scene_captured", "image_path": "/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/artifacts/release/canonical_before.png", "scene_object": "book_1", "yaw_before_deg": 28.0}
{"step": 2, "event": "order_critique_generated", "decision_source": "cache", "fallback_used": true, "reason": "The object is rotated away from the table axis."}
{"step": 3, "event": "robot_plan_selected", "plan": ["approach", "grasp", "lift", "rotate_to_target", "place", "settle"], "execution_latency_ms": 51}
{"event": "robot_instruction_generated", "step": 4, "image_path": "/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/artifacts/release/canonical_before.png", "stage": "robot_instruction_step_1", "instructions": "Step 1 action set: approach -> grasp -> lift -> rotate_to_target -> place -> settle. Goal: rotate `book_1` back to 0.0 deg and place it at the target corner."}
{"event": "post_action_evaluated", "step": 4, "image_path": "/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/artifacts/release/runs/20260316T005925408041Z-release-seed7/step_01.png", "yaw_after_deg": 28.0, "position_error_after_cm": 0.7, "step_complete": false}
{"event": "robot_instruction_generated", "step": 5, "image_path": "/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/artifacts/release/runs/20260316T005925408041Z-release-seed7/step_01.png", "stage": "robot_instruction_step_2", "instructions": "Step 2 action set: approach -> grasp -> lift -> rotate_to_target -> place -> settle. Goal: rotate `book_1` back to 0.0 deg and place it at the target corner."}
{"event": "post_action_evaluated", "step": 5, "image_path": "/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/artifacts/release/runs/20260316T005925408041Z-release-seed7/step_02.png", "yaw_after_deg": 0.0, "position_error_after_cm": 0.3, "step_complete": false}
{"event": "robot_instruction_generated", "step": 6, "image_path": "/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/artifacts/release/runs/20260316T005925408041Z-release-seed7/step_02.png", "stage": "robot_instruction_step_3", "instructions": "Step 3 action set: approach -> grasp -> lift -> rotate_to_target -> place -> settle. Goal: rotate `book_1` back to 0.0 deg and place it at the target corner."}
{"event": "post_action_evaluated", "step": 6, "image_path": "/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/artifacts/release/canonical_after.png", "yaw_after_deg": 0.0, "position_error_after_cm": 0.3, "step_complete": false}
```

## Metrics to Say Out Loud

- The object `book_1` starts visibly misaligned at `28.0 deg`.
- The robot reorients it to `0.0 deg`, which is inside the demo success threshold.
- Final position error is `0.3 cm`.
- The run used the `cache` critic path with `fallback_used=True`.

## Demo Usage Flow

```mermaid
flowchart TD
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

## System Architecture

```mermaid
flowchart TD
    V[Robot Vision<br/>RGB + structured scene state] --> P[Perception & Scene Preprocess]
    P --> I[LLM-image Inference<br/>Nebius Token Factory]
    I --> D[Decision + plan extraction]
    D --> R[Robot Controller]
    R --> M[Motion Primitives<br/>approach / grasp / lift / rotate / place / settle]
    M --> C[Execution Feedback<br/>images, poses, rewards]
    C -->|observed scene update| V
    C --> A[RL Episode Builder]
    A --> S[Cloud Artifact Store<br/>episodes + trajectories + metadata]
    S --> T[Cloud RL Training<br/>fine-tuning / policy update]
    T --> U[Updated Policy & checkpoints]
    U --> R
    C --> L[Judge logs / traces / metrics]
    C --> J[Live telemetry + debug artifacts]
```

## Files to Show During the Demo

- Trace GIF: [judge_story.gif](artifacts/release/judge_story.gif)
- Prompt/response JSON: [judge_conversation.json](artifacts/release/judge_conversation.json)
- Judge script: [judge_script.md](artifacts/release/judge_script.md)
- Agent logs: [judge_agent_log.jsonl](artifacts/release/judge_agent_log.jsonl)
- RL traces: [rl_episodes.jsonl](artifacts/release/rl_episodes.jsonl) and [rl_trajectories.jsonl](artifacts/release/rl_trajectories.jsonl)
- Manifest: [demo_manifest.json](artifacts/release/demo_manifest.json)

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

- `python3 scripts/run_demo.py --mode dry-run --seed 7`
- `python3 scripts/run_demo.py --mode mocked-nebius --seed 7`
- `python3 scripts/run_demo.py --mode live-or-cache --seed 7`
- `python3 scripts/run_demo.py --mode live-nebius --seed 7` (requires live key/access)
- `python3 scripts/run_demo.py --mode cache-only --seed 7`
- `python3 scripts/run_demo.py --mode release --seed 7`

All runs write artifacts under `artifacts/<run-id>/` and print `run_id` + artifact path.

## Judge-ready packaging

```bash
python3 scripts/package_demo.py --seed 7
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
