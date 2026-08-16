"""Compliance evidence for the ``Finding.rule`` citation boundary.

Covers this clause in ``../reviewing-changes.md``: ``Finding.rule`` is never a
free-form description, a required-action string, a repository-root review
policy citation, or a tracking-location string, and every citation resolves to
an existing rule at the referenced location. Each violating case follows one
class the rule names; the parser rejecting it, naming the offending value, is
the enforcement under test.
"""

from __future__ import annotations

import json

import pytest

from outcomeeng_testing.generators.reviewing_changes import (
    RejectedRuleCitationCase,
    rejected_rule_citation_cases,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    load_review_result_module,
    make_finding_dict,
    make_review_result_dict,
)

review_result = load_review_result_module()


@pytest.mark.parametrize(
    "case", list(rejected_rule_citation_cases()), ids=lambda c: c.violation_class
)
def test_parser_rejects_each_violating_citation_class(
    case: RejectedRuleCitationCase,
) -> None:
    payload = json.dumps(
        make_review_result_dict(findings=[make_finding_dict(rule=case.rule)])
    )

    with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
        review_result.parse_json(payload)

    assert "rule" in str(excinfo.value)
