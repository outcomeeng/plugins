"""Real subprocess evidence for native profile timeout cleanup."""

import os
import subprocess

from outcomeeng_testing.harnesses.capturing_runner import (
    PROMPT_RETURN_CEILING_SECONDS,
)
from outcomeeng_testing.harnesses.native_profile_process import (
    lingering_native_profile_process,
    waiting_native_profile_process,
)


def test_parent_exit_decodes_output_and_terminates_descendant() -> None:
    with lingering_native_profile_process() as observation:
        assert isinstance(observation.result, subprocess.CompletedProcess)
        assert observation.result.returncode == os.EX_OK
        assert observation.output is not None
        assert observation.result.stdout == observation.output.decode(
            "utf-8", errors="replace"
        )
        assert observation.child.pid_path.is_file()
        assert observation.elapsed_seconds < PROMPT_RETURN_CEILING_SECONDS
        assert not observation.child.descendant_alive()


def test_timeout_terminates_descendant_before_returning() -> None:
    with waiting_native_profile_process() as observation:
        assert isinstance(observation.result, subprocess.TimeoutExpired)
        assert observation.child.pid_path.is_file()
        assert observation.elapsed_seconds < PROMPT_RETURN_CEILING_SECONDS
        assert not observation.child.descendant_alive()
