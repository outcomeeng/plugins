"""Mapping evidence for host-readiness terminal statuses."""

import json

import pytest

from outcomeeng_testing.harnesses.host_readiness import (
    load_host_readiness_module,
    run_cli_for_status,
)

MODULE = load_host_readiness_module()


def test_every_terminal_status_carries_a_readiness_and_an_exit_code() -> None:
    statuses = set(MODULE.Status)

    assert set(MODULE.STATUS_READINESS) == statuses
    assert set(MODULE.STATUS_EXIT_CODES) == statuses
    assert {s for s in statuses if MODULE.STATUS_READINESS[s]} == {MODULE.Status.READY}


@pytest.mark.parametrize("status", list(MODULE.Status))
def test_every_terminal_status_writes_its_document_to_stderr(status: object) -> None:
    run = run_cli_for_status(status)

    assert run.stdout == ""
    assert len(run.stderr.splitlines()) == 1
    assert json.loads(run.stderr)[MODULE.ResultField.STATUS] == status
    assert run.exit_code == MODULE.STATUS_EXIT_CODES[status]
