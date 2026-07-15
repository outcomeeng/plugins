"""Compliance tests for the ``review_result`` policy module.

Covers these clauses in ``../reviewing-changes.md``:

Compliance
- ``review_result.parse_json`` returns a ``ReviewResult`` dataclass on a
  conforming document and raises ``ReviewResultValidationError`` on
  every schema violation.
- The policy module declares ``SCHEMA_VERSION``, frozen ``Finding`` and
  ``ReviewResult`` dataclasses, the ``Severity`` / ``Concern`` enums.
- The schema carries no ``decision``/verdict field — the reviewer emits
  findings only.
"""

from __future__ import annotations

import dataclasses
import json
import pathlib

import pytest

from outcomeeng_testing.generators.reviewing_changes import (
    finding_without_required_field,
    unknown_review_concern,
    unknown_review_severity,
    valid_rule_citations,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REPO_ROOT,
    load_review_result_module,
    malformed_rule_citation,
    make_finding_dict,
    make_review_result_dict,
    review_rule_citations,
    rule_slug_document,
    runtime_review_skill_path,
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
    schema violation."""

    def test_missing_required_key_raises(self) -> None:
        review_result = load_review_result_module()
        document = make_review_result_dict()
        del document["findings"]
        payload = json.dumps(document)
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        assert "findings" in str(excinfo.value)

    def test_unknown_severity_raises_with_value_and_allowed_set(self) -> None:
        review_result = load_review_result_module()
        unknown_severity = unknown_review_severity()
        bad_finding = make_finding_dict(severity=unknown_severity)
        payload = json.dumps(make_review_result_dict(findings=[bad_finding]))
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        message = str(excinfo.value)
        assert unknown_severity in message
        assert next(iter(review_result.Severity)).value in message

    def test_unknown_concern_raises_with_value_and_allowed_set(self) -> None:
        review_result = load_review_result_module()
        unknown_concern = unknown_review_concern()
        bad_finding = make_finding_dict(concern=unknown_concern)
        payload = json.dumps(make_review_result_dict(findings=[bad_finding]))
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)
        message = str(excinfo.value)
        assert unknown_concern in message
        assert next(iter(review_result.Concern)).value in message

    def test_malformed_json_raises(self) -> None:
        review_result = load_review_result_module()
        with pytest.raises(review_result.ReviewResultValidationError):
            review_result.parse_json("{not valid json")

    def test_missing_action_field_raises(self) -> None:
        review_result = load_review_result_module()
        finding = finding_without_required_field("action")
        document = make_review_result_dict(findings=[finding])
        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(json.dumps(document))
        assert "action" in str(excinfo.value)


class TestRuleCitationValidation:
    """``Finding.rule`` accepts declared citation families and rejects prose."""

    @pytest.mark.parametrize("rule_citation", valid_rule_citations())
    def test_parse_json_accepts_declared_rule_citation_forms(
        self,
        rule_citation: str,
    ) -> None:
        review_result = load_review_result_module()
        finding = make_finding_dict(rule=rule_citation)
        payload = json.dumps(make_review_result_dict(findings=[finding]))

        result = review_result.parse_json(payload)

        assert result.findings[0].rule == rule_citation

    def test_parse_json_rejects_free_form_rule_text(self) -> None:
        review_result = load_review_result_module()
        malformed = malformed_rule_citation()
        finding = make_finding_dict(rule=malformed)
        payload = json.dumps(make_review_result_dict(findings=[finding]))

        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)

        message = str(excinfo.value)
        assert "rule" in message
        assert malformed in message


class TestRuleCitationForm:
    """``Finding.rule`` must be a path-style citation; the parser rejects others.

    Accepted forms: ``spx/<path>.md:<assertion-kind>:<n>``,
    ``spx/<path>/<n>-<slug>.adr.md``,
    ``spx/<path>/<n>-<slug>.pdr.md``,
    ``plugins/<plugin>/skills/<skill>/SKILL.md:<rule-slug>``,
    ``AGENTS.md:<rule-slug>``, and ``CLAUDE.md:<rule-slug>``.
    The parser rejects citations whose file or rule slug cannot be
    verified mechanically.
    """

    @pytest.mark.parametrize("rule", valid_rule_citations())
    def test_parser_accepts_path_style_rule(self, rule: str) -> None:
        review_result = load_review_result_module()
        finding = make_finding_dict(rule=rule)
        # parse_json should not raise on a conforming rule citation.
        review_result.parse_json(
            json.dumps(make_review_result_dict(findings=[finding]))
        )

    def test_plugin_skill_rule_can_resolve_absolute_runtime_path(self) -> None:
        review_result = load_review_result_module()
        skill_path = runtime_review_skill_path()

        review_result._validate_slug(
            skill_path,
            review_rule_citations()[3].rsplit(":", maxsplit=1)[1],
            review_rule_citations()[3],
        )

    def test_plugin_skill_rule_resolves_from_runtime_layout_without_repo_tree(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        from outcomeeng_testing.harnesses.reviewing_changes import (
            versioned_sibling_plugin_resolution_holds,
        )

        assert versioned_sibling_plugin_resolution_holds()

    def test_root_rule_resolves_from_git_root_when_cwd_is_subdirectory(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        review_result = load_review_result_module()
        monkeypatch.chdir(
            REPO_ROOT
            / pathlib.Path(review_rule_citations()[0].split(":", maxsplit=1)[0]).parent
        )
        finding = make_finding_dict(rule=review_rule_citations()[4])

        review_result.parse_json(
            json.dumps(make_review_result_dict(findings=[finding]))
        )

    def test_rule_slug_discovery_rejects_bold_marker_prose(self) -> None:
        review_result = load_review_result_module()
        slugs = review_result._declared_rule_slugs(rule_slug_document())

        assert "narrative" not in slugs
        assert "critical-rules" in slugs
        assert "principles" in slugs
        assert "rules" not in slugs
