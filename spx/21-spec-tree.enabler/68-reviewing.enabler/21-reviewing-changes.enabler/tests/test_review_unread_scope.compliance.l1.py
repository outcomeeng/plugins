"""Compliance evidence for the unread rules of the review runner's finish verb.

``l1``: the shipped review runner runs as a subprocess against a synthetic
repository, with the journal routed at the fake ``spx`` the harness writes.
"""

from __future__ import annotations

import json
import pathlib

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    init_repo_with_branch,
    open_scoped_review_run,
    run_script,
    runner_env,
)

jp = load_journal_projection_module()


def _events(journal_path: pathlib.Path) -> list[dict]:
    return json.loads(journal_path.read_text(encoding="utf-8"))["events"]


def test_a_file_marked_unread_at_finish_seals_the_run_failed_and_is_named(
    tmp_path: pathlib.Path,
) -> None:
    """The terminal event of a run with an unread file carries failed and the file.

    A runner that seals approved, or omits the unread file from the terminal
    event, fails this check.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    env, journal_path = runner_env(tmp_path, repo, init_repo_with_branch(repo))
    started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=repo)
    assert started.returncode == 0, started.stderr
    state = json.loads(started.stdout)["statePath"]
    unread = json.loads(pathlib.Path(state).read_text(encoding="utf-8"))["metadata"][
        "scope"
    ]["changedFiles"]

    finished = run_script(
        REVIEW_RUN_SCRIPT,
        "finish",
        "--state",
        state,
        *[arg for unit in unread for arg in ("--unread", unit)],
        env=env,
        cwd=repo,
    )

    assert finished.returncode == 0, finished.stderr
    terminal = _events(journal_path)[-1]
    assert terminal["data"][jp.RUN_STATE_STATUS] == str(jp.JournalRunStatus.FAILED)
    for unit in unread:
        assert unit in json.dumps(terminal["data"])


def test_a_file_both_read_and_marked_unread_is_refused_at_finish(
    tmp_path: pathlib.Path,
) -> None:
    """A unit with a scope-advanced event cannot also be declared unread.

    A runner that seals such a run accepts a mark that contradicts the
    recorded reading and fails this check.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    env, journal_path = runner_env(tmp_path, repo, init_repo_with_branch(repo))
    state = open_scoped_review_run(env, repo)
    advanced = json.loads(pathlib.Path(state).read_text(encoding="utf-8"))

    finished = run_script(
        REVIEW_RUN_SCRIPT,
        "finish",
        "--state",
        state,
        "--unread",
        advanced["metadata"]["scope"]["changedFiles"][0],
        env=env,
        cwd=repo,
    )

    assert finished.returncode != 0
    assert all(event["type"] != jp.RUN_COMPLETED for event in _events(journal_path))


def test_a_file_neither_read_nor_marked_unread_is_refused_at_finish(
    tmp_path: pathlib.Path,
) -> None:
    """A run cannot seal while a changed file carries no reading and no unread mark.

    A runner that seals such a run fails this check.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    env, journal_path = runner_env(tmp_path, repo, init_repo_with_branch(repo))
    started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=repo)
    assert started.returncode == 0, started.stderr

    finished = run_script(
        REVIEW_RUN_SCRIPT,
        "finish",
        "--state",
        json.loads(started.stdout)["statePath"],
        env=env,
        cwd=repo,
    )

    assert finished.returncode != 0
    assert all(event["type"] != jp.RUN_COMPLETED for event in _events(journal_path))
