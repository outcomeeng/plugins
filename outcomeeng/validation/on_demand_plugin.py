"""Pytest plugin that keeps the on-demand suite out of directory collection.

The plugin excludes a collected file exactly when `is_on_demand_test` classifies
its file name at the on-demand level, so the exclusion and the classifier read
one definition of the level segment. pytest consults the hook for files it
discovers while walking a directory and never for a file the command line names,
so a direct target that names an on-demand file still runs it.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation._steps import is_on_demand_test


def pytest_ignore_collect(collection_path: Path) -> bool | None:
    """Ignore a discovered file whose name carries the on-demand level."""

    return True if is_on_demand_test(collection_path.name) else None
