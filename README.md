# rOCDbot Hackathon Demo

One-liner: We use OCD-informed LLM reasoning to drive high-precision robotic correction of out-of-place objects.

Long description: rOCDbot combines a language model that understands OCD-style ordering preferences with a closed-loop robot correction pipeline. The system first identifies disordered objects in a tabletop scene, then executes an iterative action sequence to reposition them into a target-aligned state. We persist the full trace of initial state, decisions, and actions; these logs are used as structured feedback for later reinforcement-learning improvement and policy refinement.

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

This creates a release bundle in `artifacts/release/` and updates root `demo_presentation.md`.

Recommended judge files to show:
- `artifacts/release/judge_story.gif`
- `artifacts/release/judge_conversation.json`
- `artifacts/release/judge_script.md`
- `artifacts/release/judge_agent_log.jsonl`
- `artifacts/release/canonical_before.png`
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

`demo_presentation.md` is the default judge deck. Keep secrets out of source control and never commit real API keys.
