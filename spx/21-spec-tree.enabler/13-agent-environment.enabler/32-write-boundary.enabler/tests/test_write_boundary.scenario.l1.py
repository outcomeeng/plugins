"""Scenario evidence: the shipped pre-write hook command denies an ungranted destination and allows a granted one.

Each case is a whole hook-payload fixture under
``outcomeeng_testing/fixtures/write_boundary/``; the write-boundary harness runs the
shipped ``dist/claude`` pre-write command on it through ``/bin/sh``, once per tool the
hook covers. The denial's field names and value are the adapter's own output
vocabulary, loaded from the adapter by the harness; the covered tools and the empty
result come from ``outcomeeng.validation.hook_contract``. The destination and the
granted roots a denial must name come from the case's own fixture files. This file
chooses no case, value, or setup policy.
"""

from __future__ import annotations

import json

import pytest

from outcomeeng.validation.hook_contract import (
    PRE_TOOL_USE_EVENT,
    PRE_WRITE_EMPTY_RESULT,
    PRE_WRITE_TOOLS,
)
from outcomeeng_testing.harnesses.write_boundary import (
    FixtureCase,
    FixtureGroup,
    case_id,
    fixture_cases,
    load_adapter,
    run_pre_write_hook,
)

adapter = load_adapter()


@pytest.mark.parametrize("tool", sorted(PRE_WRITE_TOOLS))
@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.DENY), ids=case_id)
def test_ungranted_destination_is_denied_with_its_destination_and_the_granted_roots(
    case: FixtureCase, tool: str
) -> None:
    observation = run_pre_write_hook(case, tool)

    assert observation.payload_text is not None
    destination = json.loads(observation.payload_text)[adapter.TOOL_INPUT_FIELD][
        adapter.FILE_PATH_FIELD
    ]
    output = json.loads(observation.stdout)[adapter.HOOK_SPECIFIC_OUTPUT_FIELD]
    reason = output[adapter.PERMISSION_DECISION_REASON_FIELD]

    assert observation.exit_code == 0, observation.stderr
    assert output[adapter.HOOK_EVENT_NAME_FIELD] == PRE_TOOL_USE_EVENT
    assert output[adapter.PERMISSION_DECISION_FIELD] == adapter.DENY_DECISION
    assert destination in reason
    assert observation.granted_roots
    for root in observation.granted_roots:
        assert root in reason


@pytest.mark.parametrize("tool", sorted(PRE_WRITE_TOOLS))
@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.GRANT), ids=case_id)
def test_granted_destination_is_allowed_with_the_empty_result(
    case: FixtureCase, tool: str
) -> None:
    observation = run_pre_write_hook(case, tool)

    assert observation.exit_code == 0, observation.stderr
    assert observation.stdout.strip() == PRE_WRITE_EMPTY_RESULT


@pytest.mark.parametrize("tool", sorted(PRE_WRITE_TOOLS))
@pytest.mark.parametrize("case", fixture_cases(FixtureGroup.KILL_SWITCH), ids=case_id)
def test_kill_switch_allows_an_ungranted_destination_with_the_empty_result(
    case: FixtureCase, tool: str
) -> None:
    observation = run_pre_write_hook(case, tool)

    assert observation.exit_code == 0, observation.stderr
    assert observation.stdout.strip() == PRE_WRITE_EMPTY_RESULT
