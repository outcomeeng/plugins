"""Scenario and mapping tests for the ``review_result`` policy module.

Covers these clauses in ``../reviewing-changes.md``:

Scenarios
- ``review_result.parse_json`` returns a ``ReviewResult`` dataclass on a
  conforming document and raises ``ReviewResultValidationError`` on
  every violation surfaced by the arbiter.
- ``review_result.to_json_dict`` and ``review_result.from_json_dict``
  round-trip a ``ReviewResult`` instance without loss.

Mappings
- ``Severity`` enum members map to the wire values ``blocking``,
  ``debt``.
- ``Concern`` enum members map to exactly the six wire values
  ``consistency``, ``security``, ``performance``, ``evidence``,
  ``standards``, ``architecture``.

Compliance (subset)
- The policy module declares ``SCHEMA_VERSION``, frozen ``Finding`` and
  ``ReviewResult`` dataclasses, the ``Severity`` / ``Concern`` enums.
- The schema carries no ``decision``/verdict field — the reviewer emits
  findings only.
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

    def test_severity_and_concern_enums_exist_and_no_decision(self) -> None:
        review_result = load_review_result_module()
        assert hasattr(review_result, "Severity")
        assert hasattr(review_result, "Concern")
        # The reviewer emits findings only — there is no decision/verdict
        # enum on the schema.
        assert not hasattr(review_result, "Decision")

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


class TestSeverityMapping:
    """``Severity`` members map to the wire values ``blocking``,
    ``debt``."""

    def test_severity_members_map_to_wire_values(self) -> None:
        review_result = load_review_result_module()
        wire_values = {member.value for member in review_result.Severity}
        assert wire_values == {"blocking", "debt"}


class TestConcernMapping:
    """``Concern`` members map to exactly the six wire values
    declared in the spec."""

    def test_concern_members_map_to_six_wire_values(self) -> None:
        review_result = load_review_result_module()
        wire_values = {member.value for member in review_result.Concern}
        assert wire_values == {
            "consistency",
            "security",
            "performance",
            "evidence",
            "standards",
            "architecture",
        }


class TestParseJsonConforming:
    """``parse_json`` returns a ``ReviewResult`` on a conforming document."""

    def test_parse_json_returns_review_result_on_conforming_document(self) -> None:
        review_result = load_review_result_module()
        payload = json.dumps(make_review_result_dict())
        result = review_result.parse_json(payload)
        assert isinstance(result, review_result.ReviewResult)

    def test_parse_json_accepts_empty_findings(self) -> None:
        review_result = load_review_result_module()
        payload = json.dumps(make_review_result_dict(findings=[]))
        result = review_result.parse_json(payload)
        assert result.findings == ()


class TestParseJsonRejection:
    """``parse_json`` raises ``ReviewResultValidationError`` on every
    schema violation surfaced by the arbiter."""

    def test_missing_required_key_raises(self) -> None:
        review_result = load_review_result_module()
        document = make_review_result_dict()
        del document["summary"]
        payload = json.dumps(document)
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        assert "summary" in str(excinfo.value)

    def test_unknown_severity_raises_with_value_and_allowed_set(self) -> None:
        review_result = load_review_result_module()
        bad_finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "blocker",  # not a Severity member
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "m",
            "action": "a",
        }
        payload = json.dumps(make_review_result_dict(findings=[bad_finding]))
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        message = str(excinfo.value)
        assert "blocker" in message
        assert "blocking" in message  # part of the allowed set

    def test_unknown_concern_raises_with_value_and_allowed_set(self) -> None:
        review_result = load_review_result_module()
        bad_finding = {
            "id": "F-001",
            "concern": "marketing",  # not a Concern member
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "m",
            "action": "a",
        }
        payload = json.dumps(make_review_result_dict(findings=[bad_finding]))
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        message = str(excinfo.value)
        assert "marketing" in message
        assert "consistency" in message  # part of the allowed set

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

    def test_action_field_round_trips(self) -> None:
        review_result = load_review_result_module()
        finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "Issue body",
            "action": "ISSUES.md",
        }
        document = make_review_result_dict(findings=[finding])
        first = review_result.parse_json(json.dumps(document))
        assert first.findings[0].action == "ISSUES.md"
        emitted = json.dumps(review_result.to_json_dict(first))
        second = review_result.parse_json(emitted)
        assert second.findings[0].action == "ISSUES.md"

    def test_missing_action_field_raises(self) -> None:
        review_result = load_review_result_module()
        finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "m",
            # action is required; omitting it must raise
        }
        document = make_review_result_dict(findings=[finding])
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(json.dumps(document))
        assert "action" in str(excinfo.value)


class TestSeverityToRenderClassMapping:
    """``Severity`` members map to render classes via the partitioning function.

    ``blocking`` → BLOCKING bucket.
    ``debt`` → DEBT bucket.

    The mapping is total over ``Severity`` and lives in
    ``render_review._partition_findings``. Asserting it directly closes the
    Mapping-typed evidence the spec declares for the severity → render-class
    rule.
    """

    def _make_finding(self, severity: str, finding_id: str):
        review_result = load_review_result_module()
        return review_result.Finding(
            id=finding_id,
            concern=review_result.Concern("consistency"),
            severity=review_result.Severity(severity),
            file="example.py",
            line=1,
            rule=FIXTURE_RULE_CITATION,
            message="m",
            action="a",
        )

    def test_blocking_partitions_into_blocking_bucket(self) -> None:
        render_review = load_render_review_module()
        buckets = render_review._partition_findings(
            [self._make_finding("blocking", "F-001")]
        )
        assert [f.id for f in buckets["blocking"]] == ["F-001"]
        assert buckets["debt"] == []

    def test_debt_partitions_into_debt_bucket(self) -> None:
        render_review = load_render_review_module()
        buckets = render_review._partition_findings(
            [self._make_finding("debt", "F-002")]
        )
        assert buckets["blocking"] == []
        assert [f.id for f in buckets["debt"]] == ["F-002"]

    def test_mixed_severities_split_across_buckets(self) -> None:
        render_review = load_render_review_module()
        findings = [
            self._make_finding("blocking", "F-001"),
            self._make_finding("debt", "F-002"),
            self._make_finding("debt", "F-003"),
            self._make_finding("blocking", "F-004"),
        ]
        buckets = render_review._partition_findings(findings)
        assert {f.id for f in buckets["blocking"]} == {"F-001", "F-004"}
        assert {f.id for f in buckets["debt"]} == {"F-002", "F-003"}


class TestRuleCitationForm:
    """``Finding.rule`` must be a path-style citation; the parser rejects others.

    Accepted prefixes: ``spx/``, ``plugins/``, ``AGENTS.md``, ``CLAUDE.md``,
    ``SKILL.md``. The semantic check (cited rule exists at the location)
    is the review prompt's concern and is not enforced at parse time.
    """

    @pytest.mark.parametrize(
        "rule",
        [
            "spx/21-spec-tree.enabler/spec-tree.md:ALWAYS:1",
            "plugins/python/skills/python-standards/SKILL.md:atemporal-voice",
            "AGENTS.md:critical-rules",
            "CLAUDE.md:imperfection-protocol",
            "SKILL.md:render-templates-as-data",
        ],
    )
    def test_parser_accepts_path_style_rule(self, rule: str) -> None:
        review_result = load_review_result_module()
        finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": rule,
            "message": "m",
            "action": "a",
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
            "concern": "consistency",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": rule,
            "message": "m",
            "action": "a",
        }
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(
                json.dumps(make_review_result_dict(findings=[finding]))
            )
        # The error message must name the offending value so the wrapper
        # agent can correlate the rejection with the finding it emitted.
        assert "rule" in str(excinfo.value)
