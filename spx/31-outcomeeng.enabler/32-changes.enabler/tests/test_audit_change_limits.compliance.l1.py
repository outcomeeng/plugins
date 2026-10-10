"""Compliance evidence: count-limits reports each measured quantity over its limit.

The rule is the spec assertion for the ``audit-change`` runner's ``count-limits``
operation: it counts the title's words, each Intent part's sentences, the
``## Decisions`` rows, and each answer's sentences, and reports a quantity over its
limit as a violation naming the section, the limit, and the count. Each violating
case is a record built with exactly one more than the limit the runner declares for
one quantity; the conforming case at the limit shows the same record reports none.
Counts are fixed by the record's construction, so the oracle is independent of the
runner's counting code.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.audit_change_limits import (
    Measure,
    limit_of,
    measure_record,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
ExitCode = runner.ExitCode


@pytest.mark.parametrize("measure", list(Measure))
def test_a_quantity_over_its_limit_is_reported_as_one_violation_naming_section_limit_and_count(
    measure: Measure,
) -> None:
    limit = limit_of(measure)

    observed = measure_record(measure, limit + 1)

    result = observed.call.result
    violations = result[Result.VIOLATIONS]
    assert observed.call.exit_code == ExitCode.OK
    assert result[Result.STATUS] == Status.OK
    assert len(violations) == 1
    assert measure.value in violations[0][Result.SECTION]
    assert violations[0][Result.LIMIT] == limit
    assert violations[0][Result.COUNT] == limit + 1
    assert violations[0] in result[Result.LIMITS]


@pytest.mark.parametrize("measure", list(Measure))
def test_a_quantity_at_its_limit_is_measured_and_reported_as_no_violation(
    measure: Measure,
) -> None:
    limit = limit_of(measure)

    observed = measure_record(measure, limit)

    result = observed.call.result
    measured = [
        entry
        for entry in result[Result.LIMITS]
        if measure.value in entry[Result.SECTION] and entry[Result.LIMIT] == limit
    ]
    assert observed.call.exit_code == ExitCode.OK
    assert result[Result.VIOLATIONS] == []
    assert [entry[Result.COUNT] for entry in measured] == [limit]
