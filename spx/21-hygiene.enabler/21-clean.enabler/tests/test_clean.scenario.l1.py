"""Level-1 scenario evidence for workspace cleanup.

Covers the scenario assertions in `clean.md`: the recorded argv omits an
active in-repository Python environment from generated pathspecs and runs in
the root those pathspecs came from, a Git dry run over them would remove the
other ignored cache and nothing else, the runner's exit code is propagated to
the caller, and a repository whose every top-level path is protected invokes
no runner.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.hygiene.clean import (
    CLEAN_BASE_ARGV,
    PATHSPEC_SEPARATOR,
    SUCCESS_EXIT_CODE,
    build_clean_argv,
    clean,
)
from outcomeeng_testing.harnesses.clean import (
    IGNORED_CACHE_DIR,
    IGNORED_PYTHON_ENV_DIR,
    RecordingRunner,
    create_clean_repo,
    observe_dry_run_removals,
)


def test_clean_omits_active_environment_from_pathspecs(tmp_path: Path) -> None:
    repo = create_clean_repo(tmp_path)
    runner = RecordingRunner()

    exit_code = clean(
        runner=runner,
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert exit_code == SUCCESS_EXIT_CODE
    assert len(runner.calls) == 1
    assert runner.calls[0].cwd == repo.root
    assert runner.calls[0].argv[:4] == (*CLEAN_BASE_ARGV, PATHSPEC_SEPARATOR)
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
    runner = RecordingRunner(exit_code=3)

    exit_code = clean(
        runner=runner,
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert exit_code == 3


def test_clean_noops_when_every_top_level_path_is_protected(tmp_path: Path) -> None:
    repo = create_clean_repo(tmp_path, include_cache=False)
    runner = RecordingRunner()

    exit_code = clean(
        runner=runner,
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert exit_code == SUCCESS_EXIT_CODE
    assert runner.calls == []
