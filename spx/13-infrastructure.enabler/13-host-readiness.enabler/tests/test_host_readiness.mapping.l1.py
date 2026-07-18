"""Mapping evidence for host-readiness terminal statuses."""

from outcomeeng_testing.harnesses.host_readiness import terminal_status_mapping_holds


def test_every_terminal_status_maps_to_readiness_and_exit_code() -> None:
    assert terminal_status_mapping_holds()
