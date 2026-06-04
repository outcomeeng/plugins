"""Scenario evidence for the dist-diff drift reporter.

Each test drives the reporter against a real temp git repo (L1: git plus tmp
dirs) provisioned by the ``dist_drift`` harness, asserting the report content and
the process exit code for the two states the reporter discriminates.
"""

from __future__ import annotations

from outcomeeng.distribution.dist_diff import (
    DRIFT_REBUILD_NOTE,
    EXPECTED_PRECOMMIT_NOTE,
    dist_drift_report,
    main,
)
from outcomeeng_testing.harnesses.dist_drift import dist_drift_repo


def _carries_unified_diff(report: str) -> bool:
    """Return whether the report contains raw unified-diff markers."""
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
