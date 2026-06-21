"""Compliance tests for the canonical verdict module.

Covers the Compliance MUST clauses on ``verdict.py`` in
``../verdict-toolchain.md``:

- the canonical schema constants (Status, Severity, SCHEMA_VERSION)
- ``parse_json`` validates required keys, status values, and severity
  values and raises ``VerdictValidationError`` on every kind of
  violation declared by the spec
- ``to_json_dict``/``from_json_dict`` round-trip without loss
- ``roll_up`` applies the four-case rollup rule
- ``row_status_from_findings`` derives PASS/FAIL purely from finding
  severities
"""

from __future__ import annotations

import json

import pytest
from outcomeeng_testing.harnesses.verdict_toolchain import load_verdict_module

verdict_mod = load_verdict_module()


VALID_VERDICT_DICT = {
    "schema_version": 1,
    "skill": "audit-typescript",
    "target": "spx/path/to/node",
    "overall": "PASS",
    "rows": [
        {
            "name": "scope",
            "status": "PASS",
            "findings": [],
        },
        {
            "name": "evidence",
            "status": "FAIL",
            "findings": [
                {
                    "id": "f-001",
                    "file": "src/foo.ts",
                    "line": 42,
                    "rule": "no-shared-bag",
                    "severity": "REJECT",
                    "message": "Shared constant bag declared.",
                }
            ],
        },
    ],
    "children": [],
    "metadata": {"branch": "main"},
    "resolved": [],
    "reopened": [],
}


class TestStatusAndSeverityEnums:
    def test_status_has_five_members(self) -> None:
        assert {s.value for s in verdict_mod.Status} == {
            "APPROVED",
            "REJECTED",
            "PASS",
            "FAIL",
            "UNKNOWN",
        }

    def test_severity_has_three_members(self) -> None:
        assert {s.value for s in verdict_mod.Severity} == {
            "REJECT",
            "WARNING",
            "INFO",
        }

    def test_root_statuses_constant_matches_subset(self) -> None:
        assert verdict_mod.ROOT_STATUSES == frozenset(
            {"APPROVED", "REJECTED", "UNKNOWN"}
        )

    def test_skill_statuses_constant_matches_subset(self) -> None:
        assert verdict_mod.SKILL_STATUSES == frozenset({"PASS", "FAIL", "UNKNOWN"})

    def test_schema_version_is_positive_integer(self) -> None:
        assert isinstance(verdict_mod.SCHEMA_VERSION, int)
        assert verdict_mod.SCHEMA_VERSION >= 1


class TestParseJsonAcceptsValidVerdict:
    def test_returns_verdict_dataclass(self) -> None:
        v = verdict_mod.parse_json(json.dumps(VALID_VERDICT_DICT))
        assert isinstance(v, verdict_mod.Verdict)
        assert v.skill == "audit-typescript"
        assert v.target == "spx/path/to/node"
        assert v.overall == verdict_mod.Status.PASS
        assert len(v.rows) == 2
        assert v.rows[1].findings[0].rule == "no-shared-bag"
        assert v.rows[1].findings[0].severity == verdict_mod.Severity.REJECT

    def test_accepts_optional_children_and_metadata(self) -> None:
        minimal = {
            "schema_version": 1,
            "skill": "x",
            "target": "y",
            "overall": "UNKNOWN",
        }
        v = verdict_mod.parse_json(json.dumps(minimal))
        assert v.rows == ()
        assert v.children == ()
        assert v.metadata == {}


