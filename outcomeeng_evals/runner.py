"""Model runners that produce assistant messages for an eval prompt.

``ClaudeCliRunner`` shells out to ``claude --print --output-format json``.
The runner follows the auth mode already provisioned in the inherited
environment: when ``ANTHROPIC_API_KEY`` is set to a non-empty value it passes
``--bare``; when ``ANTHROPIC_API_KEY`` is unset or empty it omits ``--bare``
and preserves the inherited environment, including ``CLAUDE_CODE_OAUTH_TOKEN``
when present. Agents use the provisioned mode as found and do not ask operators
to add, remove, or switch auth secrets for an eval run.
Callers may force the flag on or off by passing ``bare=True`` or
``bare=False`` to the constructor for direct test coverage and explicit
embedding use; the default ``bare=None`` follows the inherited environment.

Each call is a single bounded subprocess invocation; no polling, no
streaming watchers. The runner strips ``CLAUDECODE`` from the inherited
environment so nested invocations from inside a Claude Code session use
the subprocess contract rather than the interactive guard.

Test fakes (stubs, recorders) live in ``outcomeeng_testing.evals.fakes``.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from outcomeeng_evals.definition import DEFAULT_MODEL


class ClaudeCliArgument(StrEnum):
    """Source-owned command-line vocabulary for Claude print-mode runs."""

    BARE = "--bare"
    PRINT = "--print"
    OUTPUT_FORMAT = "--output-format"
    NO_SESSION_PERSISTENCE = "--no-session-persistence"
    MODEL = "--model"
    PLUGIN_DIR = "--plugin-dir"
    MAX_BUDGET_USD = "--max-budget-usd"


class ClaudeEnvironmentVariable(StrEnum):
    """Environment keys that affect Claude runner behavior."""

    ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
    CLAUDE_CODE_OAUTH_TOKEN = "CLAUDE_CODE_OAUTH_TOKEN"
    NESTING_MARKER = "CLAUDECODE"


class ClaudeResultField(StrEnum):
    """Top-level fields consumed from the Claude JSON result envelope."""

    RESULT = "result"
    RESPONSE = "response"
    CONTENT = "content"
    DURATION_MS = "duration_ms"
    TOTAL_COST_USD = "total_cost_usd"
    USAGE = "usage"
    NUM_TURNS = "num_turns"
    STOP_REASON = "stop_reason"


class ClaudeUsageField(StrEnum):
    """Usage fields consumed from the Claude JSON result envelope."""

    INPUT_TOKENS = "input_tokens"
    OUTPUT_TOKENS = "output_tokens"
    CACHE_READ_INPUT_TOKENS = "cache_read_input_tokens"
    CACHE_CREATION_INPUT_TOKENS = "cache_creation_input_tokens"


CLAUDE_OUTPUT_FORMAT = "json"


@dataclass(frozen=True)
class RunMetadata:
    """Optional per-invocation metadata.

    All fields are ``None`` when the runner does not expose them (for
    example, the stub runners under ``outcomeeng_testing.evals.fakes`` used
    by l1 meta-tests). Downstream callers must tolerate missing metadata.
    """

    duration_ms: float | None = None
    total_cost_usd: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_input_tokens: int | None = None
    cache_creation_input_tokens: int | None = None
    num_turns: int | None = None
    stop_reason: str | None = None


@dataclass(frozen=True)
class RunResult:
    """A model invocation's textual result plus metadata."""

    text: str
    metadata: RunMetadata = field(default_factory=RunMetadata)


class ModelRunner(Protocol):
    """Run a prompt and return a ``RunResult``."""

    def run(self, prompt: str) -> RunResult: ...


class SubprocessRunner(Protocol):
    """Execute one bounded Claude CLI subprocess."""

    def __call__(
        self,
        argv: list[str],
        *,
        input: str,
        capture_output: bool,
        text: bool,
        timeout: float,
        check: bool,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]: ...


def _run_subprocess(
    argv: list[str],
    *,
    input: str,
    capture_output: bool,
    text: bool,
    timeout: float,
    check: bool,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        input=input,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        check=check,
        env=env,
    )


