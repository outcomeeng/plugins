"""Evidence harness for the eval model-runner boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from outcomeeng_evals.runner import (
    BARE_FLAG,
    CLAUDECODE_ENV,
    JSON_OUTPUT_FORMAT,
    MAX_BUDGET_FLAG,
    MODEL_FLAG,
    NO_SESSION_PERSISTENCE_FLAG,
    OUTPUT_FORMAT_FLAG,
    PLUGIN_DIR_FLAG,
    PRINT_FLAG,
    SETTINGS_FLAG,
    ClaudeCliRunner,
    RunResult,
    _metadata_from_envelope,
    _subprocess_env,
)
from outcomeeng_evals.settings import ADVISOR_MODEL_SETTING, DISABLED_ADVISOR_MODEL
from outcomeeng_evals.testing.factories import (
    ModelProcessFixture,
    load_model_process_fixture,
    make_recording_model_process_launcher,
)
from outcomeeng_evals.testing.fakes import (
    RecordingModelProcessLauncher,
    StubModelRunner,
)

_FIXTURE_PATH = (
    Path(__file__).parents[1] / "fixtures/evals/claude_process_contract.json"
)


def assert_subprocess_environment_strips_claudecode_marker() -> None:
    environment = _subprocess_env({CLAUDECODE_ENV: "present", "PATH": os.defpath})

    assert CLAUDECODE_ENV not in environment
    assert environment["PATH"] == os.defpath


def assert_metadata_matches_captured_envelope() -> None:
    fixture = _fixture()

    metadata = _metadata_from_envelope(
        fixture.envelope,
        wall_clock_ms=fixture.expected_metadata.duration_ms or 0.0,
    )

    assert metadata == fixture.expected_metadata


def assert_metadata_preserves_absence() -> None:
    fixture = _fixture()

    metadata = _metadata_from_envelope(
        {}, wall_clock_ms=fixture.expected_metadata.duration_ms or 0.0
    )

    assert metadata.total_cost_usd is None
    assert metadata.input_tokens is None
    assert metadata.output_tokens is None
    assert metadata.stop_reason is None


def assert_stub_runner_replays_fixture_result() -> None:
    fixture = _fixture()
    result = StubModelRunner(
        response=fixture.expected_text,
        metadata=fixture.expected_metadata,
    ).run(fixture.prompt)

    assert isinstance(result, RunResult)
    assert result.text == fixture.expected_text
    assert result.metadata == fixture.expected_metadata


def assert_claude_runner_replays_captured_process_contract() -> None:
    fixture = _fixture()
    runner, recorder = _recording_runner(fixture)

    result = runner.run(fixture.prompt)

    assert result.text == fixture.expected_text
    assert result.metadata == fixture.expected_metadata
    invocation = recorder.invocations[0]
    assert invocation.prompt == fixture.prompt
    assert invocation.argv[invocation.argv.index(MODEL_FLAG) + 1] == (
        fixture.explicit_model
    )
    assert invocation.argv[0] == runner.binary
    assert PRINT_FLAG in invocation.argv
    assert NO_SESSION_PERSISTENCE_FLAG in invocation.argv
    assert invocation.argv[invocation.argv.index(OUTPUT_FORMAT_FLAG) + 1] == (
        JSON_OUTPUT_FORMAT
    )
    assert invocation.argv[invocation.argv.index(PLUGIN_DIR_FLAG) + 1] == str(
        runner.plugin_dir
    )
    assert runner.max_budget_usd is not None
    assert invocation.argv[invocation.argv.index(MAX_BUDGET_FLAG) + 1] == (
        f"{runner.max_budget_usd:.4f}"
    )
    settings = json.loads(invocation.argv[invocation.argv.index(SETTINGS_FLAG) + 1])
    assert settings == {ADVISOR_MODEL_SETTING: DISABLED_ADVISOR_MODEL}
    assert CLAUDECODE_ENV not in invocation.environment


def assert_claude_runner_raises_diagnostic_on_nonzero_exit() -> None:
    fixture = _fixture()
    recorder = make_recording_model_process_launcher(fixture, returncode=os.EX_USAGE)
    runner = ClaudeCliRunner(
        plugin_dir=Path.cwd(),
        process_launcher=recorder,
        environment={},
    )

    with pytest.raises(RuntimeError, match=f"claude exited {os.EX_USAGE}"):
        runner.run(fixture.prompt)


def assert_claude_runner_auth_mapping_matches_fixture() -> None:
    fixture = _fixture()

    for auth_case in fixture.auth_cases:
        runner, recorder = _recording_runner(
            fixture,
            environment=auth_case.environment,
            bare=auth_case.bare_override,
        )

        runner.run(fixture.prompt)

        has_bare = BARE_FLAG in recorder.invocations[0].argv
        assert has_bare is auth_case.expected_bare, auth_case.name


def _fixture() -> ModelProcessFixture:
    return load_model_process_fixture(_FIXTURE_PATH)


def _recording_runner(
    fixture: ModelProcessFixture,
    *,
    environment: dict[str, str] | None = None,
    bare: bool | None = None,
) -> tuple[ClaudeCliRunner, RecordingModelProcessLauncher]:
    recorder = make_recording_model_process_launcher(fixture)
    runner = ClaudeCliRunner(
        plugin_dir=Path.cwd(),
        model=fixture.explicit_model,
        environment={} if environment is None else environment,
        bare=bare,
        process_launcher=recorder,
    )
    return runner, recorder
