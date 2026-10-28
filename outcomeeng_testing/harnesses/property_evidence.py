"""Shared failure diagnostics for harness-owned Hypothesis properties."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Final

from hypothesis import given, seed, settings
from hypothesis.strategies import SearchStrategy

SEED_NOTE_PREFIX = "Hypothesis seed: "
REPLAY_NOTE_PREFIX = "Replay path: "
PROPERTY_REPLAY_COMMAND: Final = "just test"
REPO_ROOT: Final = Path(__file__).resolve().parents[2]


def run_replayable_property(
    property_run: Callable[[], None],
    *,
    seed_value: int,
    replay_path: str,
) -> None:
    """Run a configured property while preserving its native failure details."""
    try:
        property_run()
    except Exception as error:
        error.add_note(f"{SEED_NOTE_PREFIX}{seed_value}")
        error.add_note(f"{REPLAY_NOTE_PREFIX}{replay_path}")
        raise


def property_replay_path(test_func: Callable[..., None]) -> str:
    """The pytest command that replays the property run by `test_func`.

    A property named `_{name}` runs through the test entry point `test_{name}`
    beside it in the same file.
    """
    source = Path(inspect.getfile(test_func)).resolve()
    return (
        f"{PROPERTY_REPLAY_COMMAND} "
        f"{source.relative_to(REPO_ROOT).as_posix()}"
        f"::test{test_func.__name__}"
    )


def replayable_property(
    test_func: Callable[..., None],
    *,
    seed_value: int,
    max_examples: int,
    strategies: Mapping[str, SearchStrategy[Any]],
    replay_path: str | None = None,
) -> Callable[[], None]:
    """Configure a seeded property over `strategies` with replayable failures.

    The replay path defaults to the entry point beside `test_func`.
    """
    configured = seed(seed_value)(
        settings(max_examples=max_examples, deadline=None)(
            given(**strategies)(test_func)
        )
    )
    path = replay_path if replay_path is not None else property_replay_path(test_func)

    def wrapper() -> None:
        run_replayable_property(configured, seed_value=seed_value, replay_path=path)

    return wrapper
