"""Scenario evidence for the dist-diff drift reporter.

Each test drives the reporter against a real temp git repo (L1: git plus tmp
dirs) provisioned by the ``dist_drift`` harness, asserting the report content and
the process exit code for the two states the reporter discriminates.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from outcomeeng.distribution.build import (
    FORMATTER_COMMAND_NAME,
    FORMATTER_FILE_GLOB,
    BuildError,
    _format_dist,
)
from outcomeeng.distribution.dist_diff import (
    DRIFT_REBUILD_NOTE,
    EXPECTED_PRECOMMIT_NOTE,
    dist_drift_report,
    main,
)
from outcomeeng_testing.harnesses.dist_drift import dist_drift_repo


def _carries_unified_diff(report: str) -> bool:
    """Return whether the report contains raw unified-diff markers.

    Two independent guards catch a regression that dumps a raw ``git diff``:
    hunk headers (``@@``) and diff body lines (a raw added or removed line
    starts with ``+`` or ``-``). The reporter's own entries are ``name-status``
    lines that start with a status letter and are indented, so a well-formed
    report trips neither guard — the ``startswith`` branch fires only on raw,
    unindented diff body content.
    """
    return "@@" in report or any(
        line.startswith(("+", "-")) for line in report.splitlines()
    )


def test_reports_expected_precommit_state_when_src_has_matching_edits() -> None:
    with dist_drift_repo() as repo:
        repo.drift_dist()
        repo.edit_src()

        report = dist_drift_report(cwd=repo.root)

        assert report is not None
        assert repo.dist_path.as_posix() in report
        assert EXPECTED_PRECOMMIT_NOTE in report
        assert DRIFT_REBUILD_NOTE not in report
        assert not _carries_unified_diff(report)
        assert main(cwd=repo.root) == 1


def test_reports_rebuild_remediation_when_src_is_clean() -> None:
    with dist_drift_repo() as repo:
        repo.drift_dist()

        report = dist_drift_report(cwd=repo.root)

        assert report is not None
        assert repo.dist_path.as_posix() in report
        assert DRIFT_REBUILD_NOTE in report
        assert EXPECTED_PRECOMMIT_NOTE not in report
        assert not _carries_unified_diff(report)
        assert main(cwd=repo.root) == 1


def test_reports_nothing_when_dist_in_sync() -> None:
    with dist_drift_repo() as repo:
        assert dist_drift_report(cwd=repo.root) is None
        assert main(cwd=repo.root) == 0


def test_format_dist_reports_missing_formatter_without_running_child(
    tmp_path: Path,
) -> None:
    runner_calls: list[tuple[str, ...]] = []

    def unavailable_formatter(command_name: str) -> str | None:
        assert command_name == FORMATTER_COMMAND_NAME
        return None

    def recording_runner(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        runner_calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    with pytest.raises(BuildError, match=FORMATTER_COMMAND_NAME):
        _format_dist(
            tmp_path,
            formatter_probe=unavailable_formatter,
            runner=recording_runner,
        )

    assert runner_calls == []


def test_format_dist_reports_formatter_failure(tmp_path: Path) -> None:
    formatter_path = "/usr/local/bin/dprint"
    diagnostic = "formatter failed"
    runner_calls: list[tuple[str, ...]] = []

    def formatter_probe(command_name: str) -> str | None:
        assert command_name == FORMATTER_COMMAND_NAME
        return formatter_path

    def failing_runner(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
        runner_calls.append(command)
        return subprocess.CompletedProcess(command, 1, stdout="", stderr=diagnostic)

    with pytest.raises(BuildError, match=diagnostic):
        _format_dist(tmp_path, formatter_probe=formatter_probe, runner=failing_runner)

    assert runner_calls == [
        (
            formatter_path,
            "fmt",
            "--allow-no-files",
            str(tmp_path / FORMATTER_FILE_GLOB),
        )
    ]
