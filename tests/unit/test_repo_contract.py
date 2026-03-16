# TEST-000
from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("case_name", [pytest.param("repo_contract", id="TEST-000")])
def test_repo_scaffold_and_secret_hygiene_test_000(case_name: str) -> None:
    assert case_name == "repo_contract"
    required_dirs = [
        ROOT / "src" / "demo",
        ROOT / "tests" / "integration",
        ROOT / "tests" / "fixtures",
        ROOT / "assets" / "scenes",
        ROOT / "cache",
        ROOT / "artifacts",
        ROOT / "plans" / "adrs",
    ]

    missing = [str(path.relative_to(ROOT)) for path in required_dirs if not path.exists()]
    assert not missing, f"missing required directories: {missing}"

    adrs = sorted((ROOT / "plans" / "adrs").glob("ADR-*.md"))
    assert adrs, "plans/adrs must contain at least one ADR markdown file"

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore
    assert "artifacts/" in gitignore
    assert "cache/" in gitignore

    test_root = ROOT / "tests"
    for category in ["unit", "integration", "perf"]:
        category_dir = test_root / category
        for path in sorted(category_dir.glob("test_*.py")):
            content = path.read_text(encoding="utf-8")
            assert re.search(r"^# TEST-\d{3}", content, re.M), f"missing TEST id tag: {path}"
