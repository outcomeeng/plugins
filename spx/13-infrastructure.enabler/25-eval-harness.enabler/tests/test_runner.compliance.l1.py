"""Compliance evidence for the eval model-runner boundary."""

from __future__ import annotations

import json
import os

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
    RunResult,
)
from outcomeeng_evals.settings import ADVISOR_MODEL_SETTING, DISABLED_ADVISOR_MODEL
from outcomeeng_testing.evals.fakes import StubModelRunner
from outcomeeng_testing.harnesses.eval_runner import (
    metadata_from_envelope,
    process_fixture,
    recording_runner,
    subprocess_environment,
)


def test_subprocess_environment_strips_claudecode_marker() -> None:
    environment = subprocess_environment(
        {CLAUDECODE_ENV: "present", "PATH": os.defpath}
    )

    assert CLAUDECODE_ENV not in environment
    assert environment["PATH"] == os.defpath


def test_metadata_matches_captured_envelope() -> None:
    fixture = process_fixture()

    assert metadata_from_envelope(fixture.envelope) == fixture.expected_metadata


def test_metadata_preserves_absence() -> None:
    metadata = metadata_from_envelope({})

    assert metadata.duration_ms is None
    assert metadata.total_cost_usd is None
    assert metadata.input_tokens is None
    assert metadata.output_tokens is None
    assert metadata.cache_read_input_tokens is None
    assert metadata.cache_creation_input_tokens is None
    assert metadata.num_turns is None
    assert metadata.stop_reason is None


def test_stub_runner_replays_fixture_result() -> None:
    fixture = process_fixture()

    result = StubModelRunner(
        response=fixture.expected_text,
        metadata=fixture.expected_metadata,
    ).run(fixture.prompt)

    assert isinstance(result, RunResult)
    assert result.text == fixture.expected_text
    assert result.metadata == fixture.expected_metadata


def test_claude_runner_replays_captured_process_contract() -> None:
    fixture = process_fixture()
    runner, recorder = recording_runner(fixture)

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


def test_claude_runner_raises_diagnostic_on_nonzero_exit() -> None:
    fixture = process_fixture()
    runner, _recorder = recording_runner(fixture, returncode=os.EX_USAGE)

    with pytest.raises(RuntimeError, match=f"claude exited {os.EX_USAGE}"):
        runner.run(fixture.prompt)


def test_claude_runner_auth_mapping_matches_fixture() -> None:
    fixture = process_fixture()

    for auth_case in fixture.auth_cases:
        runner, recorder = recording_runner(
            fixture,
            environment=auth_case.environment,
            bare=auth_case.bare_override,
        )

        runner.run(fixture.prompt)

        has_bare = BARE_FLAG in recorder.invocations[0].argv
        assert has_bare is auth_case.expected_bare, auth_case.name