class TestParseJsonRejectsSchemaViolations:
    def test_rejects_missing_required_key(self) -> None:
        bad = dict(VALID_VERDICT_DICT)
        del bad["target"]
        with pytest.raises(verdict_mod.VerdictValidationError):
            verdict_mod.parse_json(json.dumps(bad))

    def test_rejects_unknown_overall_value(self) -> None:
        bad = dict(VALID_VERDICT_DICT)
        bad["overall"] = "MAYBE"
        with pytest.raises(verdict_mod.VerdictValidationError):
            verdict_mod.parse_json(json.dumps(bad))

    def test_rejects_unknown_row_status(self) -> None:
        bad = dict(VALID_VERDICT_DICT)
        bad["rows"] = [{"name": "x", "status": "MAYBE", "findings": []}]
        with pytest.raises(verdict_mod.VerdictValidationError):
            verdict_mod.parse_json(json.dumps(bad))

    def test_rejects_unknown_finding_severity(self) -> None:
        bad = json.loads(json.dumps(VALID_VERDICT_DICT))
        bad["rows"][1]["findings"][0]["severity"] = "critical"
        with pytest.raises(verdict_mod.VerdictValidationError):
            verdict_mod.parse_json(json.dumps(bad))

    def test_rejects_schema_version_mismatch(self) -> None:
        bad = dict(VALID_VERDICT_DICT)
        bad["schema_version"] = 999
        with pytest.raises(verdict_mod.VerdictValidationError):
            verdict_mod.parse_json(json.dumps(bad))

    def test_rejects_non_object_document(self) -> None:
        with pytest.raises(verdict_mod.VerdictValidationError):
            verdict_mod.parse_json("[]")

    def test_rejects_malformed_json(self) -> None:
        with pytest.raises(verdict_mod.VerdictValidationError):
            verdict_mod.parse_json("{not json")

    def test_rejects_null_metadata_value(self) -> None:
        """A null metadata value would otherwise coerce to the string
        ``"None"`` — indistinguishable from an intentional string —
        and downstream ``metadata.get(key) is None`` checks would
        misbehave. The parser rejects the null up front so the caller
        is forced to omit the key when no value applies.
        """
        bad = json.loads(json.dumps(VALID_VERDICT_DICT))
        bad["metadata"] = {"flag": None}
        with pytest.raises(verdict_mod.VerdictValidationError, match="null"):
            verdict_mod.parse_json(json.dumps(bad))

    def test_coerces_non_string_scalar_metadata_value(self) -> None:
        """Int / float metadata values are coerced to ``str`` so the
        ``Verdict.metadata`` typing (``dict[str, str]``) holds.
        """
        ok = json.loads(json.dumps(VALID_VERDICT_DICT))
        ok["metadata"] = {"line_count": 42, "ratio": 0.5}
        v = verdict_mod.parse_json(json.dumps(ok))
        assert v.metadata == {"line_count": "42", "ratio": "0.5"}


class TestJsonRoundTrip:
    def test_parse_dump_parse_yields_equal_verdict(self) -> None:
        first = verdict_mod.parse_json(json.dumps(VALID_VERDICT_DICT))
        dumped = verdict_mod.dump_json(first)
        second = verdict_mod.parse_json(dumped)
        assert first == second

    def test_to_json_dict_matches_input_shape(self) -> None:
        v = verdict_mod.parse_json(json.dumps(VALID_VERDICT_DICT))
        produced = verdict_mod.to_json_dict(v)
        assert produced == VALID_VERDICT_DICT


RESOLVED_FINDING = {
    "id": "f-100",
    "file": "src/old.ts",
    "line": 7,
    "rule": "no-shared-bag",
    "severity": "INFO",
    "message": "Resolved by removing the shared bag.",
}

REOPENED_FINDING = {
    "id": "f-200",
    "file": "src/new.ts",
    "line": None,
    "rule": "no-shared-bag",
    "severity": "REJECT",
    "message": "Regression — shared bag re-introduced.",
}


class TestResolvedAndReopened:
    def test_round_trip_preserves_resolved_findings(self) -> None:
        payload = {**VALID_VERDICT_DICT, "resolved": [RESOLVED_FINDING]}
        v = verdict_mod.parse_json(json.dumps(payload))
        assert len(v.resolved) == 1
        assert v.resolved[0].id == RESOLVED_FINDING["id"]
        produced = verdict_mod.to_json_dict(v)
        assert produced["resolved"] == [RESOLVED_FINDING]

    def test_round_trip_preserves_reopened_findings(self) -> None:
        payload = {**VALID_VERDICT_DICT, "reopened": [REOPENED_FINDING]}
        v = verdict_mod.parse_json(json.dumps(payload))
        assert len(v.reopened) == 1
        assert v.reopened[0].id == REOPENED_FINDING["id"]
        produced = verdict_mod.to_json_dict(v)
        assert produced["reopened"] == [REOPENED_FINDING]

    def test_absent_resolved_defaults_to_empty(self) -> None:
        payload = {k: v for k, v in VALID_VERDICT_DICT.items() if k != "resolved"}
        v = verdict_mod.parse_json(json.dumps(payload))
        assert v.resolved == ()

    def test_absent_reopened_defaults_to_empty(self) -> None:
        payload = {k: v for k, v in VALID_VERDICT_DICT.items() if k != "reopened"}
        v = verdict_mod.parse_json(json.dumps(payload))
        assert v.reopened == ()

    def test_non_array_resolved_rejected(self) -> None:
        payload = {**VALID_VERDICT_DICT, "resolved": "not-a-list"}
        with pytest.raises(verdict_mod.VerdictValidationError, match="resolved"):
            verdict_mod.parse_json(json.dumps(payload))

    def test_non_array_reopened_rejected(self) -> None:
        payload = {**VALID_VERDICT_DICT, "reopened": "not-a-list"}
        with pytest.raises(verdict_mod.VerdictValidationError, match="reopened"):
            verdict_mod.parse_json(json.dumps(payload))


