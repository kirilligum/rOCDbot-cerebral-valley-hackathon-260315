#!/usr/bin/env python3
"""Package the canonical release bundle for the rOCDbot demo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.demo.release import DEFAULT_RELEASE_ROOT, package_release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--release-root", default=str(DEFAULT_RELEASE_ROOT))
    args = parser.parse_args()

    manifest = package_release(seed=args.seed, release_root=args.release_root)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
