"""Mapping evidence: read-relations maps each Parent form to the issue number it names.

The rule is the spec assertion for the ``audit-change`` runner's
``read-relations`` operation: a ``Parent`` number field value, integer or
float, maps to the issue number it names, and an absent value maps to
``null``. The finite domain is the three forms the assertion names, one
replayed store scenario per form; each scenario states the Parent it carries,
and the mapped result is compared with that stated value, so no expected
number is chosen here and no call reaches the network.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.audit_change_relations import (
    declared,
    parent_fixtures,
    read_relations,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
ExitCode = runner.ExitCode


@pytest.mark.parametrize("fixture", parent_fixtures(), ids=lambda path: path.stem)
def test_a_parent_value_maps_to_the_issue_number_it_names_and_an_absent_value_to_null(
    fixture: Path,
) -> None:
    named = declared(fixture)

    observed = read_relations(fixture)

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.PARENT] == named
    if named is not None:
        assert isinstance(observed.result[Result.PARENT], int)
