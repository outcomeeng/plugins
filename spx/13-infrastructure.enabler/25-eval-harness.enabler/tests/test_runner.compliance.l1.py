"""Compliance wrappers for the eval model-runner boundary."""

from outcomeeng_testing.harnesses.eval_runner import (
    assert_claude_runner_auth_mapping_matches_fixture,
    assert_claude_runner_raises_diagnostic_on_nonzero_exit,
    assert_claude_runner_replays_captured_process_contract,
    assert_metadata_matches_captured_envelope,
    assert_metadata_preserves_absence,
    assert_stub_runner_replays_fixture_result,
    assert_subprocess_environment_strips_claudecode_marker,
)


def test_subprocess_environment_strips_claudecode_marker() -> None:
    assert_subprocess_environment_strips_claudecode_marker()


def test_metadata_matches_captured_envelope() -> None:
    assert_metadata_matches_captured_envelope()


def test_metadata_preserves_absence() -> None:
    assert_metadata_preserves_absence()


def test_stub_runner_replays_fixture_result() -> None:
    assert_stub_runner_replays_fixture_result()


def test_claude_runner_replays_captured_process_contract() -> None:
    assert_claude_runner_replays_captured_process_contract()


def test_claude_runner_raises_diagnostic_on_nonzero_exit() -> None:
    assert_claude_runner_raises_diagnostic_on_nonzero_exit()


def test_claude_runner_auth_mapping_matches_fixture() -> None:
    assert_claude_runner_auth_mapping_matches_fixture()
