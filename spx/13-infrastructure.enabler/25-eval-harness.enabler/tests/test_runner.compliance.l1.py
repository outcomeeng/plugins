"""Compliance tests for the eval model-runner boundary."""

import json
import os

import pytest

from outcomeeng.models import EVAL_PROFILE_MODELS
from outcomeeng_evals.definition import DEFAULT_PROFILE
from outcomeeng_evals.runner import (
    BARE_FLAG,
    CLAUDECODE_ENV,
    EFFORT_FLAG,
    JSON_OUTPUT_FORMAT,
    MAX_BUDGET_FLAG,
    MODEL_FLAG,
    NONZERO_EXIT_DIAGNOSTIC_PREFIX,
    NO_SESSION_PERSISTENCE_FLAG,
    OUTPUT_FORMAT_FLAG,
    PLUGIN_DIR_FLAG,
    PRINT_FLAG,
    SETTINGS_FLAG,
    RunResult,
    _metadata_from_envelope,
    _subprocess_env,
)
from outcomeeng_evals.settings import ADVISOR_MODEL_SETTING, DISABLED_ADVISOR_MODEL
from outcomeeng_testing.evals.fakes import StubModelRunner
from outcomeeng_testing.harnesses.eval_runner import (
    captured_process_fixture,
    recording_runner,
    replay_captured_process_contract,
)


def test_subprocess_environment_strips_claudecode_marker() -> None:
    environment = _subprocess_env({CLAUDECODE_ENV: "present", "PATH": os.defpath})

    assert CLAUDECODE_ENV not in environment
    assert environment["PATH"] == os.defpath


def test_metadata_matches_captured_envelope() -> None:
    fixture = captured_process_fixture()

    metadata = _metadata_from_envelope(fixture.envelope)

    assert metadata == fixture.expected_metadata


def test_metadata_preserves_absence() -> None:
    metadata = _metadata_from_envelope({})

    assert metadata.duration_ms is None
    assert metadata.total_cost_usd is None
    assert metadata.input_tokens is None
    assert metadata.output_tokens is None
    assert metadata.cache_read_input_tokens is None
    assert metadata.cache_creation_input_tokens is None
    assert metadata.num_turns is None
    assert metadata.stop_reason is None


def test_stub_runner_replays_fixture_result() -> None:
    fixture = captured_process_fixture()

    result = StubModelRunner(
        response=fixture.expected_text,
        metadata=fixture.expected_metadata,
    ).run(fixture.prompt)

    assert isinstance(result, RunResult)
    assert result.text == fixture.expected_text
    assert result.metadata == fixture.expected_metadata


def test_claude_runner_replays_captured_process_contract() -> None:
    replay = replay_captured_process_contract()

    assert replay.result.text == replay.fixture.expected_text
    assert replay.result.metadata == replay.fixture.expected_metadata
    (invocation,) = replay.invocations
    argv = invocation.argv
    assert invocation.prompt == replay.fixture.prompt
    assert (
        argv[argv.index(MODEL_FLAG) + 1] == EVAL_PROFILE_MODELS[DEFAULT_PROFILE].model
    )
    assert (
        argv[argv.index(EFFORT_FLAG) + 1] == EVAL_PROFILE_MODELS[DEFAULT_PROFILE].effort
    )
    assert argv[0] == replay.runner.binary
    assert PRINT_FLAG in argv
    assert NO_SESSION_PERSISTENCE_FLAG in argv
    assert argv[argv.index(OUTPUT_FORMAT_FLAG) + 1] == JSON_OUTPUT_FORMAT
    assert argv[argv.index(PLUGIN_DIR_FLAG) + 1] == str(replay.runner.plugin_dir)
    assert replay.runner.max_budget_usd is not None
    assert argv[argv.index(MAX_BUDGET_FLAG) + 1] == (
        f"{replay.runner.max_budget_usd:.4f}"
    )
    settings = json.loads(argv[argv.index(SETTINGS_FLAG) + 1])
    assert settings == {ADVISOR_MODEL_SETTING: DISABLED_ADVISOR_MODEL}
    assert CLAUDECODE_ENV not in invocation.environment


def test_claude_runner_raises_diagnostic_on_nonzero_exit() -> None:
    fixture = captured_process_fixture()
    runner, _recorder = recording_runner(fixture, returncode=os.EX_USAGE)

    with pytest.raises(
        RuntimeError, match=f"{NONZERO_EXIT_DIAGNOSTIC_PREFIX}{os.EX_USAGE}"
    ):
        runner.run(fixture.prompt)


def test_claude_runner_auth_mapping_matches_fixture() -> None:
    fixture = captured_process_fixture()

    for auth_case in fixture.auth_cases:
        runner, recorder = recording_runner(
            fixture,
            environment=auth_case.environment,
            bare=auth_case.bare_override,
        )

        runner.run(fixture.prompt)

        (invocation,) = recorder.invocations
        assert (BARE_FLAG in invocation.argv) is auth_case.expected_bare, auth_case.name
