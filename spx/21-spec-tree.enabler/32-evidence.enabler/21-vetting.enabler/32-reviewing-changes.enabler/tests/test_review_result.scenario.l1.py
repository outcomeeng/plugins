"""Scenario and mapping tests for the ``review_result`` policy module.

Covers these clauses in ``../reviewing-changes.md``:

Scenarios
- ``review_result.parse_json`` returns a ``ReviewResult`` dataclass on a
  conforming document and raises ``ReviewResultValidationError`` on
  every violation surfaced by the arbiter.
- ``review_result.to_json_dict`` and ``review_result.from_json_dict``
  round-trip a ``ReviewResult`` instance without loss.

Mappings
- ``Decision`` enum members map to the wire values ``approve``,
  ``request_changes``, ``comment``.
- ``Severity`` enum members map to the wire values ``must_fix``,
  ``suggestion``, ``nit``.
- ``Concern`` enum members map to exactly the eight wire values
  ``quality``, ``bugs``, ``performance``, ``security``,
  ``test_coverage``, ``architecture``, ``docs``, ``consistency``.

Compliance (subset)
- The policy module declares ``SCHEMA_VERSION``, frozen ``Finding`` and
  ``ReviewResult`` dataclasses, the ``Decision`` / ``Severity`` /
  ``Concern`` enums.

Consistency-invariant exhaustion lives in the property file.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from outcomeeng_testing.harnesses.reviewing_changes import (
    FIXTURE_RULE_CITATION,
    load_render_review_module,
    load_review_result_module,
    make_review_result_dict,
)


class TestModuleSurface:
    """The policy module declares the canonical schema surface."""

    def test_schema_version_is_a_positive_integer(self) -> None:
        review_result = load_review_result_module()
        assert isinstance(review_result.SCHEMA_VERSION, int)
        assert review_result.SCHEMA_VERSION >= 1

    def test_decision_severity_concern_enums_exist(self) -> None:
        review_result = load_review_result_module()
        assert hasattr(review_result, "Decision")
        assert hasattr(review_result, "Severity")
        assert hasattr(review_result, "Concern")

    def test_finding_and_review_result_are_frozen_dataclasses(self) -> None:
        review_result = load_review_result_module()
        for cls in (review_result.Finding, review_result.ReviewResult):
            assert dataclasses.is_dataclass(cls)
            # ``params`` is set by ``@dataclass(frozen=True)``; without
            # ``frozen=True`` the attribute is missing or ``frozen=False``.
            params = getattr(cls, "__dataclass_params__", None)
            assert params is not None
            assert getattr(params, "frozen", False) is True

    def test_validation_error_subclass_of_exception(self) -> None:
        review_result = load_review_result_module()
        assert issubclass(review_result.ReviewResultValidationError, Exception)


class TestDecisionMapping:
    """``Decision`` members map to the wire values ``approve``,
    ``request_changes``, ``comment``."""

    def test_decision_members_map_to_wire_values(self) -> None:
        review_result = load_review_result_module()
        wire_values = {member.value for member in review_result.Decision}
        assert wire_values == {"approve", "request_changes", "comment"}


class TestSeverityMapping:
    """``Severity`` members map to the wire values ``must_fix``,
    ``suggestion``, ``nit``."""

    def test_severity_members_map_to_wire_values(self) -> None:
        review_result = load_review_result_module()
        wire_values = {member.value for member in review_result.Severity}
        assert wire_values == {"must_fix", "suggestion", "nit"}


class TestConcernMapping:
    """``Concern`` members map to exactly the eight wire values
    declared in the spec."""

    def test_concern_members_map_to_eight_wire_values(self) -> None:
        review_result = load_review_result_module()
        wire_values = {member.value for member in review_result.Concern}
        assert wire_values == {
            "quality",
            "bugs",
            "performance",
            "security",
            "test_coverage",
            "architecture",
            "docs",
            "consistency",
        }


class TestParseJsonConforming:
    """``parse_json`` returns a ``ReviewResult`` on a conforming document."""

    def test_parse_json_returns_review_result_on_conforming_document(self) -> None:
        review_result = load_review_result_module()
        payload = json.dumps(make_review_result_dict())
        result = review_result.parse_json(payload)
        assert isinstance(result, review_result.ReviewResult)
        assert result.decision == review_result.Decision("request_changes")

    def test_parse_json_accepts_approve_with_no_must_fix(self) -> None:
        review_result = load_review_result_module()
        # Approve with a suggestion-only finding is the canonical
        # "approve with minor notes" shape.
        payload = json.dumps(make_review_result_dict(decision="approve"))
        result = review_result.parse_json(payload)
        assert result.decision == review_result.Decision("approve")

    def test_parse_json_accepts_comment_with_no_findings(self) -> None:
        review_result = load_review_result_module()
        payload = json.dumps(make_review_result_dict(decision="comment", findings=[]))
        result = review_result.parse_json(payload)
        assert result.decision == review_result.Decision("comment")
        assert result.findings == ()


class TestParseJsonRejection:
    """``parse_json`` raises ``ReviewResultValidationError`` on every
    schema violation surfaced by the arbiter."""

    def test_missing_required_key_raises(self) -> None:
        review_result = load_review_result_module()
        document = make_review_result_dict()
        del document["decision"]
        payload = json.dumps(document)
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        assert "decision" in str(excinfo.value)

    def test_unknown_decision_raises_with_value_and_allowed_set(self) -> None:
        review_result = load_review_result_module()
        payload = json.dumps(make_review_result_dict(decision="bogus-decision"))
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        message = str(excinfo.value)
        assert "bogus-decision" in message
        assert "approve" in message  # part of the allowed set

    def test_unknown_severity_raises_with_value_and_allowed_set(self) -> None:
        review_result = load_review_result_module()
        bad_finding = {
            "id": "F-001",
            "concern": "quality",
            "severity": "blocker",  # not a Severity member
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "m",
        }
        payload = json.dumps(make_review_result_dict(findings=[bad_finding]))
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        message = str(excinfo.value)
        assert "blocker" in message
        assert "must_fix" in message  # part of the allowed set

    def test_unknown_concern_raises_with_value_and_allowed_set(self) -> None:
        review_result = load_review_result_module()
        bad_finding = {
            "id": "F-001",
            "concern": "marketing",  # not a Concern member
            "severity": "suggestion",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "m",
        }
        payload = json.dumps(make_review_result_dict(findings=[bad_finding]))
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        message = str(excinfo.value)
        assert "marketing" in message
        assert "quality" in message  # part of the allowed set

    def test_approve_with_must_fix_raises_consistency_invariant(self) -> None:
        review_result = load_review_result_module()
        offending_finding = {
            "id": "F-001",
            "concern": "bugs",
            "severity": "must_fix",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "m",
        }
        payload = json.dumps(
            make_review_result_dict(decision="approve", findings=[offending_finding])
        )
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        message = str(excinfo.value)
        # The error must name the offending finding identifier so the
        # wrapper agent can correlate.
        assert "F-001" in message

    def test_malformed_json_raises(self) -> None:
        review_result = load_review_result_module()
        with pytest.raises(review_result.ReviewResultValidationError):
            review_result.parse_json("{not valid json")


class TestRoundTrip:
    """``to_json_dict`` and ``from_json_dict`` round-trip a
    ``ReviewResult`` without loss."""

    def test_round_trip_via_json_dict_preserves_equality(self) -> None:
        review_result = load_review_result_module()
        document = make_review_result_dict()
        result = review_result.parse_json(json.dumps(document))
        round_tripped = review_result.from_json_dict(review_result.to_json_dict(result))
        assert round_tripped == result

    def test_round_trip_via_parse_json_preserves_equality(self) -> None:
        review_result = load_review_result_module()
        document = make_review_result_dict()
        first = review_result.parse_json(json.dumps(document))
        emitted = json.dumps(review_result.to_json_dict(first))
        second = review_result.parse_json(emitted)
        assert first == second


class TestSeverityToRenderClassMapping:
    """``Severity`` members map to render classes via the partitioning function.

    ``must_fix`` → BLOCKING (the blockers partition).
    ``suggestion`` and ``nit`` → FOLLOW-UP (the followups partition).

    The mapping is total over ``Severity`` and lives in
    ``render_review._partition_findings``. Asserting it directly closes the
    Mapping-typed evidence the spec declares for the severity → render-class
    rule.
    """

    def _make_finding(self, severity: str, finding_id: str):
        review_result = load_review_result_module()
        return review_result.Finding(
            id=finding_id,
            concern=review_result.Concern("quality"),
            severity=review_result.Severity(severity),
            file="example.py",
            line=1,
            rule=FIXTURE_RULE_CITATION,
            message="m",
        )

    def test_must_fix_partitions_into_blockers(self) -> None:
        render_review = load_render_review_module()
        blockers, followups = render_review._partition_findings(
            [self._make_finding("must_fix", "F-001")]
        )
        assert [f.id for f in blockers] == ["F-001"]
        assert followups == []

    def test_suggestion_partitions_into_followups(self) -> None:
        render_review = load_render_review_module()
        blockers, followups = render_review._partition_findings(
            [self._make_finding("suggestion", "F-002")]
        )
        assert blockers == []
        assert [f.id for f in followups] == ["F-002"]

    def test_nit_partitions_into_followups(self) -> None:
        render_review = load_render_review_module()
        blockers, followups = render_review._partition_findings(
            [self._make_finding("nit", "F-003")]
        )
        assert blockers == []
        assert [f.id for f in followups] == ["F-003"]

    def test_mixed_severities_split_across_classes(self) -> None:
        render_review = load_render_review_module()
        findings = [
            self._make_finding("must_fix", "F-001"),
            self._make_finding("suggestion", "F-002"),
            self._make_finding("nit", "F-003"),
            self._make_finding("must_fix", "F-004"),
        ]
        blockers, followups = render_review._partition_findings(findings)
        assert {f.id for f in blockers} == {"F-001", "F-004"}
        assert {f.id for f in followups} == {"F-002", "F-003"}


class TestRuleCitationForm:
    """``Finding.rule`` must be a path-style citation; the parser rejects others.

    Accepted prefixes: ``spx/``, ``plugins/``, ``AGENTS.md``, ``CLAUDE.md``,
    ``SKILL.md``. The semantic check (cited rule exists at the location)
    is the lens prompt's concern and is not enforced at parse time.
    """

    @pytest.mark.parametrize(
        "rule",
        [
            "spx/21-spec-tree.enabler/spec-tree.md:ALWAYS:1",
            "plugins/python/skills/standardizing-python/SKILL.md:atemporal-voice",
            "AGENTS.md:critical-rules",
            "CLAUDE.md:imperfection-protocol",
            "SKILL.md:render-templates-as-data",
        ],
    )
    def test_parser_accepts_path_style_rule(self, rule: str) -> None:
        review_result = load_review_result_module()
        finding = {
            "id": "F-001",
            "concern": "quality",
            "severity": "suggestion",
            "file": "x.py",
            "line": 1,
            "rule": rule,
            "message": "m",
        }
        # parse_json should not raise on a conforming rule citation.
        review_result.parse_json(
            json.dumps(make_review_result_dict(findings=[finding]))
        )

    @pytest.mark.parametrize(
        "rule",
        [
            "",
            "naming",
            "fix the typo",
            "Track under: ISSUES.md",
            "r",
            "spec/auth.md:ALWAYS:1",  # wrong prefix (spec/ not spx/)
        ],
    )
    def test_parser_rejects_non_citation_rule(self, rule: str) -> None:
        review_result = load_review_result_module()
        finding = {
            "id": "F-001",
            "concern": "quality",
            "severity": "suggestion",
            "file": "x.py",
            "line": 1,
            "rule": rule,
            "message": "m",
        }
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(
                json.dumps(make_review_result_dict(findings=[finding]))
            )
        # The error message must name the offending value so the wrapper
        # agent can correlate the rejection with the finding it emitted.
        assert "rule" in str(excinfo.value)
