"""Shared workspace harnesses for eval evidence tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory


def with_temp_workspace(assertion: Callable[[Path], None]) -> Callable[[], None]:
    """Run a no-argument assertion inside a temporary workspace."""

    def run_assertion() -> None:
        with TemporaryDirectory() as temp_dir:
            assertion(Path(temp_dir))

    return run_assertion
