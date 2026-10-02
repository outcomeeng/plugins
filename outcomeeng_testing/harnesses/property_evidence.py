"""Shared failure diagnostics for harness-owned Hypothesis properties."""

from __future__ import annotations

from collections.abc import Callable

SEED_NOTE_PREFIX = "Hypothesis seed: "
REPLAY_NOTE_PREFIX = "Replay path: "


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
