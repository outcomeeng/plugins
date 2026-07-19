"""Shared workspace harnesses for eval evidence tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory


def with_temp_workspace(test_body: Callable[[Path], None]) -> Callable[[], None]:
    """Run a no-argument test callback inside a temporary workspace."""

    def run_test() -> None:
        with TemporaryDirectory() as temp_dir:
            test_body(Path(temp_dir))

    return run_test
