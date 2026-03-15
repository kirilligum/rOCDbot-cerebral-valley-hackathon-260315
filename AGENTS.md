# Repository Guidelines

## Project Structure & Module Organization
This repository is currently a planning and bootstrap workspace for the `rOCDbot` hackathon demo.

- [`prd.md`](/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/prd.md): current product requirements and demo scope.
- [`prd-old.md`](/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/prd-old.md): prior draft kept for reference.
- [`scripts/test_nebius_access.py`](/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/scripts/test_nebius_access.py): local Nebius inference and cloud smoke test.
- [`.env.example`](/home/kirill/hachathons/rOCDbot-cerebral-valley-hackathon-260315/.env.example): required environment variable template.

If runtime code is added, keep Python modules under `src/` and tests under `tests/`. Avoid placing executable logic in the repo root.

## Build, Test, and Development Commands
There is no full build pipeline yet. Use the current validation commands:

- `python3 scripts/test_nebius_access.py`: checks Token Factory model access and Nebius Cloud CLI access.
- `python3 scripts/test_nebius_access.py --skip-vision`: skips the current Kimi vision probe if you only need text and cloud checks.
- `~/.nebius/bin/nebius -p rocdbot iam whoami`: verifies the local Nebius CLI profile.

Add new project commands to this file when training, simulation, or demo entrypoints are introduced.

## Coding Style & Naming Conventions
Use Python 3 with 4-space indentation and `snake_case` for files, functions, and variables. Keep modules small and task-focused. Prefer structured JSON-like data over free-form strings for scene and planning state.

Name scripts with action-oriented verbs, for example `generate_dataset.py` or `run_demo.py`. Keep configuration in `.env` and document new keys in `.env.example`.

## Testing Guidelines
No formal test suite is configured yet. For now:

- keep smoke tests in `scripts/` for infrastructure checks;
- add unit tests under `tests/` when reusable Python modules are introduced;
- name tests `test_<feature>.py`.

Any new inference, planning, or simulation code should include at least one reproducible local check.

## Commit & Pull Request Guidelines
Git history currently contains only `Initial commit`, so keep commit messages short, imperative, and specific, for example `Add Nebius smoke test` or `Refine PRD success metrics`.

Pull requests should include:

- a concise summary of the change;
- links to relevant issues or PRD sections;
- validation steps run locally;
- screenshots or video only for UI or simulation-visible changes.

## Security & Configuration Tips
Do not commit secrets. Keep real credentials only in `.env`; `.env.example` must stay sanitized. Treat Nebius API keys, service-account data, and local CLI profiles as sensitive.
