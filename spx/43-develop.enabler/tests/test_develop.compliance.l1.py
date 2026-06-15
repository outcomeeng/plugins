"""Compliance evidence: develop source carries no raw runtime-divergent token."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.build import (
    TEXT_FILE_SUFFIXES,
    IMPLEMENTED,
    guard_plugin_runtime_tokens,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEVELOP_SOURCE = REPO_ROOT / "src" / "plugins" / "develop"
SHARED_ROOT = REPO_ROOT / "src" / "_shared"


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

    # guard_plugin_runtime_tokens guards each file over its include-expanded text —
    # the same public entry point build() uses — so a raw token hiding in an
    # included shared fragment is caught, not only literals in a file's own body.
    # It raises RuntimeTokenError on any raw registry name; a clean develop tree
    # passes for every file.
    for path in rendered_files:
        guard_plugin_runtime_tokens(path, shared_root=SHARED_ROOT)
