"""Scenario evidence for the head ``review_run.py start`` records.

``l1``: the shipped runner runs as a subprocess against a synthetic repository
whose origin is a real bare repository beside it, with the journal routed at the
fake ``spx`` the harness writes. ``FETCH_HEAD`` is written by a real
``git fetch`` of the pull-request ref.
"""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    FETCH_HEAD_REF,
    pull_request_head_repo,
)
from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    load_compute_diff_module,
    load_review_run_module,
    run_script,
    runner_env,
)

jp = load_journal_projection_module()
compute_diff = load_compute_diff_module()
review_run = load_review_run_module()


def test_a_pull_request_head_survives_the_base_fetch_the_runner_makes(
    tmp_path: pathlib.Path,
) -> None:
    """The run records the pull-request head commit and exactly its paths.

    The runner's base fetch rewrites ``FETCH_HEAD`` to the base tip. A runner
    that reads the head ref by name after that fetch records the base tip as
    the head and an empty changed-file set.
    """
    with pull_request_head_repo() as pull_request:
        env, _journal_path = runner_env(
            tmp_path,
            pull_request.repo,
            CHANGESET_SCOPE.remote_tracking_ref(pull_request.base_ref),
        )
        env[str(compute_diff.ENV_HEAD_REF)] = FETCH_HEAD_REF

        started = run_script(
            REVIEW_RUN_SCRIPT,
            "start",
            "--checkout",
            str(pull_request.repo),
            env=env,
            cwd=pull_request.repo,
        )

        assert started.returncode == 0, started.stderr
        run_state = json.loads(started.stdout)
        state = json.loads(
            pathlib.Path(run_state[review_run.START_STATE_PATH]).read_text(
                encoding="utf-8"
            )
        )
        recorded_head = state[review_run.STATE_METADATA][jp.RUN_STATE_HEAD_SHA]
        assert recorded_head == pull_request.pull_request_head
        assert run_state[review_run.CHANGED_FILES_KEY] == [
            pull_request.pull_request_file
        ]
