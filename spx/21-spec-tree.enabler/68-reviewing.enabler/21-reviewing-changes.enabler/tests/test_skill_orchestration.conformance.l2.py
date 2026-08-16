"""Conformance evidence for the review runner's caller-facing output.

Covers this clause in ``../reviewing-changes.md``: the live ``review-changes``
skill path never renders, summarizes, counts, or restates findings for the
caller — caller-facing output is the raw run token. The oracle is the journal
channel: ``finish`` conforms when its entire stdout is exactly the run token
the journal issued at ``open``, with nothing added for a review that raised a
finding and nothing added for a clean review.

The test is ``l2`` because it drives the runner as a subprocess against a
synthetic git repository and a fake ``spx`` journal.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    init_repo_with_branch,
    make_finding_dict,
    open_scoped_review_run,
    run_script,
    runner_env,
)


@pytest.mark.parametrize("finding_count", [0, 1], ids=["clean", "one-finding"])
def test_finish_stdout_is_exactly_the_journal_run_token(
    tmp_path: pathlib.Path, finding_count: int
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base_ref = init_repo_with_branch(repo)
    env, journal_path = runner_env(tmp_path, repo, base_ref)

    state_path = open_scoped_review_run(env, repo)
    for _ in range(finding_count):
        appended = run_script(
            REVIEW_RUN_SCRIPT,
            "append-finding",
            "--state",
            state_path,
            stdin=json.dumps(make_finding_dict(file="README.md", line=2)),
            env=env,
            cwd=repo,
        )
        assert appended.returncode == 0, appended.stderr
    finished = run_script(
        REVIEW_RUN_SCRIPT, "finish", "--state", state_path, env=env, cwd=repo
    )
    assert finished.returncode == 0, finished.stderr

    issued_token = json.loads(journal_path.read_text(encoding="utf-8"))["runToken"]
    assert finished.stdout == f"{issued_token}\n"
    assert finished.stderr == ""
