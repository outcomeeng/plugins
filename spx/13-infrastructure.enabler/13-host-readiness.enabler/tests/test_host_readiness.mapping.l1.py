"""Mapping evidence for host-readiness terminal statuses."""

from outcomeeng_testing.harnesses.host_readiness import (
    exit_code_for_status,
    load_host_readiness_module,
    readiness_for_status,
    status_cases,
    terminal_result_for,
)


def test_every_terminal_status_maps_to_readiness_and_exit_code() -> None:
    module = load_host_readiness_module()
    statuses = status_cases()

    assert module.Status.NOT_READY in statuses
    for status in statuses:
        run = terminal_result_for(status)

        assert run.result.ready is readiness_for_status(status)
        assert run.result.exit_code is exit_code_for_status(status)
