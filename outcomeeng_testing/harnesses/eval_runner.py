"""Resource-managed observations for eval runner compliance tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from outcomeeng_evals.runner import (
    ClaudeCliRunner,
    ClaudeEnvironmentVariable,
    ClaudeResultField,
    ClaudeUsageField,
    RunMetadata,
    RunResult,
    _metadata_from_envelope,
)
from outcomeeng_testing.evals.fakes import (
    RecordingSubprocessRunner,
    SubprocessCall,
)

_API_KEY_VALUE = "test-api-key"
_OAUTH_TOKEN_VALUE = "test-oauth-token"
_NESTING_MARKER_VALUE = "active"
_RUNNER_PROMPT = "observe the runner boundary"
_FALLBACK_WALL_CLOCK_MS = 1234.5


@dataclass(frozen=True)
class RunnerObservation:
    """A real runner result plus the injected subprocess boundary observation."""

    runner: ClaudeCliRunner
    result: RunResult
    call: SubprocessCall
    envelope: dict[str, object]
    provisioned_oauth_token: str | None

    @property
    def fixture_result(self) -> str:
        return _require_str(self.envelope, ClaudeResultField.RESULT)

    @property
    def fixture_duration_ms(self) -> float:
        return _require_float(self.envelope, ClaudeResultField.DURATION_MS)

    @property
    def fixture_total_cost_usd(self) -> float:
        return _require_float(self.envelope, ClaudeResultField.TOTAL_COST_USD)

    @property
    def fixture_input_tokens(self) -> int:
        return _require_usage_int(self.envelope, ClaudeUsageField.INPUT_TOKENS)

    @property
    def fixture_output_tokens(self) -> int:
        return _require_usage_int(self.envelope, ClaudeUsageField.OUTPUT_TOKENS)

    @property
    def fixture_cache_read_input_tokens(self) -> int:
        return _require_usage_int(
            self.envelope,
            ClaudeUsageField.CACHE_READ_INPUT_TOKENS,
        )

    @property
    def fixture_cache_creation_input_tokens(self) -> int:
        return _require_usage_int(
            self.envelope,
            ClaudeUsageField.CACHE_CREATION_INPUT_TOKENS,
        )

    @property
    def fixture_num_turns(self) -> int:
        return _require_int(self.envelope, ClaudeResultField.NUM_TURNS)

    @property
    def fixture_stop_reason(self) -> str:
        return _require_str(self.envelope, ClaudeResultField.STOP_REASON)


@dataclass(frozen=True)
class MetadataObservation:
    """Metadata parsed from a deliberately reduced external envelope."""

    metadata: RunMetadata
    wall_clock_ms: float


def observe_default_runner() -> RunnerObservation:
    return _observe_runner()


def observe_runner_with_nesting_marker() -> RunnerObservation:
    return _observe_runner(oauth_token=_OAUTH_TOKEN_VALUE, nesting_marker=True)


def observe_runner_with_api_key() -> RunnerObservation:
    return _observe_runner(api_key=_API_KEY_VALUE)


def observe_runner_with_oauth_token() -> RunnerObservation:
    return _observe_runner(oauth_token=_OAUTH_TOKEN_VALUE)


def observe_runner_with_empty_api_key() -> RunnerObservation:
    return _observe_runner(api_key="", oauth_token=_OAUTH_TOKEN_VALUE)


def observe_runner_with_bare_override() -> RunnerObservation:
    return _observe_runner(bare=True)


def observe_runner_with_non_bare_override() -> RunnerObservation:
    return _observe_runner(api_key=_API_KEY_VALUE, bare=False)


def observe_metadata_without_duration() -> MetadataObservation:
    envelope = _load_envelope()
    envelope.pop(ClaudeResultField.DURATION_MS)
    return MetadataObservation(
        metadata=_metadata_from_envelope(envelope, _FALLBACK_WALL_CLOCK_MS),
        wall_clock_ms=_FALLBACK_WALL_CLOCK_MS,
    )


def observe_metadata_with_optional_fields_absent() -> MetadataObservation:
    envelope = _load_envelope()
    reduced_envelope: dict[str, object] = {
        ClaudeResultField.RESULT: envelope[ClaudeResultField.RESULT],
    }
    return MetadataObservation(
        metadata=_metadata_from_envelope(reduced_envelope, _FALLBACK_WALL_CLOCK_MS),
        wall_clock_ms=_FALLBACK_WALL_CLOCK_MS,
    )


def _observe_runner(
    *,
    api_key: str | None = None,
    oauth_token: str | None = None,
    nesting_marker: bool = False,
    bare: bool | None = None,
) -> RunnerObservation:
    envelope = _load_envelope()
    command = RecordingSubprocessRunner(stdout=json.dumps(envelope))
    with pytest.MonkeyPatch.context() as environment:
        environment.delenv(
            ClaudeEnvironmentVariable.ANTHROPIC_API_KEY,
            raising=False,
        )
        environment.delenv(
            ClaudeEnvironmentVariable.CLAUDE_CODE_OAUTH_TOKEN,
            raising=False,
        )
        environment.delenv(
            ClaudeEnvironmentVariable.NESTING_MARKER,
            raising=False,
        )
        if api_key is not None:
            environment.setenv(
                ClaudeEnvironmentVariable.ANTHROPIC_API_KEY,
                api_key,
            )
        if oauth_token is not None:
            environment.setenv(
                ClaudeEnvironmentVariable.CLAUDE_CODE_OAUTH_TOKEN,
                oauth_token,
            )
        if nesting_marker:
            environment.setenv(
                ClaudeEnvironmentVariable.NESTING_MARKER,
                _NESTING_MARKER_VALUE,
            )
        with TemporaryDirectory() as directory:
            runner = ClaudeCliRunner(
                plugin_dir=Path(directory),
                bare=bare,
                run_command=command,
            )
            result = runner.run(_RUNNER_PROMPT)
    return RunnerObservation(
        runner=runner,
        result=result,
        call=command.calls[0],
        envelope=envelope,
        provisioned_oauth_token=oauth_token,
    )


def _load_envelope() -> dict[str, object]:
    path = (
        Path(__file__).parents[1] / "fixtures" / "evals" / "claude_result_envelope.json"
    )
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected object envelope, got {type(payload).__name__}")
    return {str(key): value for key, value in payload.items()}


def _require_usage_int(
    envelope: dict[str, object],
    field: ClaudeUsageField,
) -> int:
    usage = envelope[ClaudeResultField.USAGE]
    if not isinstance(usage, dict):
        raise TypeError(f"expected usage object, got {type(usage).__name__}")
    return _require_int({str(key): value for key, value in usage.items()}, field)


def _require_int(
    mapping: dict[str, object],
    field: ClaudeResultField | ClaudeUsageField,
) -> int:
    value = mapping[field]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"expected integer {field}, got {type(value).__name__}")
    return value


def _require_float(
    mapping: dict[str, object],
    field: ClaudeResultField,
) -> float:
    value = mapping[field]
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"expected number {field}, got {type(value).__name__}")
    return float(value)


def _require_str(
    mapping: dict[str, object],
    field: ClaudeResultField,
) -> str:
    value = mapping[field]
    if not isinstance(value, str):
        raise TypeError(f"expected string {field}, got {type(value).__name__}")
    return value
