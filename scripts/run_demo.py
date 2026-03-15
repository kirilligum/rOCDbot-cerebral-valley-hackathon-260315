#!/usr/bin/env python3
"""CLI wrapper for the rOCDbot demo runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.demo.run_live import run_demo


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["dry-run", "mocked-nebius", "live-nebius", "live-or-cache", "release", "cache-only"],
        default="dry-run",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--artifact-root", default=str(ROOT / "artifacts"))
    args = parser.parse_args()

    result = run_demo(mode=args.mode, seed=args.seed, artifact_root=args.artifact_root)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
