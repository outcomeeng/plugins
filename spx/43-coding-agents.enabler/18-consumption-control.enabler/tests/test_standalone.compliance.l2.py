"""Copied stdlib-only workers operate without server, checkout or optional tools."""

from outcomeeng_testing.harnesses.consumption_control import (
    standalone_observation,
    workspace,
)


def test_copied_worker_preserves_accounting_without_optional_investigation() -> None:
    with workspace() as work:
        observed = standalone_observation(work)
        assert observed.exitcode == observed.expected_exitcode
        assert not observed.model_invocations
        assert observed.artifact.is_file()
        assert observed.source_before == observed.source_after
        assert observed.optional_status == observed.expected_optional_status
        assert observed.request_count == observed.expected_requests
