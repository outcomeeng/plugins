"""Find test-infrastructure package files placed where only test evidence lives.

Harnesses, generators, and fixtures live in the ``<package>_testing/`` package at
the repository root.  A file inside a ``*_testing`` package is misplaced when it
sits under ``spx/`` or inside any ``tests/`` directory, because those locations
hold specs and typed assertion evidence only.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Final

TEST_INFRASTRUCTURE_PACKAGE_SUFFIX: Final = "_testing"
PRODUCT_TREE_DIRECTORY: Final = "spx"
TESTS_DIRECTORY: Final = "tests"


def misplaced_test_infrastructure(paths: Iterable[str]) -> tuple[str, ...]:
    """Return every ``*_testing`` package file under ``spx/`` or a ``tests/`` directory."""
    return tuple(path for path in paths if _is_misplaced(PurePosixPath(path)))


def _is_misplaced(path: PurePosixPath) -> bool:
    directories = path.parts[:-1]
    in_package = any(
        part.endswith(TEST_INFRASTRUCTURE_PACKAGE_SUFFIX) for part in directories
    )
    return in_package and (
        directories[:1] == (PRODUCT_TREE_DIRECTORY,) or TESTS_DIRECTORY in directories
    )


__all__ = [
    "PRODUCT_TREE_DIRECTORY",
    "TESTS_DIRECTORY",
    "TEST_INFRASTRUCTURE_PACKAGE_SUFFIX",
    "misplaced_test_infrastructure",
]
