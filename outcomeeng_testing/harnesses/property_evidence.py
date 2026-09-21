"""Shared failure diagnostics for harness-owned Hypothesis properties."""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

SEED_NOTE_FORM: Final = "Hypothesis seed: {seed}"
"""The note a failing property run carries for its seed."""
REPLAY_NOTE_FORM: Final = "Replay path: {path}"
"""The note a failing property run carries for its replay command."""


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
        error.add_note(SEED_NOTE_FORM.format(seed=seed_value))
        error.add_note(REPLAY_NOTE_FORM.format(path=replay_path))
        raise
