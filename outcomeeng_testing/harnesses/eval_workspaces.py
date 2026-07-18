"""Shared workspace harnesses for eval evidence tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory


def with_temp_workspace(assertion: Callable[[Path], None]) -> Callable[[], None]:
    """Run a no-argument assertion inside a temporary workspace."""

    return with_temp_workspace_under(None)(assertion)


def with_temp_workspace_under(
    parent: Path | None,
) -> Callable[[Callable[[Path], None]], Callable[[], None]]:
    """Run an assertion in a temporary workspace beneath ``parent``."""

    def decorate(assertion: Callable[[Path], None]) -> Callable[[], None]:
        def run_assertion() -> None:
            with TemporaryDirectory(dir=parent) as temp_dir:
                assertion(Path(temp_dir))

        return run_assertion

    return decorate
