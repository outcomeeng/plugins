"""Assertion entrypoints for runner compliance evidence."""

from __future__ import annotations

from outcomeeng_testing.harnesses.eval_assertions import (
    run_plain,
    run_with_monkeypatch,
    run_with_monkeypatch_tmp_path,
    run_with_tmp_path,
)

import json
from pathlib import Path

import pytest

from outcomeeng_evals.runner import (
    ClaudeCliRunner,
    RunMetadata,
    RunResult,
    _metadata_from_envelope,
    _subprocess_env,
)
from outcomeeng_testing.evals.factories import load_claude_result_envelope
from outcomeeng_testing.evals.fakes import RecordingSubprocessRunner
from outcomeeng_testing.evals.fakes import StubModelRunner as StubRunner


def _impl_subprocess_env_strips_claudecode_marker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.setenv("PATH", "/usr/bin")
    env = _subprocess_env()
    assert "CLAUDECODE" not in env, "nested invocations must strip the CLAUDECODE guard"
    assert env["PATH"] == "/usr/bin", "other env entries are preserved"


def _impl_metadata_from_envelope_extracts_duration_and_cost() -> None:
    md = _metadata_from_envelope(
        dict(load_claude_result_envelope()), wall_clock_ms=9999.0
    )
    assert md.duration_ms == pytest.approx(2608.0)
    assert md.total_cost_usd == pytest.approx(0.2207325)


def _impl_metadata_from_envelope_extracts_usage_breakdown() -> None:
    md = _metadata_from_envelope(dict(load_claude_result_envelope()), wall_clock_ms=0.0)
    assert md.input_tokens == 5
    assert md.output_tokens == 6
    assert md.cache_read_input_tokens == 18240
    assert md.cache_creation_input_tokens == 33830
    assert md.num_turns == 1
    assert md.stop_reason == "end_turn"


def _impl_metadata_from_envelope_falls_back_to_wall_clock_when_duration_missing() -> (
    None
):
    envelope = dict(load_claude_result_envelope())
    envelope.pop("duration_ms")
    md = _metadata_from_envelope(envelope, wall_clock_ms=1234.5)
    assert md.duration_ms == pytest.approx(1234.5)


def _impl_metadata_from_envelope_returns_none_for_missing_fields() -> None:
    md = _metadata_from_envelope({"result": "x"}, wall_clock_ms=10.0)
    assert md.total_cost_usd is None
    assert md.input_tokens is None
    assert md.output_tokens is None
    assert md.stop_reason is None


def _impl_stub_runner_returns_run_result_with_supplied_metadata() -> None:
    expected = RunMetadata(duration_ms=42.0, total_cost_usd=0.01)
    runner = StubRunner(response="ok", metadata=expected)
    result = runner.run("any prompt")
    assert isinstance(result, RunResult)
    assert result.text == "ok"
    assert result.metadata == expected


def _impl_stub_runner_uses_responder_callable_when_supplied() -> None:
    runner = StubRunner(responder=lambda prompt: f"got: {prompt}")
    assert runner.run("ping").text == "got: ping"


def _impl_claude_cli_runner_returns_text_and_metadata_from_envelope(
    tmp_path: Path,
) -> None:
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(plugin_dir=tmp_path, run_command=command)
    result = runner.run("any prompt")
    assert result.text == "hi"
    assert result.metadata.duration_ms == pytest.approx(2608.0)
    assert result.metadata.total_cost_usd == pytest.approx(0.2207325)


def _impl_claude_cli_runner_passes_model_to_subprocess(tmp_path: Path) -> None:
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(
        plugin_dir=tmp_path, model="claude-sonnet-4-5", run_command=command
    )
    runner.run("any prompt")
    argv = command.calls[0].argv
    assert argv[argv.index("--model") + 1] == "claude-sonnet-4-5"


def _impl_claude_cli_runner_passes_env_without_claudecode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("CLAUDECODE", "1")
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(plugin_dir=tmp_path, run_command=command)
    runner.run("any prompt")
    assert "CLAUDECODE" not in command.calls[0].env, (
        "CLAUDECODE must be stripped before invocation"
    )


def _impl_claude_cli_runner_raises_with_diagnostic_on_nonzero_exit(
    tmp_path: Path,
) -> None:
    command = RecordingSubprocessRunner(stdout="", returncode=2)
    runner = ClaudeCliRunner(plugin_dir=tmp_path, run_command=command)
    with pytest.raises(RuntimeError, match="claude exited 2"):
        runner.run("any prompt")


def _impl_claude_cli_runner_derives_bare_when_anthropic_api_key_is_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The runner follows the operator-provisioned auth mode from the inherited
    # env. A non-empty ANTHROPIC_API_KEY selects the --bare path.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(plugin_dir=tmp_path, run_command=command)
    runner.run("any prompt")
    argv = command.calls[0].argv
    assert argv[0] == runner.binary
    assert "--bare" in argv, "ANTHROPIC_API_KEY in env must trigger the derived --bare"
    # The fixed flags remain present regardless of the derived --bare.
    assert "--print" in argv
    assert "--no-session-persistence" in argv
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--plugin-dir") + 1] == str(tmp_path)


def _impl_claude_cli_runner_omits_bare_when_only_oauth_token_is_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The runner follows the operator-provisioned auth mode from the inherited
    # env. An OAuth token without an API key selects the non-bare path.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-oauth-test")
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(plugin_dir=tmp_path, run_command=command)
    runner.run("any prompt")
    argv = command.calls[0].argv
    assert "--bare" not in argv, (
        "without ANTHROPIC_API_KEY the derive rule must omit --bare so the"
        " OAuth token path is selected"
    )
    assert command.calls[0].env["CLAUDE_CODE_OAUTH_TOKEN"] == "sk-oauth-test"


