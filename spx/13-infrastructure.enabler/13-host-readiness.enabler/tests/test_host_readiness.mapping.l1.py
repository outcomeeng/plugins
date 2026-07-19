"""Mapping evidence for host-readiness terminal statuses."""

from outcomeeng_testing.harnesses.host_readiness import load_host_readiness_module


def test_every_terminal_status_carries_a_readiness_and_an_exit_code() -> None:
    module = load_host_readiness_module()
    statuses = set(module.Status)

    assert set(module.STATUS_READINESS) == statuses
    assert set(module.STATUS_EXIT_CODES) == statuses
    assert {s for s in statuses if module.STATUS_READINESS[s]} == {module.Status.READY}
