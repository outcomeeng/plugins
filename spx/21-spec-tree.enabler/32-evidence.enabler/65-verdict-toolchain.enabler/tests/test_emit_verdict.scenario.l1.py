"""Scenario tests for the ``emit_verdict.py`` CLI.

Covers the Compliance MUST clauses on ``emit_verdict.py`` in
``../verdict-toolchain.md``:

- the three surface forms (``markdown``, ``markdown+json``, ``json-only``)
- the HTML-comment-delimited JSON block inside ``markdown+json``
- cell escaping for ``|``, ``\\``, and newline characters
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
JSON_BLOCK_BEGIN = "<!-- AUDIT_VERDICT_JSON_BEGIN -->"
JSON_BLOCK_END = "<!-- AUDIT_VERDICT_JSON_END -->"

VALID_VERDICT_DICT: dict[str, object] = {
    "schema_version": 1,
    "skill": "auditing-typescript",
    "target": "spx/path/to/node",
    "overall": "FAIL",
    "rows": [
        {"name": "scope", "status": "PASS", "findings": []},
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


def _run_emit(payload: dict[str, object], fmt: str) -> str:
    result = subprocess.run(
        [sys.executable, str(EMIT_SCRIPT), "--format", fmt],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


class TestJsonOnlyFormat:
    def test_output_is_valid_json_only(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "json-only")
        parsed = json.loads(out)
        assert parsed["overall"] == "FAIL"
        assert parsed["skill"] == "auditing-typescript"

    def test_no_markdown_carrier(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "json-only")
        assert JSON_BLOCK_BEGIN not in out
        assert "# Audit verdict" not in out


class TestMarkdownFormat:
    def test_contains_overall_line(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown")
        assert "**Overall:** FAIL" in out

    def test_contains_concerns_table(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown")
        assert "| Concern | Status | Findings |" in out
        assert "| scope | PASS | — |" in out
        assert "| evidence | FAIL | 1 |" in out

    def test_no_embedded_json_block(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown")
        assert JSON_BLOCK_BEGIN not in out
        assert JSON_BLOCK_END not in out

    def test_findings_section_lists_finding_details(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown")
        assert "f-001" in out
        assert "`src/foo.ts:42`" in out
        assert "`no-shared-bag`" in out
        assert "Shared constant bag declared." in out


class TestMarkdownJsonFormat:
    def test_contains_markdown_table(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown+json")
        assert "| Concern | Status | Findings |" in out

    def test_contains_delimited_json_block(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown+json")
        assert JSON_BLOCK_BEGIN in out
        assert JSON_BLOCK_END in out
        begin = out.index(JSON_BLOCK_BEGIN)
        end = out.index(JSON_BLOCK_END)
        assert begin < end

    def test_embedded_json_parses_back_to_input(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown+json")
        begin = out.index(JSON_BLOCK_BEGIN) + len(JSON_BLOCK_BEGIN)
        end = out.index(JSON_BLOCK_END)
        parsed = json.loads(out[begin:end].strip())
        assert parsed == VALID_VERDICT_DICT


class TestCellEscaping:
    def test_escapes_pipe_in_row_name(self) -> None:
        payload = json.loads(json.dumps(VALID_VERDICT_DICT))
        payload["rows"] = [{"name": "weird | name", "status": "PASS", "findings": []}]
        out = _run_emit(payload, "markdown")
        assert r"weird \| name" in out

    def test_escapes_backslash_in_row_name(self) -> None:
        payload = json.loads(json.dumps(VALID_VERDICT_DICT))
        payload["rows"] = [{"name": "path\\name", "status": "PASS", "findings": []}]
        out = _run_emit(payload, "markdown")
        assert r"path\\name" in out

    def test_escapes_newline_in_row_name(self) -> None:
        payload = json.loads(json.dumps(VALID_VERDICT_DICT))
        payload["rows"] = [{"name": "first\nsecond", "status": "PASS", "findings": []}]
        out = _run_emit(payload, "markdown")
        table_line = next(
            line for line in out.splitlines() if "first" in line and "PASS" in line
        )
        assert "\n" not in table_line


class TestExitCodes:
    def test_invalid_verdict_exits_non_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, str(EMIT_SCRIPT), "--format", "json-only"],
            input='{"schema_version": 1}',
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "invalid verdict" in result.stderr

    def test_malformed_json_exits_non_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, str(EMIT_SCRIPT), "--format", "json-only"],
            input="{not json",
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0


class TestFileIO:
    def test_reads_from_file_when_flag_given(self, tmp_path: pathlib.Path) -> None:
        payload_path = tmp_path / "verdict.json"
        payload_path.write_text(json.dumps(VALID_VERDICT_DICT))
        result = subprocess.run(
            [
                sys.executable,
                str(EMIT_SCRIPT),
                "--file",
                str(payload_path),
                "--format",
                "json-only",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        assert json.loads(result.stdout)["overall"] == "FAIL"

    def test_writes_to_output_path_when_flag_given(
        self, tmp_path: pathlib.Path
    ) -> None:
        output_path = tmp_path / "out.md"
        subprocess.run(
            [
                sys.executable,
                str(EMIT_SCRIPT),
                "--format",
                "json-only",
                "--output",
                str(output_path),
            ],
            input=json.dumps(VALID_VERDICT_DICT),
            capture_output=True,
            text=True,
            check=True,
        )
        assert output_path.exists()
        assert json.loads(output_path.read_text())["overall"] == "FAIL"
