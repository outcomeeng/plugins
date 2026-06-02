"""Real controlled children for ``l1`` tests of the bounded capturing subprocess runner.

Backs the scenario assertions in
``spx/15-validation.enabler/32-plugin-manifest.enabler/plugin-manifest.md`` and the rules in
``spx/15-validation.enabler/21-subprocess-execution.adr.md``. No test doubles: per the testing
methodology Stage 4 the real subprocess produces the behavior under test — a child that never
exits, and a child that exits while a descendant keeps the inherited output stream open —
reliably, safely, cheaply, and observably at ``l1``. This harness owns the bounded test
timeout, builds the controlled commands, and guarantees no descendant survives the test.

POSIX only: the controlled children rely on ``os.fork`` and process-group signalling.
"""

from __future__ import annotations

import os
import signal
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

# Bounded wait the timeout test injects in place of the production default.
TEST_TIMEOUT_SECONDS: Final = 1.0

# A descendant sleep that outlasts the injected timeout and the prompt-return ceiling, so an
# unbounded read would block on it and a regression would fail the test rather than pass fast.
DESCENDANT_SLEEP_SECONDS: Final = 30

# Ceiling for a prompt return: when the invoked process exits on its own, the runner must
# return far sooner than the descendant's sleep rather than blocking until the descendant ends.
PROMPT_RETURN_CEILING_SECONDS: Final = 5.0


@dataclass(frozen=True)
class ControlledChild:
    """A real command and a liveness probe for the descendant it spawns."""

    command: tuple[str, ...]
    pid_path: Path

    def descendant_alive(self) -> bool:
        try:
            pid = int(self.pid_path.read_text())
        except (FileNotFoundError, ValueError):
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True


def _fork_script(pid_path: Path, *, parent_exits: bool) -> str:
    parent_tail = (
        "    sys.stdout.write('done')\n    sys.stdout.flush()\n    os._exit(0)\n"
        if parent_exits
        else f"    time.sleep({DESCENDANT_SLEEP_SECONDS})\n"
    )
    return (
        "import os, sys, time\n"
        "descendant = os.fork()\n"
        "if descendant:\n"
        f"    with open({str(pid_path)!r}, 'w') as handle:\n"
        "        handle.write(str(descendant))\n"
        f"{parent_tail}"
        "else:\n"
        f"    time.sleep({DESCENDANT_SLEEP_SECONDS})\n"
    )


@contextmanager
def _controlled_child(*, parent_exits: bool) -> Iterator[ControlledChild]:
    with TemporaryDirectory() as tmp:
        pid_path = Path(tmp) / "descendant.pid"
        command = (
            sys.executable,
            "-c",
            _fork_script(pid_path, parent_exits=parent_exits),
        )
        try:
            yield ControlledChild(command=command, pid_path=pid_path)
        finally:
            _terminate(pid_path)


@contextmanager
def never_returning_child() -> Iterator[ControlledChild]:
    """Yield a child whose group stays alive until terminated, holding its output stream."""
    with _controlled_child(parent_exits=False) as child:
        yield child


@contextmanager
def child_exiting_with_lingering_descendant() -> Iterator[ControlledChild]:
    """Yield a child that exits immediately while a descendant keeps the output stream open."""
    with _controlled_child(parent_exits=True) as child:
        yield child


def _terminate(pid_path: Path) -> None:
    # Kill the descendant's whole process group, not just the recorded PID, so cleanup
    # reaps the spawned parent too — independent of whether run_validate group-killed it.
    try:
        pid = int(pid_path.read_text())
    except (FileNotFoundError, ValueError):
        return
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except ProcessLookupError:
        return


__all__ = [
    "DESCENDANT_SLEEP_SECONDS",
    "PROMPT_RETURN_CEILING_SECONDS",
    "TEST_TIMEOUT_SECONDS",
    "ControlledChild",
    "child_exiting_with_lingering_descendant",
    "never_returning_child",
]
