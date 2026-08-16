"""Scenario evidence for the ``review_result`` policy module.

Covers these clauses in ``../reviewing-changes.md``:

- Given a conforming document, ``review_result.parse_json`` returns a
  ``ReviewResult`` dataclass.
- Given a document that omits a required key, ``parse_json`` raises
  ``ReviewResultValidationError`` naming the missing key.
- Given a finding whose ``severity`` or ``concern`` is outside its enum,
  ``parse_json`` raises naming the offending value and the allowed set.
- ``review_result.to_json_dict`` and ``review_result.from_json_dict``
  round-trip a ``ReviewResult`` instance without loss.

Each test is one existential interaction; the universal wire-value, citation
family, and citation-rejection claims live in the sibling mapping and
compliance files.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from outcomeeng_testing.harnesses.reviewing_changes import (
    FIXTURE_AGENTS_RULE_CITATION,
    FIXTURE_RULE_CITATION,
    FIXTURE_SKILL_RULE_CITATION,
    REPO_ROOT,
    load_review_result_module,
    make_review_result_dict,
)


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


class TestRuleCitationResolution:
    """A cited rule resolves against the runtime layout and the repository root."""

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
