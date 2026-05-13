"""Scenario tests for the canonical verdict module.

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

import importlib.util
import json
import pathlib
import sys
from types import ModuleType

import pytest

SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[5]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "auditing"
    / "scripts"
)
VERDICT_MODULE = SCRIPTS_DIR / "verdict.py"


def _load_verdict() -> ModuleType:
    spec = importlib.util.spec_from_file_location("verdict", VERDICT_MODULE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {VERDICT_MODULE}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["verdict"] = module
    spec.loader.exec_module(module)
    return module


verdict_mod = _load_verdict()


VALID_VERDICT_DICT = {
    "schema_version": 1,
    "skill": "auditing-typescript",
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
        assert v.skill == "auditing-typescript"
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
