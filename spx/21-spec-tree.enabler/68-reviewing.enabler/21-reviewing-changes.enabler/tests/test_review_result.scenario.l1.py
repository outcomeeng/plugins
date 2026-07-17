"""Scenario and mapping tests for the ``review_result`` policy module.

Covers these clauses in ``../reviewing-changes.md``:

Scenarios
- ``review_result.parse_json`` returns a ``ReviewResult`` dataclass on a
  conforming document and raises ``ReviewResultValidationError`` on
  every schema violation.
- ``review_result.to_json_dict`` and ``review_result.from_json_dict``
  round-trip a ``ReviewResult`` instance without loss.

Mappings
- ``Severity`` enum members map to the wire values ``blocking``,
  ``debt``.
- ``Concern`` enum members map to exactly the five wire values
  ``consistency``, ``security``, ``performance``, ``evidence``,
  ``architecture``.

Audit (subset)
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

from outcomeeng_testing.harnesses.reviewing_changes import (
    FIXTURE_ADR_RULE_CITATION,
    FIXTURE_AGENTS_RULE_CITATION,
    FIXTURE_MALFORMED_RULE_CITATION,
    FIXTURE_RULE_CITATION,
    FIXTURE_SKILL_RULE_CITATION,
    REPO_ROOT,
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
    """``Concern`` members map to exactly the five wire values
    declared in the spec."""

    def test_concern_members_map_to_five_wire_values(self) -> None:
        review_result = load_review_result_module()
        wire_values = {member.value for member in review_result.Concern}
        assert wire_values == {
            "consistency",
            "security",
            "performance",
            "evidence",
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

    @pytest.mark.parametrize("finding_id", ["", "1", "F-1", "F-0000", "X-001"])
    def test_malformed_finding_id_raises(self, finding_id: str) -> None:
        review_result = load_review_result_module()
        bad_finding = {
            "id": finding_id,
            "concern": "consistency",
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
        assert "id" in message
        assert finding_id in message

    def test_malformed_json_raises(self) -> None:
        review_result = load_review_result_module()
        with pytest.raises(review_result.ReviewResultValidationError):
            review_result.parse_json("{not valid json")


class TestRuleCitationValidation:
    """``Finding.rule`` accepts declared citation families and rejects prose."""

    @pytest.mark.parametrize(
        "rule_citation",
        (
            FIXTURE_RULE_CITATION,
            FIXTURE_ADR_RULE_CITATION,
            FIXTURE_AGENTS_RULE_CITATION,
        ),
    )
    def test_parse_json_accepts_declared_rule_citation_forms(
        self,
        rule_citation: str,
    ) -> None:
        review_result = load_review_result_module()
        finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": rule_citation,
            "message": "m",
            "action": "a",
        }
        payload = json.dumps(make_review_result_dict(findings=[finding]))

        result = review_result.parse_json(payload)

        assert result.findings[0].rule == rule_citation

    def test_parse_json_rejects_free_form_rule_text(self) -> None:
        review_result = load_review_result_module()
        finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_MALFORMED_RULE_CITATION,
            "message": "m",
            "action": "a",
        }
        payload = json.dumps(make_review_result_dict(findings=[finding]))

        with pytest.raises(review_result.ReviewResultValidationError) as excinfo:
            review_result.parse_json(payload)

        message = str(excinfo.value)
        assert "rule" in message
        assert FIXTURE_MALFORMED_RULE_CITATION in message


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

    @pytest.mark.parametrize(
        "rule",
        [
            FIXTURE_RULE_CITATION,
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:NEVER:1",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:SCENARIO:1",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:SCENARIO:2",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:MAPPING:1",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:MAPPING:2",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:PROPERTY:1",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:AUDIT:1",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:AUDIT:2",
            "spx/21-spec-tree.enabler/spec-tree.md:CONFORMANCE:1",
            "spx/outcomeeng.product.md:COMPLIANCE:1",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/21-script-decomposition.adr.md",
            "spx/15-merging.pdr.md",
            FIXTURE_SKILL_RULE_CITATION,
            "plugins/spec-tree/skills/understand/SKILL.md:layer-precedence",
            "CLAUDE.md:critical-rules",
            FIXTURE_AGENTS_RULE_CITATION,
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

    def test_plugin_skill_rule_can_resolve_absolute_runtime_path(self) -> None:
        review_result = load_review_result_module()
        skill_path = pathlib.Path(
            "dist/claude/spec-tree/skills/review-changes/SKILL.md"
        ).resolve(strict=True)

        review_result._validate_slug(
            skill_path,
            "api-surface",
            FIXTURE_SKILL_RULE_CITATION,
        )

    def test_cross_plugin_rule_resolves_from_installed_cache_without_repo(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        review_result = load_review_result_module()
        marketplace_root = tmp_path / "cache" / "outcomeeng"
        cited_marketplace_root = tmp_path / "cache" / "external-marketplace"
        fake_script = (
            marketplace_root
            / "spec-tree"
            / "0.78.2"
            / "skills"
            / "review-changes"
            / "scripts"
            / "review_result.py"
        )
        fake_script.parent.mkdir(parents=True)
        fake_script.touch()
        skill_path = (
            cited_marketplace_root
            / "typescript"
            / "0.10.0"
            / "skills"
            / "audit-typescript-architecture"
            / "SKILL.md"
        )
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text(
            "<constraints>\n\n- ALWAYS: preserve architecture boundaries.\n\n</constraints>\n",
            encoding="utf-8",
        )
        stale_skill_path = (
            cited_marketplace_root
            / "typescript"
            / "0.9.0"
            / "skills"
            / "audit-typescript-architecture"
            / "SKILL.md"
        )
        stale_skill_path.parent.mkdir(parents=True)
        stale_skill_path.write_text(
            "<objective>Stale cache entry without the cited rule.</objective>\n",
            encoding="utf-8",
        )
        empty_repo = tmp_path / "empty-repo"
        empty_repo.mkdir()
        monkeypatch.chdir(empty_repo)
        monkeypatch.setattr(review_result, "__file__", str(fake_script))
        rule = (
            "plugins/typescript/skills/audit-typescript-architecture/"
            "SKILL.md:constraints"
        )
        finding = {
            "id": "F-001",
            "concern": "architecture",
            "severity": "debt",
            "file": "x.ts",
            "line": 1,
            "rule": rule,
            "message": "m",
            "action": "a",
        }

        review_result.parse_json(
            json.dumps(make_review_result_dict(findings=[finding]))
        )

    def test_inline_foundation_citations_require_a_rule_marker(self) -> None:
        review_result = load_review_result_module()
        skill_path = REPO_ROOT / "src/plugins/spec-tree/skills/understand/SKILL.md"
        declared_slugs = review_result._declared_rule_slugs(
            skill_path.read_text(encoding="utf-8")
        )

        assert "layer-precedence" in declared_slugs
        assert "future-product-truth" not in declared_slugs
        assert "truth-hierarchy" not in declared_slugs

    def test_plugin_skill_rule_resolves_from_runtime_layout_without_repo_tree(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        review_result = load_review_result_module()
        monkeypatch.chdir(tmp_path)
        finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_SKILL_RULE_CITATION,
            "message": "m",
            "action": "a",
        }

        review_result.parse_json(
            json.dumps(make_review_result_dict(findings=[finding]))
        )

    def test_root_rule_resolves_from_git_root_when_cwd_is_subdirectory(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        review_result = load_review_result_module()
        monkeypatch.chdir(
            REPO_ROOT
            / "spx"
            / "21-spec-tree.enabler"
            / "68-reviewing.enabler"
            / "21-reviewing-changes.enabler"
        )
        finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_AGENTS_RULE_CITATION,
            "message": "m",
            "action": "a",
        }

        review_result.parse_json(
            json.dumps(make_review_result_dict(findings=[finding]))
        )

    def test_rule_slug_discovery_rejects_bold_marker_prose(self) -> None:
        review_result = load_review_result_module()
        document = """# Rules

