"""Compliance evidence for the checkout root ``review_run.py`` receives.

``l2``: the shipped runner runs as a subprocess against synthetic git
repositories under ``tmp_path``, with the journal routed at the fake ``spx``
the harness writes, which records the working directory of each command.
"""

from __future__ import annotations

import json
import os
import pathlib

import pytest

from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    init_work_branch_repo,
    load_review_run_module,
    make_finding_dict,
    read_fake_journal,
    run_script,
    runner_env,
)

review_run = load_review_run_module()

CHANGED_FILE = "sample.txt"
BASE_BRANCH = "main"


def test_the_run_state_holds_the_checkout_root_and_every_journal_command_runs_there(
    tmp_path: pathlib.Path,
) -> None:
    target = tmp_path / "target"
    decoy = tmp_path / "decoy"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    init_work_branch_repo(target, "target edit")
    init_work_branch_repo(decoy, "decoy edit")
    outside = tmp_path / "outside"
    outside.mkdir()
    env, journal_path = runner_env(outside, target, BASE_BRANCH)

    started = run_script(
        REVIEW_RUN_SCRIPT, "start", "--checkout", str(target), env=env, cwd=elsewhere
    )
    assert started.returncode == 0, started.stderr
    state_path = str(json.loads(started.stdout)[review_run.START_STATE_PATH])
    state = json.loads(pathlib.Path(state_path).read_text(encoding="utf-8"))
    verbs = (
        (("append-scope", "--state", state_path, CHANGED_FILE), None, decoy),
        (
            ("append-finding", "--state", state_path),
            json.dumps(make_finding_dict(file=CHANGED_FILE, line=1)),
            elsewhere,
        ),
        (("finish", "--state", state_path), None, decoy),
    )
    for args, stdin, cwd in verbs:
        result = run_script(REVIEW_RUN_SCRIPT, *args, stdin=stdin, env=env, cwd=cwd)
        assert result.returncode == 0, result.stderr
    journal = read_fake_journal(journal_path)

    assert state[review_run.CHECKOUT_ROOT_KEY] == str(target)
    assert journal.commands == [
        "open",
        "append",
        "append",
        "append",
        "read",
        "append",
        "seal",
    ]
    assert len(journal.cwds) == len(journal.commands)
    assert {os.path.realpath(cwd) for cwd in journal.cwds} == {os.path.realpath(target)}


def _refusal_cases(tmp_path: pathlib.Path) -> list[tuple[str, tuple[str, ...], str]]:
    """Each start invocation whose --checkout names no checkout root, with its value."""
    target = tmp_path / "target"
    init_work_branch_repo(target, "target edit")
    subdirectory = target / "nested"
    subdirectory.mkdir()
    no_repository = tmp_path / "plain"
    no_repository.mkdir()
    return [
        ("absent", (), "None"),
        ("relative", ("--checkout", "target"), "'target'"),
        ("no-repository", ("--checkout", str(no_repository)), str(no_repository)),
        ("subdirectory", ("--checkout", str(subdirectory)), str(subdirectory)),
        ("missing", ("--checkout", str(tmp_path / "gone")), str(tmp_path / "gone")),
    ]


@pytest.mark.parametrize(
    "case",
    ["absent", "relative", "no-repository", "subdirectory", "missing"],
)
def test_start_refuses_a_checkout_that_names_no_repository_checkout(
    tmp_path: pathlib.Path, case: str
) -> None:
    cases = {name: (args, value) for name, args, value in _refusal_cases(tmp_path)}
    args, value = cases[case]
    target = tmp_path / "target"
    outside = tmp_path / "outside"
    outside.mkdir()
    env, journal_path = runner_env(outside, target, BASE_BRANCH)
    temp_root = tmp_path / "temp-root"
    temp_root.mkdir()
    env["TMPDIR"] = str(temp_root)

    refused = run_script(REVIEW_RUN_SCRIPT, "start", *args, env=env, cwd=tmp_path)

    lines = refused.stderr.splitlines()
    assert refused.returncode != 0
    assert len(lines) == 1, refused.stderr
    assert value in lines[0], refused.stderr
    assert refused.stdout == ""
    assert list(temp_root.iterdir()) == []
    assert not journal_path.exists()
