"""Real subprocess evidence for native profile timeout cleanup."""

import subprocess

from outcomeeng_testing.harnesses.capturing_runner import (
    PROMPT_RETURN_CEILING_SECONDS,
)
from outcomeeng_testing.harnesses.native_profile_process import (
    lingering_native_profile_process,
)


def test_timeout_terminates_descendant_before_returning() -> None:
    with lingering_native_profile_process() as observation:
        assert isinstance(observation.result, subprocess.TimeoutExpired)
        assert observation.child.pid_path.is_file()
        assert observation.elapsed_seconds < PROMPT_RETURN_CEILING_SECONDS
        assert not observation.child.descendant_alive()
