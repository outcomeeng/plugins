"""Scenario tests for the ``validate_review_result.py`` CLI arbiter.

Covers these clauses in ``../reviewing-changes.md``:

Scenarios
- Given a JSON document conforming to the review-result schema on
  stdin or via ``--file``, ``validate_review_result.py`` exits 0.
- Given a JSON document missing a required key,
  ``validate_review_result.py`` exits non-zero with a structured error
  message naming the missing key.
- Given a JSON document with an unknown ``severity`` or ``concern``
  value, ``validate_review_result.py`` exits non-zero with a structured
  error message naming the unknown value and the allowed set.

Compliance (subset)
- ``validate_review_result.py`` accepts JSON on stdin or via ``--file``
  and pipes it through ``review_result.parse_json`` — the CLI is the
  arbiter the wrapper agent invokes to validate every result it emits.
"""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.harnesses.reviewing_changes import (
    FIXTURE_RULE_CITATION,
    make_review_result_dict,
    run_validate_review_result_in_process,
)


class TestConformingDocument:
    """A conforming document exits 0 on both stdin and ``--file`` paths."""

    def test_conforming_via_stdin_exits_zero(self) -> None:
        payload = json.dumps(make_review_result_dict())
        result = run_validate_review_result_in_process(stdin=payload)
        assert result.returncode == 0, result.stderr

    def test_conforming_via_file_flag_exits_zero(self, tmp_path: pathlib.Path) -> None:
        payload_path = tmp_path / "review.json"
        payload_path.write_text(json.dumps(make_review_result_dict()), encoding="utf-8")
        result = run_validate_review_result_in_process("--file", str(payload_path))
        assert result.returncode == 0, result.stderr


class TestMissingKeyRejection:
    """A document missing a required key exits non-zero and names the key."""

    def test_missing_summary_key_exits_nonzero_naming_the_key(self) -> None:
        document = make_review_result_dict()
        del document["summary"]
        result = run_validate_review_result_in_process(stdin=json.dumps(document))
        assert result.returncode != 0
        assert "summary" in result.stderr

    def test_missing_findings_key_exits_nonzero_naming_the_key(self) -> None:
        document = make_review_result_dict()
        del document["findings"]
        result = run_validate_review_result_in_process(stdin=json.dumps(document))
        assert result.returncode != 0
        assert "findings" in result.stderr


class TestUnknownEnumValueRejection:
    """Unknown wire values exit non-zero with the value and allowed set."""

    def test_unknown_severity_exits_nonzero_naming_value_and_allowed_set(
        self,
    ) -> None:
        bad_finding = {
            "id": "F-001",
            "concern": "consistency",
            "severity": "blocker",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "m",
            "action": "a",
        }
        document = make_review_result_dict(findings=[bad_finding])
        result = run_validate_review_result_in_process(stdin=json.dumps(document))
        assert result.returncode != 0
        assert "blocker" in result.stderr
        assert "blocking" in result.stderr

    def test_unknown_concern_exits_nonzero_naming_value_and_allowed_set(
        self,
    ) -> None:
        bad_finding = {
            "id": "F-001",
            "concern": "marketing",
            "severity": "debt",
            "file": "x.py",
            "line": 1,
            "rule": FIXTURE_RULE_CITATION,
            "message": "m",
            "action": "a",
        }
        document = make_review_result_dict(findings=[bad_finding])
        result = run_validate_review_result_in_process(stdin=json.dumps(document))
        assert result.returncode != 0
        assert "marketing" in result.stderr
        assert "consistency" in result.stderr


class TestMalformedJsonRejection:
    """Malformed JSON exits non-zero with a parser-derived diagnostic."""

    def test_malformed_json_exits_nonzero(self) -> None:
        result = run_validate_review_result_in_process(stdin="{not json")
        assert result.returncode != 0
        assert result.stderr.strip() != ""
