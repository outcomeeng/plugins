"""Scenario evidence for the checkout a review run reads.

``l2``: the shipped runner runs as a subprocess against synthetic git
repositories under ``tmp_path``, with the journal routed at the fake ``spx``
the harness writes, which records the working directory of each command.
"""

from __future__ import annotations

import json
import os
import pathlib

from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    init_work_branch_repo,
    load_review_run_module,
    make_finding_dict,
    read_fake_journal,
    run_git,
    run_script,
    runner_env,
)

jp = load_journal_projection_module()
review_run = load_review_run_module()

TARGET_EDIT = "target edit"
DECOY_EDIT = "decoy edit"
CHANGED_FILE = "sample.txt"
BASE_BRANCH = "main"
WORK_BRANCH = "work"


def _start(
    env: dict[str, str], checkout: pathlib.Path, cwd: pathlib.Path
) -> tuple[str, dict[str, object], str]:
    """Start a run for ``checkout`` from ``cwd``; return its state path, state and diff."""
    started = run_script(
        REVIEW_RUN_SCRIPT, "start", "--checkout", str(checkout), env=env, cwd=cwd
    )
    assert started.returncode == 0, started.stderr
    payload = json.loads(started.stdout)
    state_path = str(payload[review_run.START_STATE_PATH])
    state = json.loads(pathlib.Path(state_path).read_text(encoding="utf-8"))
    diff = pathlib.Path(payload[review_run.START_DIFF_PATH]).read_text(encoding="utf-8")
    return state_path, state, diff


def _verb(
    env: dict[str, str],
    cwd: pathlib.Path,
    *args: str,
    stdin: str | None = None,
) -> None:
    result = run_script(REVIEW_RUN_SCRIPT, *args, stdin=stdin, env=env, cwd=cwd)
    assert result.returncode == 0, result.stderr


def _commit(repo: pathlib.Path, ref: str) -> str:
    return run_git("rev-parse", ref, cwd=repo).stdout.strip()


def test_a_run_reads_the_checkout_it_names_from_any_working_directory(
    tmp_path: pathlib.Path,
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    target = scratch / "target"
    decoy = scratch / "decoy"
    elsewhere = scratch / "elsewhere"
    elsewhere.mkdir()
    init_work_branch_repo(target, TARGET_EDIT)
    init_work_branch_repo(decoy, DECOY_EDIT)
    outside = tmp_path / "outside"
    outside.mkdir()
    env, journal_path = runner_env(outside, target, BASE_BRANCH)

    state_path, state, diff = _start(env, target, elsewhere)
    _verb(env, decoy, "append-scope", "--state", state_path, CHANGED_FILE)
    _verb(
        env,
        elsewhere,
        "append-finding",
        "--state",
        state_path,
        stdin=json.dumps(make_finding_dict(file=CHANGED_FILE, line=1)),
    )
    _verb(env, decoy, "finish", "--state", state_path)
    journal = read_fake_journal(journal_path)

    inside = tmp_path / "inside"
    inside.mkdir()
    inside_env, _inside_journal = runner_env(inside, target, BASE_BRANCH)
    inside_state_path, inside_state, _inside_diff = _start(inside_env, target, target)
    _verb(
        inside_env, target, "append-scope", "--state", inside_state_path, CHANGED_FILE
    )
    _verb(inside_env, target, "finish", "--state", inside_state_path)

    metadata = state[review_run.STATE_METADATA]
    inside_metadata = inside_state[review_run.STATE_METADATA]
    assert isinstance(metadata, dict)
    assert isinstance(inside_metadata, dict)
    scope = metadata[jp.RUN_STATE_SCOPE]
    inside_scope = inside_metadata[jp.RUN_STATE_SCOPE]
    assert metadata[jp.RUN_STATE_BASE_SHA] == _commit(target, BASE_BRANCH)
    assert metadata[jp.RUN_STATE_HEAD_SHA] == _commit(target, WORK_BRANCH)
    assert metadata[jp.RUN_STATE_BRANCH_NAME] == WORK_BRANCH
    assert TARGET_EDIT in diff
    assert DECOY_EDIT not in diff
    assert (
        scope[review_run.SCOPE_REVIEW_INPUT_SHA256]
        == inside_scope[review_run.SCOPE_REVIEW_INPUT_SHA256]
    )
    assert (
        scope[review_run.CHANGED_FILES_KEY]
        == inside_scope[review_run.CHANGED_FILES_KEY]
    )
    assert journal.commands.count("open") == 1
    assert journal.sealed
    assert {os.path.realpath(cwd) for cwd in journal.cwds} == {os.path.realpath(target)}
    assert not (decoy / ".spx").exists()
