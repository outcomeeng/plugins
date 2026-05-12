"""Model runners that produce assistant messages for an eval prompt.

``ClaudeCliRunner`` shells out to ``claude --print --output-format json``
using the user's OAuth subscription. Each call is a single bounded
subprocess invocation; no polling, no streaming watchers. The runner
strips ``CLAUDECODE`` from the inherited environment so nested
invocations from inside a Claude Code session use the subprocess
contract rather than the interactive guard.

Test fakes (stubs, recorders) live in ``outcomeeng_evals.testing.fakes``.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


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
class ClaudeCliRunner:
    """Spawn ``claude`` in non-interactive print mode and return the response."""

    plugin_dir: Path
    binary: str = "claude"
    max_budget_usd: float | None = 0.50
    timeout_seconds: float = 120.0

    def run(self, prompt: str) -> RunResult:
        argv = [
            self.binary,
            "--print",
            "--output-format",
            "json",
            "--no-session-persistence",
            "--plugin-dir",
            str(self.plugin_dir),
        ]
        if self.max_budget_usd is not None:
            argv.extend(["--max-budget-usd", f"{self.max_budget_usd:.4f}"])
        start = time.perf_counter()
        completed = subprocess.run(
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


def _subprocess_env() -> dict[str, str]:
    """Return a copy of the parent env with the Claude Code nesting guard removed.

    The full parent environment is passed through deliberately: ``claude``
    resolves the user's OAuth subscription (and any other auth it needs)
    from inherited variables, so narrowing the env to an allow-list would
    break authentication. The only key dropped is ``CLAUDECODE`` — leaving
    it set would make the nested call take the interactive-guard path
    instead of the print-mode subprocess contract. Do not narrow this in a
    future refactor.

    In CI, this means job-level secrets injected as environment variables
    (deployment tokens, cloud credentials, an unrelated ``ANTHROPIC_API_KEY``)
    are also forwarded to the ``claude`` subprocess. That is acceptable —
    ``claude`` consumes only what it needs — but it is the reason a filter
    must not be added: a future maintainer cannot know which inherited
    variable ``claude`` depends on for auth, so dropping any of them risks
    breaking it.
    """
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
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
