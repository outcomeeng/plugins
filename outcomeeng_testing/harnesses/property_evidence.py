"""Shared failure diagnostics for harness-owned Hypothesis properties."""

from __future__ import annotations

from collections.abc import Callable


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
        error.add_note(f"Hypothesis seed: {seed_value}")
        error.add_note(f"Replay path: {replay_path}")
        raise
