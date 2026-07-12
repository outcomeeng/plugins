"""Binding-free compliance wrappers for the eval runner."""

from outcomeeng_testing.evals.assert_runner import (
    assert_subprocess_env_strips_claudecode_marker,
    assert_metadata_from_envelope_extracts_duration_and_cost,
    assert_metadata_from_envelope_extracts_usage_breakdown,
    assert_metadata_from_envelope_falls_back_to_wall_clock_when_duration_missing,
    assert_metadata_from_envelope_returns_none_for_missing_fields,
    assert_stub_runner_returns_run_result_with_supplied_metadata,
    assert_stub_runner_uses_responder_callable_when_supplied,
    assert_claude_cli_runner_returns_text_and_metadata_from_envelope,
    assert_claude_cli_runner_passes_model_to_subprocess,
    assert_claude_cli_runner_passes_env_without_claudecode,
    assert_claude_cli_runner_raises_with_diagnostic_on_nonzero_exit,
    assert_claude_cli_runner_derives_bare_when_anthropic_api_key_is_set,
    assert_claude_cli_runner_omits_bare_when_only_oauth_token_is_set,
    assert_claude_cli_runner_omits_bare_when_anthropic_api_key_is_empty,
    assert_claude_cli_runner_omits_bare_when_no_env_auth_is_set,
    assert_claude_cli_runner_forces_bare_when_override_is_true,
    assert_claude_cli_runner_forces_no_bare_when_override_is_false,
)


def test_subprocess_env_strips_claudecode_marker() -> None:
    assert_subprocess_env_strips_claudecode_marker()


def test_metadata_from_envelope_extracts_duration_and_cost() -> None:
    assert_metadata_from_envelope_extracts_duration_and_cost()


def test_metadata_from_envelope_extracts_usage_breakdown() -> None:
    assert_metadata_from_envelope_extracts_usage_breakdown()


def test_metadata_from_envelope_falls_back_to_wall_clock_when_duration_missing() -> (
    None
):
    assert_metadata_from_envelope_falls_back_to_wall_clock_when_duration_missing()


def test_metadata_from_envelope_returns_none_for_missing_fields() -> None:
    assert_metadata_from_envelope_returns_none_for_missing_fields()


def test_stub_runner_returns_run_result_with_supplied_metadata() -> None:
    assert_stub_runner_returns_run_result_with_supplied_metadata()


def test_stub_runner_uses_responder_callable_when_supplied() -> None:
    assert_stub_runner_uses_responder_callable_when_supplied()


def test_claude_cli_runner_returns_text_and_metadata_from_envelope() -> None:
    assert_claude_cli_runner_returns_text_and_metadata_from_envelope()


def test_claude_cli_runner_passes_model_to_subprocess() -> None:
    assert_claude_cli_runner_passes_model_to_subprocess()


def test_claude_cli_runner_passes_env_without_claudecode() -> None:
    assert_claude_cli_runner_passes_env_without_claudecode()


def test_claude_cli_runner_raises_with_diagnostic_on_nonzero_exit() -> None:
    assert_claude_cli_runner_raises_with_diagnostic_on_nonzero_exit()


def test_claude_cli_runner_derives_bare_when_anthropic_api_key_is_set() -> None:
    assert_claude_cli_runner_derives_bare_when_anthropic_api_key_is_set()


def test_claude_cli_runner_omits_bare_when_only_oauth_token_is_set() -> None:
    assert_claude_cli_runner_omits_bare_when_only_oauth_token_is_set()


def test_claude_cli_runner_omits_bare_when_anthropic_api_key_is_empty() -> None:
    assert_claude_cli_runner_omits_bare_when_anthropic_api_key_is_empty()


def test_claude_cli_runner_omits_bare_when_no_env_auth_is_set() -> None:
    assert_claude_cli_runner_omits_bare_when_no_env_auth_is_set()


def test_claude_cli_runner_forces_bare_when_override_is_true() -> None:
    assert_claude_cli_runner_forces_bare_when_override_is_true()


def test_claude_cli_runner_forces_no_bare_when_override_is_false() -> None:
    assert_claude_cli_runner_forces_no_bare_when_override_is_false()
