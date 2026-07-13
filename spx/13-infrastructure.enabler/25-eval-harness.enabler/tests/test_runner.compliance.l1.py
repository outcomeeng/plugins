"""Compliance evidence for the eval runner subprocess and envelope contract."""

import pytest

from outcomeeng_evals.runner import (
    CLAUDE_OUTPUT_FORMAT,
    ClaudeCliArgument,
    ClaudeEnvironmentVariable,
)
from outcomeeng_testing.harnesses.eval_runner import (
    observe_default_runner,
    observe_metadata_with_optional_fields_absent,
    observe_metadata_without_duration,
    observe_runner_with_api_key,
    observe_runner_with_bare_override,
    observe_runner_with_empty_api_key,
    observe_runner_with_nesting_marker,
    observe_runner_with_non_bare_override,
    observe_runner_with_oauth_token,
)


def test_runner_reads_text_duration_and_cost_from_the_envelope() -> None:
    observation = observe_default_runner()

    assert observation.result.text == observation.fixture_result
    assert observation.result.metadata.duration_ms == pytest.approx(
        observation.fixture_duration_ms
    )
    assert observation.result.metadata.total_cost_usd == pytest.approx(
        observation.fixture_total_cost_usd
    )


def test_runner_reads_usage_metadata_from_the_envelope() -> None:
    observation = observe_default_runner()

    assert observation.result.metadata.input_tokens == observation.fixture_input_tokens
    assert (
        observation.result.metadata.output_tokens == observation.fixture_output_tokens
    )
    assert (
        observation.result.metadata.cache_read_input_tokens
        == observation.fixture_cache_read_input_tokens
    )
    assert (
        observation.result.metadata.cache_creation_input_tokens
        == observation.fixture_cache_creation_input_tokens
    )
    assert observation.result.metadata.num_turns == observation.fixture_num_turns
    assert observation.result.metadata.stop_reason == observation.fixture_stop_reason


def test_runner_invokes_the_configured_print_mode_contract() -> None:
    observation = observe_default_runner()

    assert observation.call.argv[0] == observation.runner.binary
    assert ClaudeCliArgument.PRINT in observation.call.argv
    assert ClaudeCliArgument.NO_SESSION_PERSISTENCE in observation.call.argv
    assert (
        observation.call.argv[
            observation.call.argv.index(ClaudeCliArgument.OUTPUT_FORMAT) + 1
        ]
        == CLAUDE_OUTPUT_FORMAT
    )
    assert (
        observation.call.argv[observation.call.argv.index(ClaudeCliArgument.MODEL) + 1]
        == observation.runner.model
    )
    assert observation.call.argv[
        observation.call.argv.index(ClaudeCliArgument.PLUGIN_DIR) + 1
    ] == str(observation.runner.plugin_dir)


def test_runner_strips_the_nesting_marker_and_preserves_inherited_auth() -> None:
    observation = observe_runner_with_nesting_marker()

    assert ClaudeEnvironmentVariable.NESTING_MARKER not in observation.call.env
    assert (
        observation.call.env[ClaudeEnvironmentVariable.CLAUDE_CODE_OAUTH_TOKEN]
        == observation.provisioned_oauth_token
    )


def test_runner_derives_bare_mode_from_a_nonempty_api_key() -> None:
    observation = observe_runner_with_api_key()

    assert ClaudeCliArgument.BARE in observation.call.argv


def test_runner_omits_bare_mode_for_oauth_auth() -> None:
    observation = observe_runner_with_oauth_token()

    assert ClaudeCliArgument.BARE not in observation.call.argv
    assert (
        observation.call.env[ClaudeEnvironmentVariable.CLAUDE_CODE_OAUTH_TOKEN]
        == observation.provisioned_oauth_token
    )


def test_runner_treats_an_empty_api_key_as_non_bare_auth() -> None:
    observation = observe_runner_with_empty_api_key()

    assert ClaudeCliArgument.BARE not in observation.call.argv


def test_runner_constructor_can_force_bare_mode() -> None:
    observation = observe_runner_with_bare_override()

    assert ClaudeCliArgument.BARE in observation.call.argv


def test_runner_constructor_can_force_non_bare_mode() -> None:
    observation = observe_runner_with_non_bare_override()

    assert ClaudeCliArgument.BARE not in observation.call.argv


def test_metadata_duration_falls_back_to_observed_wall_clock_time() -> None:
    observation = observe_metadata_without_duration()

    assert observation.metadata.duration_ms == observation.wall_clock_ms


def test_missing_optional_metadata_remains_absent() -> None:
    observation = observe_metadata_with_optional_fields_absent()

    assert observation.metadata.total_cost_usd is None
    assert observation.metadata.input_tokens is None
    assert observation.metadata.output_tokens is None
    assert observation.metadata.stop_reason is None
