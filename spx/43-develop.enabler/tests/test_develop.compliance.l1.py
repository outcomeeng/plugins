"""Compliance evidence: develop source carries no raw runtime-divergent token."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import (
    TEXT_FILE_SUFFIXES,
    IMPLEMENTED,
    guard_runtime_tokens,
)

DEVELOP_SOURCE = Path(__file__).resolve().parents[3] / "src" / "plugins" / "develop"


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


def test_develop_source_carries_no_raw_runtime_token() -> None:
    rendered_files = [
        path
        for path in DEVELOP_SOURCE.rglob("*")
        if path.is_file() and path.suffix in TEXT_FILE_SUFFIXES
    ]
    assert rendered_files, f"no rendered-text source under {DEVELOP_SOURCE}"

    # guard_runtime_tokens raises RuntimeTokenError on any raw registry name; a
    # clean develop tree passes for every file.
    for path in rendered_files:
        guard_runtime_tokens(path.read_text(encoding="utf-8"), source=path)
