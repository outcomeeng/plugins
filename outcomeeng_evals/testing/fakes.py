"""Stub and recording runners for l1 meta-tests of the eval harness."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from outcomeeng_evals.runner import ModelRunner, RunMetadata, RunResult


@dataclass(frozen=True)
class StubModelRunner:
    """Return a canned ``RunResult`` for any prompt.

    Supply either ``response`` (a single canned text) or ``responder`` (a
    callable mapping prompt -> response text). Metadata is empty unless
    ``metadata`` is supplied.
    """

    response: str = ""
    responder: Callable[[str], str] | None = field(default=None)
    metadata: RunMetadata = field(default_factory=RunMetadata)

    def run(self, prompt: str) -> RunResult:
        text = self.responder(prompt) if self.responder is not None else self.response
        return RunResult(text=text, metadata=self.metadata)


@dataclass(frozen=True)
class RaisingModelRunner:
    """A ``ModelRunner`` whose ``run`` always raises ``error``.

    For meta-tests of suite-level fault isolation: a real ``claude``
    non-zero exit or timeout surfaces as an exception out of ``run`` (a
    ``RuntimeError`` or ``subprocess.TimeoutExpired``), and ``run_suite``
    must convert it to a failing outcome rather than crash the whole run.
    """

    error: BaseException

    def run(self, prompt: str) -> RunResult:  # noqa: ARG002 — prompt is unused; this runner always raises before reading it
        raise self.error


@dataclass
class RecordingRunner:
    """Wrap another runner and record every prompt and response.

    Not ``frozen=True`` — the runner is inherently stateful: ``run`` appends
    each (prompt, result) pair to ``transcripts``. The dataclass is mutable
    so the list can grow across invocations.

    Not safe for parallel use: ``transcripts.append`` is GIL-atomic in
    CPython but offers no ordering or isolation guarantee across threads or
    processes. Recording under ``run_suite(workers > 1)`` (or a
    ``ProcessPoolExecutor``) needs an external lock; the meta-tests that
    use this runner are single-threaded.
    """

    inner: ModelRunner
    transcripts: list[tuple[str, RunResult]] = field(default_factory=list)

    def run(self, prompt: str) -> RunResult:
        result = self.inner.run(prompt)
        self.transcripts.append((prompt, result))
        return result
