"""Level-1 scenario evidence for `spx/21-hygiene.enabler/21-clean.enabler/`.

Covers the scenario assertions in `clean.md`: the recorded argv omits an
active in-repository Python environment from generated pathspecs, Git dry-run
output preserves that environment while listing another ignored cache, and
the runner's exit code is propagated to the caller.
"""

from __future__ import annotations

import subprocess
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
)


def test_clean_omits_active_environment_from_pathspecs(tmp_path: Path) -> None:
    repo = create_clean_repo(tmp_path)
    runner = RecordingRunner()

    exit_code = clean(
        runner=runner,
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert exit_code == 0
    assert len(runner.calls) == 1
    assert runner.calls[0][:4] == (*CLEAN_BASE_ARGV, PATHSPEC_SEPARATOR)
    assert IGNORED_CACHE_DIR in runner.calls[0]
    assert IGNORED_PYTHON_ENV_DIR not in runner.calls[0]


def test_git_dry_run_preserves_active_environment(tmp_path: Path) -> None:
    repo = create_clean_repo(tmp_path)

    argv = build_clean_argv(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )
    dry_run_argv = ("git", "clean", "-ndX", *argv[len(CLEAN_BASE_ARGV) :])

    result = subprocess.run(
        dry_run_argv,
        cwd=repo.root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert f"Would remove {IGNORED_CACHE_DIR}/" in result.stdout
    assert f"Would remove {IGNORED_PYTHON_ENV_DIR}/" not in result.stdout


def test_clean_propagates_runner_exit_code() -> None:
    runner = RecordingRunner(exit_code=3)

    exit_code = clean(runner=runner)

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
