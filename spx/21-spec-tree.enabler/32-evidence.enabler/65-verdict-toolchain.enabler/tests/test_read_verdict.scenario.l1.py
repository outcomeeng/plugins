"""Scenario tests for the ``read_verdict.py`` CLI.

Covers the Compliance MUST clauses on ``read_verdict.py`` in
``../verdict-toolchain.md``:

- extracts JSON from json-only input
- extracts JSON from markdown+json (the HTML-comment-delimited block)
- rejects markdown-only input with a non-zero exit
- emits a markdown+json verdict and parses it back to the same JSON
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[5]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "auditing"
    / "scripts"
)
EMIT_SCRIPT = SCRIPTS_DIR / "emit_verdict.py"
READ_SCRIPT = SCRIPTS_DIR / "read_verdict.py"
JSON_BLOCK_BEGIN = "<!-- AUDIT_VERDICT_JSON_BEGIN -->"
JSON_BLOCK_END = "<!-- AUDIT_VERDICT_JSON_END -->"

VALID_VERDICT_DICT: dict[str, object] = {
    "schema_version": 1,
    "skill": "auditing-typescript",
    "target": "spx/path",
    "overall": "PASS",
    "rows": [{"name": "scope", "status": "PASS", "findings": []}],
    "children": [],
    "metadata": {"branch": "main"},
}


def _run_read(text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(READ_SCRIPT)],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )


def _emit(payload: dict[str, object], fmt: str) -> str:
    result = subprocess.run(
        [sys.executable, str(EMIT_SCRIPT), "--format", fmt],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


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
