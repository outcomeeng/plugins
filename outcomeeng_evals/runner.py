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

Test fakes (stubs, recorders) live in ``outcomeeng_evals.testing.fakes``.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from outcomeeng_evals.definition import DEFAULT_MODEL
from outcomeeng_evals.settings import (
    ADVISOR_MODEL_SETTING,
    DEFAULT_MAX_BUDGET_USD,
    DEFAULT_TIMEOUT_SECONDS,
    DISABLED_ADVISOR_MODEL,
)

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
CLAUDE_CODE_OAUTH_TOKEN_ENV = "CLAUDE_CODE_OAUTH_TOKEN"
CLAUDECODE_ENV = "CLAUDECODE"
DEFAULT_CLAUDE_BINARY = "claude"
BARE_FLAG = "--bare"
PRINT_FLAG = "--print"
OUTPUT_FORMAT_FLAG = "--output-format"
JSON_OUTPUT_FORMAT = "json"
NO_SESSION_PERSISTENCE_FLAG = "--no-session-persistence"
SETTINGS_FLAG = "--settings"
MODEL_FLAG = "--model"
PLUGIN_DIR_FLAG = "--plugin-dir"
MAX_BUDGET_FLAG = "--max-budget-usd"


@dataclass(frozen=True)
class RunMetadata:
    """Optional per-invocation metadata.

    All fields are ``None`` when the runner does not expose them (for
    example, the stub runners under ``outcomeeng_evals.testing.fakes`` used
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


@dataclass(frozen=True)
class ModelProcessInvocation:
    """Complete input to one automated model subprocess."""

    argv: tuple[str, ...]
    prompt: str
    timeout_seconds: float
    environment: Mapping[str, str]


@dataclass(frozen=True)
class ModelProcessResult:
    """Normalized output from one automated model subprocess."""

    returncode: int
    stdout: str
    stderr: str
    duration_ms: float


class ModelProcessLauncher(Protocol):
    """Execute one bounded automated model subprocess."""

    def __call__(self, invocation: ModelProcessInvocation) -> ModelProcessResult: ...


def launch_model_process(invocation: ModelProcessInvocation) -> ModelProcessResult:
    """Execute the repository's single automated model-process boundary."""

    start = time.perf_counter()
    completed = subprocess.run(
        invocation.argv,
        input=invocation.prompt,
        capture_output=True,
        text=True,
        timeout=invocation.timeout_seconds,
        check=False,
        env=invocation.environment,
    )
    return ModelProcessResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_ms=(time.perf_counter() - start) * 1000.0,
    )


@dataclass(frozen=True)
class ClaudeCliRunner:
    """Spawn ``claude`` in non-interactive print mode and return the response."""

    plugin_dir: Path
    model: str = DEFAULT_MODEL
    binary: str = DEFAULT_CLAUDE_BINARY
    max_budget_usd: float | None = DEFAULT_MAX_BUDGET_USD
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    bare: bool | None = None
    environment: Mapping[str, str] | None = None
    process_launcher: ModelProcessLauncher = launch_model_process

    def run(self, prompt: str) -> RunResult:
        environment = _subprocess_env(self.environment)
        argv = [self.binary]
        if self._effective_bare(environment):
            argv.append(BARE_FLAG)
        argv.extend(
            [
                PRINT_FLAG,
                OUTPUT_FORMAT_FLAG,
                JSON_OUTPUT_FORMAT,
                NO_SESSION_PERSISTENCE_FLAG,
                SETTINGS_FLAG,
                json.dumps(
                    {ADVISOR_MODEL_SETTING: DISABLED_ADVISOR_MODEL},
                    separators=(",", ":"),
                ),
                MODEL_FLAG,
                self.model,
                PLUGIN_DIR_FLAG,
                str(self.plugin_dir),
            ]
        )
        if self.max_budget_usd is not None:
            argv.extend([MAX_BUDGET_FLAG, f"{self.max_budget_usd:.4f}"])
        completed = self.process_launcher(
            ModelProcessInvocation(
                argv=tuple(argv),
                prompt=prompt,
                timeout_seconds=self.timeout_seconds,
                environment=environment,
            )
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "claude exited "
                f"{completed.returncode}: "
                f"{completed.stderr.strip() or completed.stdout.strip()}"
            )
        envelope = json.loads(completed.stdout)
        return RunResult(
            text=_assistant_text(envelope),
            metadata=_metadata_from_envelope(envelope, completed.duration_ms),
        )

    def _effective_bare(self, environment: Mapping[str, str]) -> bool:
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
        return bool(environment.get(ANTHROPIC_API_KEY_ENV))


def _subprocess_env(environment: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a copy of the parent env with the Claude Code nesting guard removed.

    The full parent environment is passed through deliberately: ``claude``
    resolves auth from the environment the operator already provisioned, so
    narrowing the env to an allow-list could drop required auth variables. The
    only key dropped is ``CLAUDECODE``; leaving it set would make the nested
    call take the interactive-guard path instead of the print-mode subprocess
    contract.
    """
    env = dict(os.environ if environment is None else environment)
    env.pop(CLAUDECODE_ENV, None)
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
    for key in ("result", "response", "content"):
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
    duration_ms = _coerce_float(envelope.get("duration_ms"))
    if duration_ms is None:
        duration_ms = wall_clock_ms
    raw_usage = envelope.get("usage")
    usage: dict[str, object] = raw_usage if isinstance(raw_usage, dict) else {}
    return RunMetadata(
        duration_ms=duration_ms,
        total_cost_usd=_coerce_float(envelope.get("total_cost_usd")),
        input_tokens=_coerce_int(usage.get("input_tokens")),
        output_tokens=_coerce_int(usage.get("output_tokens")),
        cache_read_input_tokens=_coerce_int(usage.get("cache_read_input_tokens")),
        cache_creation_input_tokens=_coerce_int(
            usage.get("cache_creation_input_tokens")
        ),
        num_turns=_coerce_int(envelope.get("num_turns")),
        stop_reason=_coerce_str(envelope.get("stop_reason")),
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
