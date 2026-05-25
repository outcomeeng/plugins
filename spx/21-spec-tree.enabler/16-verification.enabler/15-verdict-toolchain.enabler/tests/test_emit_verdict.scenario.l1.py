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

from outcomeeng_testing.harnesses.verdict_toolchain import (
    EMIT_SCRIPT,
    JSON_BLOCK_BEGIN,
    JSON_BLOCK_END,
    run_script,
)

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
    "resolved": [],
    "reopened": [],
}


def _run_emit(payload: dict[str, object], fmt: str) -> str:
    return run_script(
        EMIT_SCRIPT,
        "--format",
        fmt,
        stdin=json.dumps(payload),
        check=True,
    ).stdout


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


RESOLVED_FINDING_DICT = {
    "id": "f-100",
    "file": "src/old.ts",
    "line": 7,
    "rule": "no-shared-bag",
    "severity": "INFO",
    "message": "Resolved by removing the shared bag.",
}

REOPENED_FINDING_DICT = {
    "id": "f-200",
    "file": "src/new.ts",
    "line": None,
    "rule": "no-shared-bag",
    "severity": "REJECT",
    "message": "Regression — shared bag re-introduced.",
}


class TestResolvedAndReopenedRendering:
    def test_resolved_section_omitted_when_empty(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown")
        assert "Resolved findings" not in out

    def test_reopened_section_omitted_when_empty(self) -> None:
        out = _run_emit(VALID_VERDICT_DICT, "markdown")
        assert "Reopened findings" not in out

    def test_resolved_section_renders_when_present(self) -> None:
        payload = {**VALID_VERDICT_DICT, "resolved": [RESOLVED_FINDING_DICT]}
        out = _run_emit(payload, "markdown")
        assert "## Resolved findings" in out
        assert "f-100" in out
        assert "`src/old.ts:7`" in out
        assert "Resolved by removing the shared bag." in out

    def test_reopened_section_renders_when_present(self) -> None:
        payload = {**VALID_VERDICT_DICT, "reopened": [REOPENED_FINDING_DICT]}
        out = _run_emit(payload, "markdown")
        assert "## Reopened findings" in out
        assert "f-200" in out
        assert "`src/new.ts`" in out
        assert "shared bag re-introduced." in out

    def test_both_sections_render_in_order(self) -> None:
        payload = {
            **VALID_VERDICT_DICT,
            "resolved": [RESOLVED_FINDING_DICT],
            "reopened": [REOPENED_FINDING_DICT],
        }
        out = _run_emit(payload, "markdown")
        resolved_idx = out.index("## Resolved findings")
        reopened_idx = out.index("## Reopened findings")
        assert resolved_idx < reopened_idx


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
        result = run_script(
            EMIT_SCRIPT,
            "--format",
            "json-only",
            stdin='{"schema_version": 1}',
        )
        assert result.returncode != 0
        assert "invalid verdict" in result.stderr

    def test_malformed_json_exits_non_zero(self) -> None:
        result = run_script(
            EMIT_SCRIPT,
            "--format",
            "json-only",
            stdin="{not json",
        )
        assert result.returncode != 0


class TestFileIO:
    def test_reads_from_file_when_flag_given(self, tmp_path: pathlib.Path) -> None:
        payload_path = tmp_path / "verdict.json"
        payload_path.write_text(json.dumps(VALID_VERDICT_DICT))
        result = run_script(
            EMIT_SCRIPT,
            "--file",
            str(payload_path),
            "--format",
            "json-only",
            check=True,
        )
        assert json.loads(result.stdout)["overall"] == "FAIL"

    def test_writes_to_output_path_when_flag_given(
        self, tmp_path: pathlib.Path
    ) -> None:
        output_path = tmp_path / "out.md"
        run_script(
            EMIT_SCRIPT,
            "--format",
            "json-only",
            "--output",
            str(output_path),
            stdin=json.dumps(VALID_VERDICT_DICT),
            check=True,
        )
        assert output_path.exists()
        assert json.loads(output_path.read_text())["overall"] == "FAIL"
