"""Compliance evidence for ``review_run.py start``'s resolution boundary.

``l1``: the shipped runner runs as a subprocess against a synthetic
repository whose origin is a real bare repository beside it, with the
journal routed at the fake ``spx`` the harness writes.
"""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    base_advanced_after_branch_repo,
    lagging_remote_tracking_repo,
    remote_base_oid,
    sever_origin_remote,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    run_script,
    runner_env,
)


def test_a_head_behind_the_fetched_base_is_refused_before_any_journal_opens(
    tmp_path: pathlib.Path,
) -> None:
    """The runner relays the shared refusal and opens no run.

    Removing the relay makes the shared resolver's error escape as a
    traceback with a different exit code, and the check moving after the
    journal open leaves a run recorded for a tree that cannot merge.
    """
    with base_advanced_after_branch_repo() as advanced:
        tip = remote_base_oid(advanced.repo, advanced.base_ref)
        env, journal_path = runner_env(
            tmp_path,
            advanced.repo,
            CHANGESET_SCOPE.remote_tracking_ref(advanced.base_ref),
        )

        started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=advanced.repo)

        assert started.returncode == CHANGESET_SCOPE.EXIT_STALE_BASE
        assert not started.stdout
        diagnostic = json.loads(started.stderr.strip().splitlines()[-1])
        assert diagnostic[CHANGESET_SCOPE.StaleBaseField.STATUS] == (
            CHANGESET_SCOPE.STALE_BASE_STATUS
        )
        assert diagnostic[CHANGESET_SCOPE.StaleBaseField.TIP] == tip
        assert not journal_path.exists()


def test_an_unfetchable_base_is_reported_as_a_diagnostic_line(
    tmp_path: pathlib.Path,
) -> None:
    """A failed fetch reaches stderr as git's own message, never a traceback.

    Moving the base resolution outside the runner's translating clause lets
    the process error escape as a traceback with no git message.
    """
    with base_advanced_after_branch_repo() as advanced:
        absent = sever_origin_remote(advanced.repo)
        env, journal_path = runner_env(
            tmp_path,
            advanced.repo,
            CHANGESET_SCOPE.remote_tracking_ref(advanced.base_ref),
        )

        started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=advanced.repo)

        assert started.returncode == 1
        assert not started.stdout
        assert len(started.stderr.strip().splitlines()) == 1
        assert absent in started.stderr
        assert "Traceback (most recent call last):" not in started.stderr
        assert not journal_path.exists()


def test_a_symbolic_origin_head_base_is_refused_against_the_remote_tip(
    tmp_path: pathlib.Path,
) -> None:
    """The base the wrapper agent exports resolves to the branch fetch updates.

    Fetching the bare ``HEAD`` writes only ``FETCH_HEAD``, so a comparison
    against the local symbolic ref would pass a head the remote has left
    behind.
    """
    with lagging_remote_tracking_repo() as lagging:
        remote_tip = remote_base_oid(lagging.repo, lagging.base_ref)
        env, journal_path = runner_env(
            tmp_path,
            lagging.repo,
            CHANGESET_SCOPE.remote_tracking_ref(CHANGESET_SCOPE.HEAD_REF),
        )

        started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=lagging.repo)

        assert started.returncode == CHANGESET_SCOPE.EXIT_STALE_BASE
        diagnostic = json.loads(started.stderr.strip().splitlines()[-1])
        assert diagnostic[CHANGESET_SCOPE.StaleBaseField.TIP] == remote_tip
        assert not journal_path.exists()
