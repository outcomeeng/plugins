"""Mapping evidence for host-readiness terminal statuses."""

import pytest

from outcomeeng_testing.harnesses.host_readiness import (
    DECLARED_EXIT_CODES,
    load_host_readiness_module,
)


@pytest.mark.parametrize(("status_value", "declared_exit_code"), DECLARED_EXIT_CODES)
def test_each_terminal_status_maps_to_its_declared_exit_code(
    status_value: str, declared_exit_code: int
) -> None:
    module = load_host_readiness_module()

    assert (
        int(module.STATUS_EXIT_CODES[module.Status(status_value)]) == declared_exit_code
    )


def test_every_terminal_status_carries_a_readiness_and_an_exit_code() -> None:
    module = load_host_readiness_module()
    statuses = set(module.Status)

    assert set(module.STATUS_READINESS) == statuses
    assert set(module.STATUS_EXIT_CODES) == statuses
    assert {s for s in statuses if module.STATUS_READINESS[s]} == {module.Status.READY}
