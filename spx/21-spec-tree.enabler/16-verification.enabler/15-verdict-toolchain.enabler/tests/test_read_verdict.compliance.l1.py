"""Compliance tests for the ``read_verdict.py`` CLI.

Covers the Compliance MUST clauses on ``read_verdict.py`` in
``../verdict-toolchain.md``:

- extracts JSON from json-only input
- extracts JSON from markdown+json (the HTML-comment-delimited block)
- rejects markdown-only input with a non-zero exit
- emits a markdown+json verdict and parses it back to the same JSON
"""

from __future__ import annotations

import json
import subprocess

from outcomeeng_testing.harnesses.verdict_toolchain import (
    EMIT_SCRIPT,
    JSON_BLOCK_BEGIN,
    JSON_BLOCK_END,
    READ_SCRIPT,
    run_script,
)

VALID_VERDICT_DICT: dict[str, object] = {
    "schema_version": 1,
    "skill": "audit-typescript",
    "target": "spx/path",
    "overall": "PASS",
    "rows": [{"name": "scope", "status": "PASS", "findings": []}],
    "children": [],
    "metadata": {"branch": "main"},
    "resolved": [],
    "reopened": [],
}


def _run_read(text: str) -> subprocess.CompletedProcess[str]:
    return run_script(READ_SCRIPT, stdin=text)


def _emit(payload: dict[str, object], fmt: str) -> str:
    return run_script(
        EMIT_SCRIPT,
        "--format",
        fmt,
        stdin=json.dumps(payload),
        check=True,
    ).stdout


class TestJsonOnlyExtraction:
    def test_returns_input_when_json_only(self) -> None:
        result = _run_read(json.dumps(VALID_VERDICT_DICT))
        assert result.returncode == 0
        assert json.loads(result.stdout) == VALID_VERDICT_DICT

    def test_tolerates_surrounding_whitespace(self) -> None:
        result = _run_read("\n  " + json.dumps(VALID_VERDICT_DICT) + "\n\n")
        assert result.returncode == 0


class TestMarkdownJsonExtraction:
    def test_extracts_block_from_carrier(self) -> None:
        carrier = _emit(VALID_VERDICT_DICT, "markdown+json")
        result = _run_read(carrier)
        assert result.returncode == 0
        assert json.loads(result.stdout) == VALID_VERDICT_DICT

    def test_extracts_block_when_text_surrounds_carrier(self) -> None:
        carrier = _emit(VALID_VERDICT_DICT, "markdown+json")
        wrapped = (
            "Some surrounding PR-comment text.\n\n"
            + carrier
            + "\nMore trailing text.\n"
        )
        result = _run_read(wrapped)
        assert result.returncode == 0
        assert json.loads(result.stdout) == VALID_VERDICT_DICT


class TestMarkdownOnlyRejected:
    def test_markdown_without_block_fails(self) -> None:
        markdown_only = _emit(VALID_VERDICT_DICT, "markdown")
        result = _run_read(markdown_only)
        assert result.returncode != 0
        assert "no JSON payload found" in result.stderr

    def test_random_text_fails(self) -> None:
        result = _run_read("This is not a verdict.\n")
        assert result.returncode != 0


class TestRoundTrip:
    def test_emit_then_read_preserves_payload(self) -> None:
        carrier = _emit(VALID_VERDICT_DICT, "markdown+json")
        result = _run_read(carrier)
        assert result.returncode == 0
        assert json.loads(result.stdout) == VALID_VERDICT_DICT


class TestSchemaViolations:
    def test_extracted_payload_with_invalid_schema_fails(self) -> None:
        bad = {"schema_version": 1, "skill": "x"}
        result = _run_read(json.dumps(bad))
        assert result.returncode != 0
        assert "invalid verdict" in result.stderr


class TestPartialDelimiters:
    """Coverage for the three malformed-delimiter cases in ``read_verdict``.

    The script handles each partial / reversed delimiter pattern with its
    own error message; pinning those messages in tests locks the public
    error contract so downstream tooling can match on them.
    """

    def test_begin_only_fails_with_no_closing_delimiter_message(self) -> None:
        text = (
            "Some carrier prose.\n\n" + JSON_BLOCK_BEGIN + '\n{"schema_version": 1}\n'
        )
        result = _run_read(text)
        assert result.returncode != 0
        assert JSON_BLOCK_BEGIN in result.stderr
        assert JSON_BLOCK_END in result.stderr
        assert "no closing" in result.stderr

    def test_end_only_fails_with_no_opening_delimiter_message(self) -> None:
        text = (
            "Some carrier prose.\n\n"
            + '{"schema_version": 1}\n'
            + JSON_BLOCK_END
            + "\n"
        )
        result = _run_read(text)
        assert result.returncode != 0
        assert JSON_BLOCK_END in result.stderr
        assert JSON_BLOCK_BEGIN in result.stderr
        assert "no opening" in result.stderr

    def test_reversed_delimiters_fail_with_out_of_order_message(self) -> None:
        # END marker appears before BEGIN — a malformed carrier the script
        # must reject rather than silently extracting whatever sits between
        # them in the wrong order.
        text = (
            "Some carrier prose.\n\n"
            + JSON_BLOCK_END
            + '\n{"schema_version": 1}\n'
            + JSON_BLOCK_BEGIN
            + "\n"
        )
        result = _run_read(text)
        assert result.returncode != 0
        assert "out of order" in result.stderr or "before" in result.stderr
        assert JSON_BLOCK_BEGIN in result.stderr
        assert JSON_BLOCK_END in result.stderr
