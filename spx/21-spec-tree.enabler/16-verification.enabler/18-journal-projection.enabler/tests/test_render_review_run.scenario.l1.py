"""Scenario evidence for the review-run inspection helper."""

from __future__ import annotations

import json
import os
import pathlib
import stat
import subprocess
from typing import Any

from outcomeeng_testing.harnesses.journal_projection import (
    INSPECT_REVIEW_RUN_SCRIPT,
    load_journal_projection_module,
    load_render_review_run_module,
)

jp = load_journal_projection_module()
render_review_run = load_render_review_run_module()

RUN_TOKEN = "2026-07-02_06-38-22-118-d7c71d2f5575"
NOW = "2026-07-02T06:38:22Z"


def _run_identity() -> Any:
    return jp.RunResult(
        target="changeset",
        scope_hash="abc123def456",
        branch_name="work/review-run-inspection-helper",
        branch_slug="work-review-run-inspection-helper-ddab1169",
        head_sha="1" * 40,
        base_ref="origin/main",
        base_sha="2" * 40,
        config_digest="cfg-abc123",
        participants=("review",),
        scope={
            "baseRef": "origin/main",
            "headRef": "HEAD",
            "changedFiles": ["a.py", "b.py"],
            "reviewInputSha256": "3" * 64,
        },
        started_at=NOW,
        completed_at="2026-07-02T06:38:30Z",
        output_paths=(),
    )


def _completed_events(
    *,
    findings: tuple[Any, ...] = (),
    include_review_summary: bool = True,
) -> list[dict]:
    run = _run_identity()
    events = [
        jp.scope_entered_event(run, now=NOW),
        jp.scope_advanced_event("a.py", now=NOW),
        jp.scope_advanced_event("b.py", now=NOW),
    ]
    for finding in findings:
        events.append(jp.finding_reported_event(finding, now=NOW))
    status = jp.terminal_status(jp.compute_overall(events))
    completed = jp.run_completed_event(run, status=status, now=NOW)
    if include_review_summary:
        data = completed["data"]
        data["review"] = {
            "blocking": sum(
                1 for item in findings if item.severity == jp.Severity.REJECT
            ),
            "debt": sum(1 for item in findings if item.severity == jp.Severity.WARNING),
            "overall": str(jp.compute_overall(events)),
        }
    events.append(completed)
    return events


