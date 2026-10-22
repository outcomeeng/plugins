"""Compliance: a pytest run bounds its temp files under one run root.

Each test runs a whole-payload pytest module in a scratch Git worktree that
holds stale run roots, a symlinked stale root pointing outside the worktree, and
neighbouring state, with a sandbox as the user temp folder. The run holds a
passing and a failing test.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng_testing.harnesses.run_temp_root import RUN_ROOTS_RELATIVE
from outcomeeng_testing.harnesses.run_temp_root_observation import (
    FAILING_TEST,
    PASSING_TEST,
    observe_pytest_run,
)

GIT_NOT_A_REPOSITORY_STATUS = 128


def test_run_root_holds_every_temp_file_and_is_removed(tmp_path: Path) -> None:
    observation = observe_pytest_run(tmp_path)
    first = observation.first_test
    run_root = Path(str(first["temp_variable"]))

    assert run_root.parent == observation.worktree / RUN_ROOTS_RELATIVE
    assert Path(str(first["default_tempdir"])) == run_root
    for created in observation.created.values():
        assert run_root in Path(created).parents
    assert not run_root.exists()
    assert observation.run_roots_after == ()


def test_git_ceiling_is_the_run_root(tmp_path: Path) -> None:
    observation = observe_pytest_run(tmp_path)
    first = observation.first_test

    assert first["git_ceiling"] == first["temp_variable"]
    assert first["git_probe_returncode"] == GIT_NOT_A_REPOSITORY_STATUS


def test_stale_roots_are_swept_without_leaving_the_worktree(tmp_path: Path) -> None:
    observation = observe_pytest_run(tmp_path)
    run_root = Path(str(observation.first_test["temp_variable"]))

    assert observation.first_test["run_roots_present"] == [run_root.name]
    assert observation.outside_sentinel_after == observation.outside_sentinel_before
    assert observation.neighbour_exists_after


def test_tmp_path_directories_do_not_outlive_their_tests(tmp_path: Path) -> None:
    observation = observe_pytest_run(tmp_path)

    assert observation.retained == {PASSING_TEST: False, FAILING_TEST: False}
