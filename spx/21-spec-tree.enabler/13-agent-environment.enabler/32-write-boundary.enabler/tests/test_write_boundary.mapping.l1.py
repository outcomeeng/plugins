"""Mapping evidence: every failure the spec names allows the call with the empty result.

Each failure is a whole fixture under ``outcomeeng_testing/fixtures/write_boundary/``
whose payload names a destination outside every granted root, so a denial would be
the outcome absent the failure: an absent, unreadable, malformed, or non-object
payload; a payload missing its session identity or transcript path; an unset project
directory; an unreadable and a malformed settings file; a missing adapter script; an
absent interpreter; and a destination whose resolution raises. The write-boundary
harness runs the shipped ``dist/claude`` pre-write command on each, once per tool the
hook covers; the covered tools and the empty result come from
``outcomeeng.validation.hook_contract``. The timeout failure has no case here: the
host enforces it. This file chooses no case, value, or setup policy.
"""

from __future__ import annotations

import pytest

from outcomeeng.validation.hook_contract import PRE_WRITE_EMPTY_RESULT, PRE_WRITE_TOOLS
from outcomeeng_testing.harnesses.write_boundary import (
    FixtureCase,
    FixtureGroup,
    case_id,
    fixture_cases,
    run_pre_write_hook,
)


@pytest.mark.parametrize("tool", sorted(PRE_WRITE_TOOLS))
@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.FAILURE), ids=case_id)
def test_failure_allows_the_call_with_the_empty_result(
    case: FixtureCase, tool: str
) -> None:
    observation = run_pre_write_hook(case, tool)

    assert observation.exit_code == 0, observation.stderr
    assert observation.stdout.strip() == PRE_WRITE_EMPTY_RESULT