### Narrative

This paragraph names **ALWAYS** as prose, not as a rule marker.

```text
### Example Finding
Reference: <file:line or governing rule>
```

### Critical Rules

- ⚠️ **NEVER answer** without loading the rule source.

<principles>

ALWAYS: pseudo-XML sections are rule-bearing surfaces.

</principles>
"""

        slugs = review_result._declared_rule_slugs(document)

        assert "narrative" not in slugs
        assert "critical-rules" in slugs
        assert "principles" in slugs
        assert "rules" not in slugs

    def test_rule_slug_discovery_does_not_promote_structural_parents(self) -> None:
        review_result = load_review_result_module()
        document = """<workflow>

<examples>

```text
ALWAYS: fenced examples do not declare rules.
```

</examples>

<constraints>

ALWAYS: direct imperative constraints remain citeable when explicitly marked.

</constraints>

<critical_rules>

ALWAYS: direct custom rule markers remain citeable.

</critical_rules>

</workflow>
"""

        slugs = review_result._declared_rule_slugs(document)

        assert "workflow" not in slugs
        assert "examples" not in slugs
        assert "constraints" in slugs
        assert "critical-rules" in slugs

    @pytest.mark.parametrize(
        "rule",
        [
            "",
            "naming",
            "fix the typo",
            "Track under: ISSUES.md",
            "r",
            "spec/auth.md:ALWAYS:1",  # wrong prefix (spec/ not spx/)
            "spx/",
            "spx/rules.md",
            "spx/rules.md:ALWAYS",
            "spx/rules.md:SCENARIO",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:SCENARIO:999",
            "spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/reviewing-changes.md:PROPERTY:2",
            "plugins/foo",
            "plugins/foo/skills/bar",
            "plugins/foo/skills/bar/SKILL.md",
            "plugins/python/skills/standardizing-python/SKILL.md:atemporal-voice",
            "plugins/spec-tree/skills/review-changes/SKILL.md:objective",
            "plugins/spec-tree/skills/review-changes/SKILL.md:review",
            "plugins/spec-tree/skills/review-changes/SKILL.md:workflow",
            "AGENTS.md",
            "AGENTS.md:plugins",
            "AGENTS.md:two-audiences-two-design-surfaces",
            "AGENTS.md:documentation",
            "AGENTS.md:plugin-catalog",
            "AGENTS.md:why",
            "AGENTS.md:not-a-real-rule-slug",
            "CLAUDE.md",
            "CLAUDE.md:plugins",
            "CLAUDE.md:never-use",
            "REVIEW.md",
            "REVIEW.md:not-a-real-rule-slug",
            "SKILL.md",
            "SKILL.md:render-templates-as-data",
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