class TestRollUpRules:
    def test_all_pass_returns_approved(self) -> None:
        result = verdict_mod.roll_up([verdict_mod.Status.PASS, verdict_mod.Status.PASS])
        assert result == verdict_mod.Status.APPROVED

    def test_any_fail_returns_rejected(self) -> None:
        result = verdict_mod.roll_up(
            [
                verdict_mod.Status.PASS,
                verdict_mod.Status.FAIL,
                verdict_mod.Status.UNKNOWN,
            ]
        )
        assert result == verdict_mod.Status.REJECTED

    def test_any_rejected_returns_rejected(self) -> None:
        result = verdict_mod.roll_up(
            [verdict_mod.Status.APPROVED, verdict_mod.Status.REJECTED]
        )
        assert result == verdict_mod.Status.REJECTED

    def test_unknown_without_fail_returns_unknown(self) -> None:
        result = verdict_mod.roll_up(
            [verdict_mod.Status.PASS, verdict_mod.Status.UNKNOWN]
        )
        assert result == verdict_mod.Status.UNKNOWN

    def test_empty_returns_unknown(self) -> None:
        assert verdict_mod.roll_up([]) == verdict_mod.Status.UNKNOWN

    def test_root_and_skill_statuses_compose(self) -> None:
        result = verdict_mod.roll_up(
            [verdict_mod.Status.APPROVED, verdict_mod.Status.PASS]
        )
        assert result == verdict_mod.Status.APPROVED


class TestRowStatusFromFindings:
    def test_empty_findings_returns_pass(self) -> None:
        assert verdict_mod.row_status_from_findings(()) == verdict_mod.Status.PASS

    def test_only_info_findings_return_pass(self) -> None:
        finding = verdict_mod.Finding(
            id="f-001",
            file="src/foo.ts",
            line=None,
            rule="r",
            severity=verdict_mod.Severity.INFO,
            message="m",
        )
        assert (
            verdict_mod.row_status_from_findings((finding,)) == verdict_mod.Status.PASS
        )

    def test_only_warning_findings_return_pass(self) -> None:
        finding = verdict_mod.Finding(
            id="f-001",
            file="src/foo.ts",
            line=None,
            rule="r",
            severity=verdict_mod.Severity.WARNING,
            message="m",
        )
        assert (
            verdict_mod.row_status_from_findings((finding,)) == verdict_mod.Status.PASS
        )

    def test_reject_finding_returns_fail(self) -> None:
        reject_finding = verdict_mod.Finding(
            id="f-002",
            file="src/foo.ts",
            line=None,
            rule="r",
            severity=verdict_mod.Severity.REJECT,
            message="m",
        )
        warning_finding = verdict_mod.Finding(
            id="f-001",
            file="src/foo.ts",
            line=None,
            rule="r",
            severity=verdict_mod.Severity.WARNING,
            message="m",
        )
        assert (
            verdict_mod.row_status_from_findings((warning_finding, reject_finding))
            == verdict_mod.Status.FAIL
        )


class TestVerdictIsUnhashable:
    """Pin the explicit ``__hash__ = None`` declaration on ``Verdict``.

    ``@dataclass(frozen=True)`` normally auto-generates ``__hash__``,
    but Verdict carries a ``dict[str, str]`` metadata field — the
    auto-hash would fail at hash time when metadata is non-empty. The
    production class sets ``__hash__ = None`` to surface a clear
    ``TypeError`` at the call site instead. A regression that removes
    the line (or replaces it with ``object`` inheritance) would silently
    re-enable hashing for empty-metadata Verdicts and fail later for
    populated ones — this test pins both branches now.
    """

    def _build_verdict(self, *, metadata: dict[str, str]) -> object:
        return verdict_mod.Verdict(
            schema_version=verdict_mod.SCHEMA_VERSION,
            skill="audit-x",
            target="spx/path",
            overall=verdict_mod.Status.PASS,
            rows=(),
            children=(),
            metadata=metadata,
        )

    def test_empty_metadata_verdict_is_unhashable(self) -> None:
        v = self._build_verdict(metadata={})
        with pytest.raises(TypeError, match="unhashable"):
            hash(v)

    def test_populated_metadata_verdict_is_unhashable(self) -> None:
        v = self._build_verdict(metadata={"branch": "main"})
        with pytest.raises(TypeError, match="unhashable"):
            hash(v)

    def test_cannot_be_used_as_set_member(self) -> None:
        v = self._build_verdict(metadata={})
        with pytest.raises(TypeError, match="unhashable"):
            {v}  # noqa: B018 — expression itself is the assertion subject
