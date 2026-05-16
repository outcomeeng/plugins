"""Recording doubles for the gate orchestrator.

These harnesses implement the `ProcessSpawner` and `ProcessHandle` Protocols
declared in `outcomeeng.validation`. They are spies (recording calls) and
stubs (returning scripted exit codes), used by `l1` tests to verify
orchestration behavior without launching real subprocesses.

Exception case: Stage 5, Interaction protocols — the orchestrator's
correctness depends on the sequence and shape of spawn/wait/signal calls.
Recording doubles let `l1` tests assert on those interactions.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from outcomeeng.validation import ProcessHandle, ProcessSpawner


@dataclass
class RecordingHandle:
    """A ProcessHandle that returns a scripted exit code on wait().

    poll() returns None until wait() has been called once, then returns the
    scripted exit code. send_signal_to_group records the signal but does not
    affect the next poll()/wait() — tests that need "child ignores SIGTERM"
    behavior can use this directly; tests that need "child exits on SIGTERM"
    should set `exit_on_signal=True`.
    """

    pid: int
    exit_code: int
    exit_on_signal: bool = False
    received_signals: list[int] = field(default_factory=list)
    _exited: bool = False

    def poll(self) -> int | None:
        if self._exited:
            return self.exit_code
        return None

    def wait(self) -> int:
        self._exited = True
        return self.exit_code

    def send_signal_to_group(self, sig: int) -> None:
        self.received_signals.append(sig)
        if self.exit_on_signal:
            self._exited = True


@dataclass
class RecordingSpawner:
    """A ProcessSpawner that returns scripted handles in order of spawn calls.

    The exit_codes sequence drives the i-th spawn() call's handle. spawn_calls
    records the argv tuples passed to spawn(), in order.
    """

    exit_codes: Sequence[int]
    spawn_calls: list[tuple[str, ...]] = field(default_factory=list)
    handles: list[RecordingHandle] = field(default_factory=list)
    _next_pid: int = 10_000

    def spawn(self, argv: Sequence[str]) -> ProcessHandle:
        index = len(self.spawn_calls)
        self.spawn_calls.append(tuple(argv))
        exit_code = self.exit_codes[index] if index < len(self.exit_codes) else 0
        handle = RecordingHandle(pid=self._next_pid + index, exit_code=exit_code)
        self.handles.append(handle)
        return handle


@dataclass
class HangingHandle:
    """A ProcessHandle that never exits on its own — for signal-handling tests.

    poll() always returns None. wait() blocks indefinitely (tests should not
    call wait directly on this; the signal handler escalates to SIGKILL after
    the grace period). send_signal_to_group records the signal; if
    `exit_on_kill=True`, a subsequent poll() returns 137 after SIGKILL (9)
    is received.
    """

    pid: int
    exit_on_kill: bool = True
    received_signals: list[int] = field(default_factory=list)
    _killed: bool = False

    def poll(self) -> int | None:
        if self._killed:
            return 137
        return None

    def wait(self) -> int:
        if self._killed:
            return 137
        msg = "HangingHandle.wait would block indefinitely"
        raise RuntimeError(msg)

    def send_signal_to_group(self, sig: int) -> None:
        self.received_signals.append(sig)
        if self.exit_on_kill and sig == 9:
            self._killed = True


__all__ = ["HangingHandle", "RecordingHandle", "RecordingSpawner"]


# The double classes implement the Protocols structurally.
_: type[ProcessSpawner] = RecordingSpawner
_2: type[ProcessHandle] = RecordingHandle
_3: type[ProcessHandle] = HangingHandle
