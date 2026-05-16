"""Level-1 scenario evidence for `spx/21-hygiene.enabler/21-clean.enabler/`.

Covers the two scenario assertions in `clean.md`: the recorded argv is
exactly the source-owned `CLEAN_ARGV`, and the runner's exit code is
propagated to the caller. Filesystem-level behavior (what `git clean
-fdX` removes or preserves) is owned by git and out of scope for this
module's L1 evidence.
"""

from __future__ import annotations

from outcomeeng.hygiene.clean import CLEAN_ARGV, clean
from outcomeeng_testing.harnesses.clean import RecordingRunner


def test_clean_invokes_recorded_argv_exactly_once() -> None:
    runner = RecordingRunner()

    exit_code = clean(runner=runner)

    assert exit_code == 0
    assert runner.calls == [CLEAN_ARGV]


def test_clean_propagates_runner_exit_code() -> None:
    runner = RecordingRunner(exit_code=3)

    exit_code = clean(runner=runner)

    assert exit_code == 3