def _write_spx(
    tmp_path: pathlib.Path,
) -> pathlib.Path:
    script = tmp_path / "spx"
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "import os",
                "import sys",
                "expected = [",
                "    'journal',",
                "    'render',",
                "    '--type',",
                "    'review',",
                "    '--run',",
                "    os.environ['EXPECTED_RUN_TOKEN'],",
                "]",
                "branch_expected = expected + [",
                "    '--branch-slug',",
                "    os.environ.get('SPX_BRANCH_SLUG', ''),",
                "]",
                "list_expected = [",
                "    'journal',",
                "    'list',",
                "    '--type',",
                "    'review',",
                "    '--sealed',",
                "    'sealed',",
                "    '--limit',",
                f"    {render_review_run.RECENT_RUN_LIST_LIMIT!r},",
                "]",
                "if sys.argv[1:] == expected and os.environ.get('SPX_DIRECT_NOT_FOUND') == '1':",
                "    sys.stderr.write('journal run not found; open the run before operating on it\\n')",
                "    raise SystemExit(1)",
                "if sys.argv[1:] == expected and os.environ.get('SPX_DIRECT_EXIT_CODE') is not None:",
                "    sys.stderr.write(os.environ.get('SPX_DIRECT_STDERR', ''))",
                "    raise SystemExit(int(os.environ['SPX_DIRECT_EXIT_CODE']))",
                "if sys.argv[1:] == list_expected:",
                "    sys.stdout.write(os.environ.get('SPX_LIST_STDOUT', '[]'))",
                "    sys.stderr.write(os.environ.get('SPX_LIST_STDERR', ''))",
                "    raise SystemExit(int(os.environ.get('SPX_LIST_EXIT_CODE', '0')))",
                "if sys.argv[1:] != expected and sys.argv[1:] != branch_expected:",
                "    sys.stderr.write('unexpected spx arguments: ' + repr(sys.argv[1:]))",
                "    raise SystemExit(97)",
                "sys.stdout.write(os.environ.get('SPX_STDOUT', ''))",
                "sys.stderr.write(os.environ.get('SPX_STDERR', ''))",
                "raise SystemExit(int(os.environ.get('SPX_EXIT_CODE', '0')))",
            ]
        ),
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _run_helper(
    tmp_path: pathlib.Path,
    *,
    spx_stdout: str,
    spx_stderr: str = "",
    spx_exit_code: int = 0,
    direct_not_found: bool = False,
    direct_stderr: str = "",
    direct_exit_code: int | None = None,
    branch_slug: str = "",
    pass_branch_slug: bool = False,
    list_stdout: str = "[]",
    list_stderr: str = "",
    list_exit_code: int = 0,
) -> subprocess.CompletedProcess[str]:
    _write_spx(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["EXPECTED_RUN_TOKEN"] = RUN_TOKEN
    env["SPX_STDOUT"] = spx_stdout
    env["SPX_STDERR"] = spx_stderr
    env["SPX_EXIT_CODE"] = str(spx_exit_code)
    if direct_not_found:
        env["SPX_DIRECT_NOT_FOUND"] = "1"
    if direct_exit_code is not None:
        env["SPX_DIRECT_EXIT_CODE"] = str(direct_exit_code)
        env["SPX_DIRECT_STDERR"] = direct_stderr
    if branch_slug != "":
        env["SPX_BRANCH_SLUG"] = branch_slug
    env["SPX_LIST_STDOUT"] = list_stdout
    env["SPX_LIST_STDERR"] = list_stderr
    env["SPX_LIST_EXIT_CODE"] = str(list_exit_code)
    command = ["python3", str(INSPECT_REVIEW_RUN_SCRIPT), RUN_TOKEN]
    if pass_branch_slug:
        command.extend(["--branch-slug", branch_slug])
    return subprocess.run(  # noqa: S603,S607
        command,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_approved_run_renders_compact_summary(tmp_path: pathlib.Path) -> None:
    result = _run_helper(tmp_path, spx_stdout=json.dumps(_completed_events()))

    assert result.returncode == 0
    assert f"Review run: {RUN_TOKEN}" in result.stdout
    assert "Status: approved" in result.stdout
    assert f"Head: {'1' * 40}" in result.stdout
    assert f"Base: origin/main @ {'2' * 40}" in result.stdout
    assert "Scope: 2 files, 2 examined" in result.stdout
    assert "Findings: 0 blocking, 0 debt" in result.stdout
    assert "# Verification run:" not in result.stdout


def test_run_with_findings_renders_shared_projection(tmp_path: pathlib.Path) -> None:
    finding = jp.Finding(
        file="a.py",
        line=12,
        rule="spx/example.md:AUDIT:1",
        severity=jp.Severity.REJECT,
        message="unsafe change",
        concern="security",
        action="close the gap",
    )
    result = _run_helper(
        tmp_path,
        spx_stdout=json.dumps(_completed_events(findings=(finding,))),
    )

    assert result.returncode == 0
    assert "Status: rejected" in result.stdout
    assert "Findings: 1 blocking, 0 debt" in result.stdout
    assert "# Verification run: changeset" in result.stdout
    assert "a.py:12" in result.stdout
    assert "unsafe change" in result.stdout
    assert "Required: close the gap" in result.stdout


def test_run_without_review_summary_counts_finding_events(
    tmp_path: pathlib.Path,
) -> None:
    blocking = jp.Finding(
        file="a.py",
        line=12,
        rule="spx/example.md:AUDIT:1",
        severity=jp.Severity.REJECT,
        message="unsafe change",
        concern="security",
        action="close the gap",
    )
    debt = jp.Finding(
        file="b.py",
        line=18,
        rule="spx/example.md:AUDIT:2",
        severity=jp.Severity.WARNING,
        message="coverage gap",
        concern="evidence",
        action="cover fallback counts",
    )

    result = _run_helper(
        tmp_path,
        spx_stdout=json.dumps(
            _completed_events(
                findings=(blocking, debt),
                include_review_summary=False,
            )
        ),
    )

    assert result.returncode == 0
    assert "Status: rejected" in result.stdout
    assert "Findings: 1 blocking, 1 debt" in result.stdout
    assert "a.py:12" in result.stdout
    assert "b.py:18" in result.stdout


def test_direct_render_failure_is_reported_without_branch_slug_retry(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout="",
        direct_stderr="run is outside current scope\n",
        direct_exit_code=2,
    )

    assert result.returncode == 2
    assert result.stderr == "run is outside current scope\n"


def test_explicit_branch_slug_renders_run_outside_current_scope(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout=json.dumps(_completed_events()),
        direct_not_found=True,
        branch_slug="head-b5180223",
        pass_branch_slug=True,
    )

    assert result.returncode == 0
    assert f"Review run: {RUN_TOKEN}" in result.stdout
    assert "Status: approved" in result.stdout


def test_explicit_branch_slug_accepts_state_store_slug(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout=json.dumps(_completed_events()),
        direct_not_found=True,
        branch_slug="work-review-run-inspection-helper-ddab1169",
        pass_branch_slug=True,
    )

    assert result.returncode == 0
    assert f"Review run: {RUN_TOKEN}" in result.stdout
    assert "Status: approved" in result.stdout


def test_missing_current_scope_run_uses_listed_branch_slug(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout=json.dumps(_completed_events()),
        direct_not_found=True,
        branch_slug="work-review-run-inspection-helper-ddab1169",
        list_stdout=json.dumps(
            [
                {
                    "runToken": RUN_TOKEN,
                    "branchSlug": "work-review-run-inspection-helper-ddab1169",
                    "sealed": True,
                }
            ]
        ),
    )

    assert result.returncode == 0
    assert f"Review run: {RUN_TOKEN}" in result.stdout
    assert "Status: approved" in result.stdout


def test_missing_current_scope_run_uses_listed_state_store_branch_slug(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout=json.dumps(_completed_events()),
        direct_not_found=True,
        branch_slug="task-test-audit-skill-governance-6e624d36",
        list_stdout=json.dumps(
            [
                {
                    "runToken": RUN_TOKEN,
                    "branchSlug": "task-test-audit-skill-governance-6e624d36",
                    "sealed": True,
                }
            ]
        ),
    )

    assert result.returncode == 0
    assert f"Review run: {RUN_TOKEN}" in result.stdout
    assert "Status: approved" in result.stdout


def test_missing_current_scope_run_without_list_match_reports_original_miss(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout="",
        direct_not_found=True,
        list_stdout=json.dumps([]),
    )

    assert result.returncode == 1
    assert "journal run not found" in result.stderr


def test_missing_current_scope_run_with_multiple_list_matches_reports_original_miss(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout="",
        direct_not_found=True,
        list_stdout=json.dumps(
            [
                {
                    "runToken": RUN_TOKEN,
                    "branchSlug": "work-review-run-inspection-helper-ddab1169",
                    "sealed": True,
                },
                {
                    "runToken": RUN_TOKEN,
                    "branchSlug": "head-b5180223",
                    "sealed": True,
                },
            ]
        ),
    )

    assert result.returncode == 1
    assert "journal run not found" in result.stderr


def test_list_failure_is_reported_after_current_scope_miss(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout="",
        direct_not_found=True,
        list_stderr="journal list sealed filter is not registered\n",
        list_exit_code=2,
    )

    assert result.returncode == 2
    assert result.stderr == "journal list sealed filter is not registered\n"


def test_malformed_list_output_is_reported_after_current_scope_miss(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout="",
        direct_not_found=True,
        list_stdout="not json",
    )

    assert result.returncode == 1
    assert "spx journal list returned invalid JSON" in result.stderr


def test_invalid_run_token_is_rejected_before_spx_invocation(
    tmp_path: pathlib.Path,
) -> None:
    _write_spx(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["EXPECTED_RUN_TOKEN"] = RUN_TOKEN

    result = subprocess.run(  # noqa: S603,S607
        ["python3", str(INSPECT_REVIEW_RUN_SCRIPT), "../bad"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 1
    assert "run token must contain only ASCII letters" in result.stderr
    assert "unexpected spx arguments" not in result.stderr


def test_incomplete_run_is_rejected(tmp_path: pathlib.Path) -> None:
    events = [jp.scope_entered_event(_run_identity(), now=NOW)]

    result = _run_helper(tmp_path, spx_stdout=json.dumps(events))

    assert result.returncode == 1
    assert f"review run {RUN_TOKEN} has no terminal completion event" in result.stderr


def test_spx_failure_is_reported(tmp_path: pathlib.Path) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout="",
        spx_stderr="render failed\n",
        spx_exit_code=7,
    )

    assert result.returncode == 7
    assert result.stderr == "render failed\n"


def test_invalid_json_is_reported(tmp_path: pathlib.Path) -> None:
    result = _run_helper(tmp_path, spx_stdout="{bad")

    assert result.returncode == 1
    assert "spx journal render returned invalid JSON" in result.stderr