def _impl_claude_cli_runner_omits_bare_when_anthropic_api_key_is_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # GitHub forwards an empty string for an absent secret. The runner treats
    # that as no API-key mode and uses the non-bare mode already provisioned.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "sk-oauth-test")
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(plugin_dir=tmp_path, run_command=command)
    runner.run("any prompt")
    argv = command.calls[0].argv
    assert "--bare" not in argv, (
        "an empty ANTHROPIC_API_KEY must derive no --bare so the OAuth token"
        " path remains available"
    )


def _impl_claude_cli_runner_omits_bare_when_no_env_auth_is_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # With no auth environment variables present, the runner still omits
    # --bare. Agents do not propose switching auth modes from inside the run.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(plugin_dir=tmp_path, run_command=command)
    runner.run("any prompt")
    argv = command.calls[0].argv
    assert "--bare" not in argv, (
        "without env-form auth the default path must omit --bare and avoid"
        " switching the operator's auth mode"
    )


def _impl_claude_cli_runner_forces_bare_when_override_is_true(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The constructor override remains available for direct embedding and tests;
    # normal eval runs follow the inherited environment.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(plugin_dir=tmp_path, bare=True, run_command=command)
    runner.run("any prompt")
    argv = command.calls[0].argv
    assert "--bare" in argv, "bare=True must force --bare regardless of env"


def _impl_claude_cli_runner_forces_no_bare_when_override_is_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The constructor override remains available for direct embedding and tests;
    # normal eval runs follow the inherited environment.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    command = RecordingSubprocessRunner(
        stdout=json.dumps(load_claude_result_envelope())
    )
    runner = ClaudeCliRunner(plugin_dir=tmp_path, bare=False, run_command=command)
    runner.run("any prompt")
    argv = command.calls[0].argv
    assert "--bare" not in argv, (
        "bare=False must suppress --bare even when ANTHROPIC_API_KEY is set"
    )
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--plugin-dir") + 1] == str(tmp_path)


def assert_subprocess_env_strips_claudecode_marker() -> None:
    run_with_monkeypatch(_impl_subprocess_env_strips_claudecode_marker)


def assert_metadata_from_envelope_extracts_duration_and_cost() -> None:
    run_plain(_impl_metadata_from_envelope_extracts_duration_and_cost)


def assert_metadata_from_envelope_extracts_usage_breakdown() -> None:
    run_plain(_impl_metadata_from_envelope_extracts_usage_breakdown)


def assert_metadata_from_envelope_falls_back_to_wall_clock_when_duration_missing() -> (
    None
):
    run_plain(
        _impl_metadata_from_envelope_falls_back_to_wall_clock_when_duration_missing
    )


def assert_metadata_from_envelope_returns_none_for_missing_fields() -> None:
    run_plain(_impl_metadata_from_envelope_returns_none_for_missing_fields)


def assert_stub_runner_returns_run_result_with_supplied_metadata() -> None:
    run_plain(_impl_stub_runner_returns_run_result_with_supplied_metadata)


def assert_stub_runner_uses_responder_callable_when_supplied() -> None:
    run_plain(_impl_stub_runner_uses_responder_callable_when_supplied)


def assert_claude_cli_runner_returns_text_and_metadata_from_envelope() -> None:
    run_with_tmp_path(_impl_claude_cli_runner_returns_text_and_metadata_from_envelope)


def assert_claude_cli_runner_passes_model_to_subprocess() -> None:
    run_with_tmp_path(_impl_claude_cli_runner_passes_model_to_subprocess)


def assert_claude_cli_runner_passes_env_without_claudecode() -> None:
    run_with_monkeypatch_tmp_path(_impl_claude_cli_runner_passes_env_without_claudecode)


def assert_claude_cli_runner_raises_with_diagnostic_on_nonzero_exit() -> None:
    run_with_tmp_path(_impl_claude_cli_runner_raises_with_diagnostic_on_nonzero_exit)


def assert_claude_cli_runner_derives_bare_when_anthropic_api_key_is_set() -> None:
    run_with_monkeypatch_tmp_path(
        _impl_claude_cli_runner_derives_bare_when_anthropic_api_key_is_set
    )


def assert_claude_cli_runner_omits_bare_when_only_oauth_token_is_set() -> None:
    run_with_monkeypatch_tmp_path(
        _impl_claude_cli_runner_omits_bare_when_only_oauth_token_is_set
    )


def assert_claude_cli_runner_omits_bare_when_anthropic_api_key_is_empty() -> None:
    run_with_monkeypatch_tmp_path(
        _impl_claude_cli_runner_omits_bare_when_anthropic_api_key_is_empty
    )


def assert_claude_cli_runner_omits_bare_when_no_env_auth_is_set() -> None:
    run_with_monkeypatch_tmp_path(
        _impl_claude_cli_runner_omits_bare_when_no_env_auth_is_set
    )


def assert_claude_cli_runner_forces_bare_when_override_is_true() -> None:
    run_with_monkeypatch_tmp_path(
        _impl_claude_cli_runner_forces_bare_when_override_is_true
    )


def assert_claude_cli_runner_forces_no_bare_when_override_is_false() -> None:
    run_with_monkeypatch_tmp_path(
        _impl_claude_cli_runner_forces_no_bare_when_override_is_false
    )
