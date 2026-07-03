"""Scenario evidence for the review-run inspection helper."""

from __future__ import annotations

import json
import os
import pathlib
import stat
import subprocess
from typing import Any

from outcomeeng_testing.harnesses.journal_projection import (
    RENDER_REVIEW_RUN_SCRIPT,
    load_journal_projection_module,
)

jp = load_journal_projection_module()

RUN_TOKEN = "2026-07-02_06-38-22-118-d7c71d2f5575"
NOW = "2026-07-02T06:38:22Z"


def _run_identity() -> Any:
    return jp.RunResult(
        target="changeset",
        scope_hash="abc123def456",
        branch_name="work/review-run-inspection-helper",
        branch_slug="work__review-run-inspection-helper",
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


def _completed_events(*, findings: tuple[Any, ...] = ()) -> list[dict]:
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
    data = completed["data"]
    data["review"] = {
        "blocking": sum(1 for item in findings if item.severity == jp.Severity.REJECT),
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
                "import pathlib",
                "import sys",
                "marker = pathlib.Path(os.environ['SPX_LIST_MARKER'])",
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
                "    '--limit',",
                "    '200',",
                "]",
                "if sys.argv[1:] == list_expected:",
                "    marker.write_text(os.environ.get('SPX_BRANCH_SLUG', ''), encoding='utf-8')",
                "    sys.stdout.write(os.environ.get('SPX_LIST_STDOUT', '[]'))",
                "    raise SystemExit(0)",
                "if sys.argv[1:] == expected and os.environ.get('SPX_DIRECT_NOT_FOUND') == '1':",
                "    sys.stderr.write('journal run not found; open the run before operating on it\\n')",
                "    raise SystemExit(1)",
                "if sys.argv[1:] == branch_expected and os.environ.get('SPX_REQUIRE_LIST_FOR_BRANCH_RENDER') == '1':",
                "    if not marker.exists() or marker.read_text(encoding='utf-8') != os.environ.get('SPX_BRANCH_SLUG', ''):",
                "        sys.stderr.write('branch render happened before journal list resolved the slug')",
                "        raise SystemExit(98)",
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
    branch_slug: str = "",
    require_list_for_branch_render: bool = False,
    pass_branch_slug: bool = False,
) -> subprocess.CompletedProcess[str]:
    _write_spx(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["EXPECTED_RUN_TOKEN"] = RUN_TOKEN
    env["SPX_LIST_MARKER"] = str(tmp_path / "listed-branch-slug")
    env["SPX_STDOUT"] = spx_stdout
    env["SPX_STDERR"] = spx_stderr
    env["SPX_EXIT_CODE"] = str(spx_exit_code)
    if direct_not_found:
        env["SPX_DIRECT_NOT_FOUND"] = "1"
    if require_list_for_branch_render:
        env["SPX_REQUIRE_LIST_FOR_BRANCH_RENDER"] = "1"
    if branch_slug != "":
        env["SPX_BRANCH_SLUG"] = branch_slug
        env["SPX_LIST_STDOUT"] = json.dumps(
            [{"runToken": RUN_TOKEN, "branchSlug": branch_slug}]
        )
    command = ["python3", str(RENDER_REVIEW_RUN_SCRIPT), RUN_TOKEN]
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


def test_run_token_resolves_branch_slug_from_journal_list(
    tmp_path: pathlib.Path,
) -> None:
    result = _run_helper(
        tmp_path,
        spx_stdout=json.dumps(_completed_events()),
        direct_not_found=True,
        branch_slug="head-b5180223",
        require_list_for_branch_render=True,
    )

    assert result.returncode == 0
    assert f"Review run: {RUN_TOKEN}" in result.stdout
    assert "Status: approved" in result.stdout


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


def test_invalid_run_token_is_rejected_before_spx_invocation(
    tmp_path: pathlib.Path,
) -> None:
    _write_spx(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["EXPECTED_RUN_TOKEN"] = RUN_TOKEN
    env["SPX_LIST_MARKER"] = str(tmp_path / "listed-branch-slug")

    result = subprocess.run(  # noqa: S603,S607
        ["python3", str(RENDER_REVIEW_RUN_SCRIPT), "../bad"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 1
    assert "run token must contain only ASCII letters" in result.stderr
    assert "unexpected spx arguments" not in result.stderr


def test_invalid_branch_slug_is_rejected_before_spx_invocation(
    tmp_path: pathlib.Path,
) -> None:
    _write_spx(tmp_path)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    env["EXPECTED_RUN_TOKEN"] = RUN_TOKEN
    env["SPX_LIST_MARKER"] = str(tmp_path / "listed-branch-slug")

    result = subprocess.run(  # noqa: S603,S607
        [
            "python3",
            str(RENDER_REVIEW_RUN_SCRIPT),
            RUN_TOKEN,
            "--branch-slug",
            "bad/slug",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 1
    assert "branch slug must contain only ASCII letters" in result.stderr
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
