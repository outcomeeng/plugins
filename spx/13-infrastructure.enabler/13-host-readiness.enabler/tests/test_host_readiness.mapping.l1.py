"""Mapping evidence for host-readiness terminal statuses."""

import pytest

from outcomeeng_testing.harnesses.host_readiness import (
    load_host_readiness_module,
    terminal_result_for_status,
)

MODULE = load_host_readiness_module()

DECLARED_TERMINAL_CONTRACT = [
    ("ready", True, 0),
    ("error", False, 1),
    ("unsupported", False, 2),
    ("not_ready", False, 3),
    ("interrupted", False, 130),
]


@pytest.mark.parametrize(
    ("status_value", "declared_ready", "declared_exit_code"),
    DECLARED_TERMINAL_CONTRACT,
)
def test_each_terminal_status_carries_its_declared_readiness_and_exit_code(
    status_value: str, declared_ready: bool, declared_exit_code: int
) -> None:
    result = terminal_result_for_status(MODULE.Status(status_value))

    assert result.ready is declared_ready
    assert int(result.exit_code) == declared_exit_code


def test_the_declared_contract_covers_every_terminal_status() -> None:
    declared = {status_value for status_value, _, _ in DECLARED_TERMINAL_CONTRACT}

    assert {status.value for status in MODULE.Status} == declared
