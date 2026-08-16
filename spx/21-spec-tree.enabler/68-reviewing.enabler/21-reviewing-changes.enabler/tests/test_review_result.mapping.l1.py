"""Mapping evidence for the ``review_result`` policy module.

Covers these clauses in ``../reviewing-changes.md`` and
``../21-script-decomposition.adr.md``:

- ``Severity`` enum members map to the wire values ``blocking``, ``debt``.
- ``Concern`` enum members map to exactly the five wire values
  ``consistency``, ``security``, ``performance``, ``evidence``,
  ``architecture``.
- ``Finding.rule`` is a path-style citation from one of the declared citation
  families, and the spec-assertion family carries the audit vocabulary
  (``AUDIT``) beside the rule markers and the four other assertion kinds.

Each domain is imported from the ``review_result`` module; each expectation
is the relationship the spec declares, independent of the parser's own tables.
"""

from __future__ import annotations

import json

import pytest

from outcomeeng_testing.harnesses.reviewing_changes import (
    RULE_CITATION_EXEMPLARS,
    load_review_result_module,
    make_finding_dict,
    make_review_result_dict,
)

review_result = load_review_result_module()


class TestSeverityWireValues:
    """Every ``Severity`` member maps to one of the two declared wire values."""

    def test_severity_members_map_to_the_two_wire_values(self) -> None:
        wire_values = {member.value for member in review_result.Severity}
        assert wire_values == {"blocking", "debt"}

    @pytest.mark.parametrize("member", list(review_result.Severity))
    def test_each_severity_member_maps_to_its_lowercase_name(self, member) -> None:
        assert member.value == member.name.lower()


class TestConcernWireValues:
    """Every ``Concern`` member maps to one of the five declared wire values."""

    def test_concern_members_map_to_the_five_wire_values(self) -> None:
        wire_values = {member.value for member in review_result.Concern}
        assert wire_values == {
            "consistency",
            "security",
            "performance",
            "evidence",
            "architecture",
        }

    @pytest.mark.parametrize("member", list(review_result.Concern))
    def test_each_concern_member_maps_to_its_lowercase_name(self, member) -> None:
        assert member.value == member.name.lower()


class TestRuleCitationFamilies:
    """Every declared citation family maps to an accepted ``Finding.rule`` form."""

    def test_every_declared_family_has_an_exemplar(self) -> None:
        assert set(RULE_CITATION_EXEMPLARS) == set(review_result.RULE_CITATION_FAMILIES)

    @pytest.mark.parametrize("family", review_result.RULE_CITATION_FAMILIES)
    def test_family_exemplar_classifies_to_its_family(self, family: str) -> None:
        assert (
            review_result.rule_citation_family(RULE_CITATION_EXEMPLARS[family])
            == family
        )

    @pytest.mark.parametrize("family", review_result.RULE_CITATION_FAMILIES)
    def test_family_exemplar_is_accepted_by_the_parser(self, family: str) -> None:
        rule = RULE_CITATION_EXEMPLARS[family]
        payload = json.dumps(
            make_review_result_dict(findings=[make_finding_dict(rule=rule)])
        )

        result = review_result.parse_json(payload)

        assert result.findings[0].rule == rule


class TestSpecAssertionKinds:
    """The spec-assertion family's kind vocabulary carries the audit vocabulary."""

    def test_kinds_are_the_rule_markers_plus_the_assertion_and_audit_kinds(
        self,
    ) -> None:
        assert set(review_result.SPEC_ASSERTION_KINDS) == {
            "ALWAYS",
            "NEVER",
            "MUST",
            "SCENARIO",
            "MAPPING",
            "CONFORMANCE",
            "PROPERTY",
            "AUDIT",
        }

    @pytest.mark.parametrize("kind", review_result.SPEC_ASSERTION_KINDS)
    def test_each_kind_forms_a_spec_assertion_citation(self, kind: str) -> None:
        rule = f"spx/example.md:{kind}:1"
        assert review_result.rule_citation_family(rule) == "spec-assertion"
