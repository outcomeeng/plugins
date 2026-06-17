"""Property tests for the ``review_result`` policy module.

Covers this clause in ``../review-changes.md``:

Properties
- For every ``ReviewResult`` instance, ``from_json_dict(to_json_dict(r)) == r``
  — serialization is lossless across the generated input space.

Uses Hypothesis to generate variable ``ReviewResult``-shaped dicts and
exercises the parse/emit round-trip. The reviewer emits findings only —
there is no ``decision`` field and no consistency invariant — so any
generated document with conforming findings parses and round-trips.
"""

from __future__ import annotations

import json
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng_testing.harnesses.reviewing_changes import (
    load_review_result_module,
)


def _concern_values() -> list[str]:
    review_result = load_review_result_module()
    return sorted(member.value for member in review_result.Concern)


def _severity_values() -> list[str]:
    review_result = load_review_result_module()
    return sorted(member.value for member in review_result.Severity)


def _finding_strategy() -> st.SearchStrategy[dict[str, Any]]:
    """Generate finding-shaped dicts spanning the full severity space."""
    return st.builds(
        lambda fid, concern, severity, file, line, rule, message, action: {
            "id": fid,
            "concern": concern,
            "severity": severity,
            "file": file,
            "line": line,
            "rule": rule,
            "message": message,
            "action": action,
        },
        fid=st.from_regex(r"F-[0-9]{3}", fullmatch=True),
        concern=st.sampled_from(_concern_values()),
        severity=st.sampled_from(_severity_values()),
        file=st.from_regex(r"[a-z_]{1,12}\.py", fullmatch=True),
        line=st.integers(min_value=1, max_value=10_000),
        # Rule citation form: a path-style string starting with one of the
        # accepted prefixes (see review_result._RULE_CITATION_PREFIXES).
        rule=st.from_regex(
            r"spx/[a-z]{1,8}\.md:(ALWAYS|NEVER|MUST):[1-9][0-9]?",
            fullmatch=True,
        ),
        message=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
            min_size=0,
            max_size=64,
        ),
        action=st.text(
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
            min_size=0,
            max_size=64,
        ),
    )


def _conforming_review_result_dicts() -> st.SearchStrategy[dict[str, Any]]:
    """Generate conforming review-result dicts — findings only, no decision."""
    review_result = load_review_result_module()
    return st.builds(
        lambda findings, acks, summary: {
            "schema_version": review_result.SCHEMA_VERSION,
            "summary": summary,
            "findings": findings,
            "acknowledgements": acks,
        },
        findings=st.lists(_finding_strategy(), max_size=4),
        acks=st.lists(st.text(min_size=0, max_size=32), max_size=3),
        summary=st.text(min_size=0, max_size=64),
    )


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
