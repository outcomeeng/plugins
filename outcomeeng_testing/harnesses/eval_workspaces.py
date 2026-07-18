"""Shared workspace harnesses for eval evidence tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


@contextmanager
def temporary_workspace(parent: Path | None = None) -> Iterator[Path]:
    """Yield a temporary workspace and remove it after the assertion completes."""
    with TemporaryDirectory(dir=parent) as temp_dir:
        yield Path(temp_dir)


def with_temp_workspace(assertion: Callable[[Path], None]) -> Callable[[], None]:
    """Run a no-argument assertion inside a temporary workspace."""

    return with_temp_workspace_under(None)(assertion)


def with_temp_workspace_under(
    parent: Path | None,
) -> Callable[[Callable[[Path], None]], Callable[[], None]]:
    """Run an assertion in a temporary workspace beneath ``parent``."""

    def decorate(assertion: Callable[[Path], None]) -> Callable[[], None]:
        def run_assertion() -> None:
            with temporary_workspace(parent) as temp_path:
                assertion(temp_path)

        return run_assertion

    return decorate