@dataclass(frozen=True)
class ClaudeCliRunner:
    """Spawn ``claude`` in non-interactive print mode and return the response."""

    plugin_dir: Path
    model: str = DEFAULT_MODEL
    binary: str = "claude"
    max_budget_usd: float | None = 0.50
    timeout_seconds: float = 120.0
    bare: bool | None = None
    run_command: SubprocessRunner = _run_subprocess

    def run(self, prompt: str) -> RunResult:
        argv = [self.binary]
        if self._effective_bare():
            argv.append(ClaudeCliArgument.BARE)
        argv.extend(
            [
                ClaudeCliArgument.PRINT,
                ClaudeCliArgument.OUTPUT_FORMAT,
                CLAUDE_OUTPUT_FORMAT,
                ClaudeCliArgument.NO_SESSION_PERSISTENCE,
                ClaudeCliArgument.MODEL,
                self.model,
                ClaudeCliArgument.PLUGIN_DIR,
                str(self.plugin_dir),
            ]
        )
        if self.max_budget_usd is not None:
            argv.extend(
                [
                    ClaudeCliArgument.MAX_BUDGET_USD,
                    f"{self.max_budget_usd:.4f}",
                ]
            )
        start = time.perf_counter()
        completed = self.run_command(
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
            env=_subprocess_env(),
        )
        wall_clock_ms = (time.perf_counter() - start) * 1000.0
        if completed.returncode != 0:
            raise RuntimeError(
                "claude exited "
                f"{completed.returncode}: "
                f"{completed.stderr.strip() or completed.stdout.strip()}"
            )
        envelope = json.loads(completed.stdout)
        return RunResult(
            text=_assistant_text(envelope),
            metadata=_metadata_from_envelope(envelope, wall_clock_ms),
        )

    def _effective_bare(self) -> bool:
        """Return True iff ``--bare`` should be added to the argv.

        ``bare=True`` or ``bare=False`` is an explicit caller override for
        direct test coverage and embedding. ``bare=None`` (the default)
        follows the inherited environment: ``--bare`` is added only when
        ``ANTHROPIC_API_KEY`` is set to a non-empty value. An empty value is
        treated as unset, so the call omits ``--bare`` and leaves inherited
        non-bare auth variables available to the subprocess.
        """
        if self.bare is not None:
            return self.bare
        return bool(os.environ.get(ClaudeEnvironmentVariable.ANTHROPIC_API_KEY))


def _subprocess_env() -> dict[str, str]:
    """Return a copy of the parent env with the Claude Code nesting guard removed.

    The full parent environment is passed through deliberately: ``claude``
    resolves auth from the environment the operator already provisioned, so
    narrowing the env to an allow-list could drop required auth variables. The
    only key dropped is ``CLAUDECODE``; leaving it set would make the nested
    call take the interactive-guard path instead of the print-mode subprocess
    contract.
    """
    env = dict(os.environ)
    env.pop(ClaudeEnvironmentVariable.NESTING_MARKER, None)
    return env


def _assistant_text(envelope: object) -> str:
    """Extract the assistant text from a ``claude --output-format json`` envelope.

    Tries ``result`` first (the active key in claude CLI ~1.x), then
    ``response`` and ``content`` as backwards-compat aliases for older CLI
    builds. If the active key changes in a future release, update this
    fallback order rather than letting the runtime ``ValueError`` surface
    after a silent envelope shift.
    """
    if not isinstance(envelope, dict):
        raise ValueError(
            f"expected JSON object envelope, got {type(envelope).__name__}"
        )
    for key in (
        ClaudeResultField.RESULT,
        ClaudeResultField.RESPONSE,
        ClaudeResultField.CONTENT,
    ):
        value = envelope.get(key)
        if isinstance(value, str):
            return value
    raise ValueError(
        f"no result/response/content field in envelope: {sorted(envelope.keys())}"
    )


def _metadata_from_envelope(
    envelope: dict[str, object], wall_clock_ms: float
) -> RunMetadata:
    """Pull cost and timing fields out of a claude JSON envelope.

    Falls back to wall-clock duration when the envelope omits ``duration_ms``.
    """
    duration_ms = _coerce_float(envelope.get(ClaudeResultField.DURATION_MS))
    if duration_ms is None:
        duration_ms = wall_clock_ms
    raw_usage = envelope.get(ClaudeResultField.USAGE)
    usage: dict[str, object] = raw_usage if isinstance(raw_usage, dict) else {}
    return RunMetadata(
        duration_ms=duration_ms,
        total_cost_usd=_coerce_float(envelope.get(ClaudeResultField.TOTAL_COST_USD)),
        input_tokens=_coerce_int(usage.get(ClaudeUsageField.INPUT_TOKENS)),
        output_tokens=_coerce_int(usage.get(ClaudeUsageField.OUTPUT_TOKENS)),
        cache_read_input_tokens=_coerce_int(
            usage.get(ClaudeUsageField.CACHE_READ_INPUT_TOKENS)
        ),
        cache_creation_input_tokens=_coerce_int(
            usage.get(ClaudeUsageField.CACHE_CREATION_INPUT_TOKENS)
        ),
        num_turns=_coerce_int(envelope.get(ClaudeResultField.NUM_TURNS)),
        stop_reason=_coerce_str(envelope.get(ClaudeResultField.STOP_REASON)),
    )


def _coerce_int(value: object) -> int | None:
    return (
        int(value) if isinstance(value, int) and not isinstance(value, bool) else None
    )


def _coerce_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _coerce_str(value: object) -> str | None:
    return value if isinstance(value, str) else None
