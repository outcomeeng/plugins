"""Marketplace-wide pytest configuration.

Reads spx/EXCLUDE and tells pytest to skip collection of the listed nodes'
tests/ directories. Without this, raw pytest collects tests for specified
nodes whose implementation is a stub, causing per-test fixture failures
that break the quality gate even when EXCLUDE correctly marks the nodes
as not-yet-implemented.

The spx CLI's `spx test passing` command consumes the same EXCLUDE file at
invocation time. This conftest mirrors that filtering for raw pytest so
`just check` and similar entry points see the same scope.
"""

from __future__ import annotations

import pathlib
from typing import Final

import pytest

_REPO_ROOT: Final = pathlib.Path(__file__).resolve().parent
_EXCLUDE_FILE: Final = _REPO_ROOT / "spx" / "EXCLUDE"
_SPX_ROOT: Final = _REPO_ROOT / "spx"


def _excluded_test_dirs() -> frozenset[pathlib.Path]:
    if not _EXCLUDE_FILE.is_file():
        return frozenset()
    paths: list[pathlib.Path] = []
    for raw_line in _EXCLUDE_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        node_path = _SPX_ROOT / line
        tests_dir = node_path / "tests"
        if tests_dir.is_dir():
            paths.append(tests_dir.resolve())
    return frozenset(paths)


_EXCLUDED_TEST_DIRS: Final = _excluded_test_dirs()


def pytest_ignore_collect(
    collection_path: pathlib.Path,
    config: pytest.Config,
) -> bool | None:
    """Skip collection of test paths under nodes listed in spx/EXCLUDE."""
    resolved = collection_path.resolve()
    return (
        any(resolved.is_relative_to(excluded) for excluded in _EXCLUDED_TEST_DIRS)
        or None
    )
