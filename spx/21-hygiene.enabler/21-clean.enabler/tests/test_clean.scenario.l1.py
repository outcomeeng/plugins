"""Level-1 scenario evidence for workspace cleanup.

Covers the scenario assertions in `clean.md`: run from a directory nested in
a repository holding the running interpreter's environment, with neither the
root nor the environment handed to it, `clean` records an argv that omits
that environment and runs in the repository root it found, a Git dry run
over the generated pathspecs would remove the
other ignored cache and nothing else, the runner's exit code is propagated to
the caller, and a repository whose every top-level path is protected invokes
no runner. Root resolution from a directory with no repository metadata up to
the search ceiling returns that directory, and a ceiling below a repository
stops the search before it.
"""

from __future__ import annotations

import os
from pathlib import Path

from outcomeeng.hygiene.clean import (
    CLEAN_BASE_ARGV,
    build_clean_argv,
    clean,
    find_repository_root,
)
from outcomeeng_testing.harnesses.clean import (
    GIT_END_OF_OPTIONS,
    IGNORED_CACHE_DIR,
    IGNORED_PYTHON_ENV_DIR,
    EnvironmentPlacement,
    RecordingRunner,
    create_clean_repo,
    create_directory_without_repository,
    observe_dry_run_removals,
    working_directory_below_root,
)


def test_clean_omits_active_environment_from_pathspecs(tmp_path: Path) -> None:
    repo = create_clean_repo(
        tmp_path,
        environment=EnvironmentPlacement.RUNNING_INTERPRETER,
    )
    runner = RecordingRunner()

    with working_directory_below_root(repo):
        exit_code = clean(runner=runner)

    assert exit_code == os.EX_OK
    assert len(runner.calls) == 1
    assert runner.calls[0].cwd == repo.root
    base_length = len(CLEAN_BASE_ARGV)
    assert runner.calls[0].argv[:base_length] == CLEAN_BASE_ARGV
    assert runner.calls[0].argv[base_length] == GIT_END_OF_OPTIONS
    assert IGNORED_CACHE_DIR in runner.calls[0].argv
    assert IGNORED_PYTHON_ENV_DIR not in runner.calls[0].argv


def test_git_dry_run_preserves_session_store_and_active_environment(
    tmp_path: Path,
) -> None:
    repo = create_clean_repo(tmp_path)

    argv = build_clean_argv(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    removals = observe_dry_run_removals(repo=repo, argv=argv)

    assert removals == {IGNORED_CACHE_DIR}


def test_clean_propagates_runner_exit_code(tmp_path: Path) -> None:
    repo = create_clean_repo(tmp_path)
    runner = RecordingRunner.failing()

    exit_code = clean(
        runner=runner,
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert exit_code != os.EX_OK
    assert exit_code == runner.exit_code


def test_clean_noops_when_every_top_level_path_is_protected(tmp_path: Path) -> None:
    repo = create_clean_repo(tmp_path, include_cache=False)
    runner = RecordingRunner()

    exit_code = clean(
        runner=runner,
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert exit_code == os.EX_OK
    assert runner.calls == []


def test_root_resolution_falls_back_to_start_without_metadata(
    tmp_path: Path,
) -> None:
    start = create_directory_without_repository(tmp_path)

    root = find_repository_root(start, ceiling=tmp_path)

    assert root == start


def test_root_resolution_stops_at_the_search_ceiling(tmp_path: Path) -> None:
    repo = create_clean_repo(tmp_path)
    ceiling = repo.ignored_cache

    root = find_repository_root(ceiling, ceiling=ceiling)

    assert root == ceiling
