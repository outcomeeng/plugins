"""Property tests for the ``review_result`` policy module.

Covers these clauses in ``../reviewing-changes.md``:

Properties
- For every ``ReviewResult`` instance, ``from_json_dict(to_json_dict(r)) == r``
  — serialization is lossless across the generated input space.
- For every finding with ``severity == "must_fix"`` combined with
  ``decision == "approve"``, ``parse_json`` raises
  ``ReviewResultValidationError`` — the consistency invariant holds
  across the full input space, not just sampled examples.

The first property uses Hypothesis to generate variable
``ReviewResult``-shaped dicts and exercises the parse/emit round-trip.
The second property uses ``itertools.product`` to exhaust the finite
``Decision × Severity`` cross-product so the consistency invariant is
verified universally rather than against examples.
"""

from __future__ import annotations

import itertools
import json
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.reviewing_changes import (
    load_review_result_module,
    make_review_result_dict,
)


def _concern_values() -> list[str]:
    review_result = load_review_result_module()
    return sorted(member.value for member in review_result.Concern)


def _severity_values_excluding_must_fix() -> list[str]:
    """Severity wire values valid for *all* decisions.

    Used by the round-trip property strategy: must_fix is excluded so
    Hypothesis cannot generate a document that violates the consistency
    invariant (which would short-circuit ``parse_json`` and defeat the
    round-trip property).
    """
    review_result = load_review_result_module()
    return sorted(
        member.value for member in review_result.Severity if member.value != "must_fix"
    )


def _decisions_excluding_approve() -> list[str]:
    review_result = load_review_result_module()
    return sorted(
        member.value for member in review_result.Decision if member.value != "approve"
    )


def _finding_strategy(
    severities: list[str],
) -> st.SearchStrategy[dict[str, Any]]:
    """Generate finding-shaped dicts with the given allowed severities."""
    return st.builds(
        lambda fid, concern, severity, file, line, rule, message: {
            "id": fid,
            "concern": concern,
            "severity": severity,
            "file": file,
            "line": line,
            "rule": rule,
            "message": message,
        },
        fid=st.from_regex(r"F-[0-9]{3}", fullmatch=True),
        concern=st.sampled_from(_concern_values()),
        severity=st.sampled_from(severities),
        file=st.from_regex(r"[a-z_]{1,12}\.py", fullmatch=True),
        line=st.integers(min_value=1, max_value=10_000),
        rule=st.from_regex(r"[a-z_]{1,16}", fullmatch=True),
        message=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
            min_size=0,
            max_size=64,
        ),
    )


def _conforming_review_result_dicts() -> st.SearchStrategy[dict[str, Any]]:
    """Generate review-result dicts that satisfy the consistency invariant.

    The strategy alternates two shapes:

    1. ``decision`` is one of ``request_changes`` / ``comment``, findings
       may carry any severity including ``must_fix``.
    2. ``decision`` is ``approve``, findings carry only non-``must_fix``
       severities.

    Both shapes are conforming, so ``parse_json`` accepts each generated
    document and the round-trip property exercises the full enum space.
    """
    review_result = load_review_result_module()
    all_severities = sorted(member.value for member in review_result.Severity)

    request_or_comment = st.builds(
        lambda decision, findings, acks, summary: {
            "schema_version": review_result.SCHEMA_VERSION,
            "decision": decision,
            "summary": summary,
            "findings": findings,
            "acknowledgements": acks,
        },
        decision=st.sampled_from(_decisions_excluding_approve()),
        findings=st.lists(_finding_strategy(all_severities), max_size=4),
        acks=st.lists(st.text(min_size=0, max_size=32), max_size=3),
        summary=st.text(min_size=0, max_size=64),
    )

    approve_without_must_fix = st.builds(
        lambda findings, acks, summary: {
            "schema_version": review_result.SCHEMA_VERSION,
            "decision": "approve",
            "summary": summary,
            "findings": findings,
            "acknowledgements": acks,
        },
        findings=st.lists(
            _finding_strategy(_severity_values_excluding_must_fix()), max_size=4
        ),
        acks=st.lists(st.text(min_size=0, max_size=32), max_size=3),
        summary=st.text(min_size=0, max_size=64),
    )

    return st.one_of(request_or_comment, approve_without_must_fix)


class TestRoundTripProperty:
    """``from_json_dict(to_json_dict(r)) == r`` for every parseable
    ``ReviewResult`` value."""

    @given(document=_conforming_review_result_dicts())
    @settings(max_examples=100, deadline=None)
    def test_round_trip_preserves_equality(self, document: dict[str, Any]) -> None:
        review_result = load_review_result_module()
        result = review_result.parse_json(json.dumps(document))
        round_tripped = review_result.from_json_dict(review_result.to_json_dict(result))
        assert round_tripped == result


class TestConsistencyInvariantUniversal:
    """For every ``(decision, severity)`` combination, ``parse_json``
    raises iff ``decision == "approve"`` AND any finding has
    ``severity == "must_fix"``.

    The cross-product over the two enums is finite (3 × 3 = 9), so the
    property is verified by exhaustion rather than by sampling. The
    finding count is varied across {1, 2} so the validator's
    quantification over the findings list is exercised.
    """

    def test_invariant_holds_across_full_decision_severity_cross_product(
        self,
    ) -> None:
        review_result = load_review_result_module()
        decisions = sorted(member.value for member in review_result.Decision)
        severities = sorted(member.value for member in review_result.Severity)

        for decision, severity, finding_count in itertools.product(
            decisions, severities, (1, 2)
        ):
            findings = [
                {
                    "id": f"F-{idx:03d}",
                    "concern": "quality",
                    "severity": severity,
                    "file": "x.py",
                    "line": idx + 1,
                    "rule": "r",
                    "message": "m",
                }
                for idx in range(finding_count)
            ]
            document = make_review_result_dict(decision=decision, findings=findings)
            payload = json.dumps(document)
            inconsistent = decision == "approve" and severity == "must_fix"
            if inconsistent:
                with pytest.raises(review_result.ReviewResultValidationError):
                    review_result.parse_json(payload)
            else:
                # Must parse without error — the invariant does not apply
                # to this (decision, severity) combination.
                review_result.parse_json(payload)
