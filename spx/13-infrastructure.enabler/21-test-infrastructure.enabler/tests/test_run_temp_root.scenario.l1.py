"""Scenario: a pytest run leaves the user temp folder as it found it.

The scratch run holds a passing and a failing test; each creates temp files
through ``tempfile``, through ``tmp_path``, and through a child process. The
user temp folder is a sandbox the harness hands the run as ``TMPDIR``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.run_temp_root_observation import (
    CHANNELS,
    observe_pytest_run,
)


def test_user_temp_folder_entries_equal_entries_before_the_run(tmp_path: Path) -> None:
    observation = observe_pytest_run(tmp_path)

    assert observation.returncode == pytest.ExitCode.TESTS_FAILED, observation.output
    assert set(observation.created) == set(CHANNELS)
    assert observation.user_temp_entries_after == observation.user_temp_entries_before
