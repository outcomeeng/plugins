"""Mapping evidence: resolve-reference maps a named path to its default-branch resolution.

The rule is the spec assertion for the ``audit-change`` runner's
``resolve-reference`` operation: ``defaultBranch`` is ``on-default-branch`` when
origin's default branch holds the named path as a file, ``checkout-only`` when it
does not and the path resolves to an existing path in the checkout, and
``absent`` for every other path, a directory only origin holds, an absolute path
and a path outside the repository among them. The finite domain is the
``PathCondition`` set the harness builds as real Git repositories with a real
bare origin. Each situation states what its
construction made true about the spelling, and the expected resolution derives
from those two stated facts under the assertion's rule, so no expected value is
copied from the runner's branch logic.
"""

from __future__ import annotations

import pytest

from outcomeeng_testing.harnesses.audit_change_default_branch import (
    PathCondition,
    default_branch_situation,
    resolve_reference,
)
from outcomeeng_testing.harnesses.audit_change_run import load_runner

runner = load_runner()
Result = runner.ResultField
Status = runner.ResultStatus
ExitCode = runner.ExitCode
Resolution = runner.DefaultBranchResolution


@pytest.mark.parametrize("condition", list(PathCondition), ids=lambda c: c.value)
def test_a_named_path_maps_to_the_resolution_its_origin_and_checkout_state_states(
    condition: PathCondition,
) -> None:
    with default_branch_situation(condition) as situation:
        observed = resolve_reference(situation)

    if situation.names_file_on_origin_default:
        expected = Resolution.ON_DEFAULT_BRANCH
    elif situation.names_existing_path_in_checkout:
        expected = Resolution.CHECKOUT_ONLY
    else:
        expected = Resolution.ABSENT

    assert observed.exit_code == ExitCode.OK
    assert observed.result[Result.STATUS] == Status.OK
    assert observed.result[Result.PATH] == situation.named
    assert observed.result[Result.DEFAULT_BRANCH] == expected


def test_every_resolution_the_runner_defines_is_the_result_of_some_condition() -> None:
    produced = set()
    for condition in PathCondition:
        with default_branch_situation(condition) as situation:
            observed = resolve_reference(situation)
        produced.add(observed.result[Result.DEFAULT_BRANCH])

    assert produced == set(Resolution)
