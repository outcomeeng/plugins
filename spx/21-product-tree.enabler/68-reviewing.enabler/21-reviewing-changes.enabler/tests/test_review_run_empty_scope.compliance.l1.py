"""Compliance evidence for ``review_run.py start`` on a scope with no changed path.

``l1``: the shipped runner runs as a subprocess against a synthetic repository
whose origin is a real bare repository beside it, with the journal routed at the
fake ``spx`` the harness writes.
"""

from __future__ import annotations

import pathlib

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    empty_scope_repo,
    git_commit_oid,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    run_script,
    runner_env,
)


def test_a_scope_with_no_changed_path_opens_no_journal_and_names_both_commits(
    tmp_path: pathlib.Path,
) -> None:
    """The runner stops before opening a journal and names the commit ids.

    A runner that opens the journal for an empty scope seals a verdict over an
    empty diff and leaves a journal file; one that exits zero or prints run
    state fails the exit and stdout checks; one that omits either commit id
    fails the diagnostic check.
    """
    with empty_scope_repo() as empty:
        base_ref = CHANGESET_SCOPE.remote_tracking_ref(empty.base_ref)
        base_commit = git_commit_oid(empty.repo, base_ref)
        head_commit = git_commit_oid(empty.repo, CHANGESET_SCOPE.HEAD_REF)
        env, journal_path = runner_env(tmp_path, empty.repo, base_ref)

        started = run_script(
            REVIEW_RUN_SCRIPT,
            "start",
            "--checkout",
            str(empty.repo),
            env=env,
            cwd=empty.repo,
        )

        assert base_commit != head_commit
        assert started.returncode != 0
        assert not started.stdout
        assert len(started.stderr.strip().splitlines()) == 1
        assert base_commit in started.stderr
        assert head_commit in started.stderr
        assert "Traceback (most recent call last):" not in started.stderr
        assert not journal_path.exists()
