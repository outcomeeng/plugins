"""Level-1 compliance evidence for `spx/21-hygiene.enabler/21-clean.enabler/`.

Covers the compliance assertions in `clean.md`:
- ALWAYS: invoke `git clean -fdX` as the base command.
- ALWAYS: separate `git clean -fdX` from generated pathspecs with `--`.
- NEVER: include the active in-repository Python environment in the generated
  pathspecs.
- NEVER: fall back to bare `git clean -fdX` when no cleanup candidates exist.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.hygiene.clean import (
    CLEAN_BASE_ARGV,
    GIT_IGNORE_FILE,
    GIT_METADATA_DIR,
    PATHSPEC_SEPARATOR,
    build_clean_argv,
)
from outcomeeng_testing.harnesses.clean import (
    IGNORED_CACHE_DIR,
    IGNORED_PYTHON_ENV_DIR,
    create_clean_repo,
)


def test_argv_is_force_directories_gitignored_only() -> None:
    assert CLEAN_BASE_ARGV == ("git", "clean", "-fdX")


def test_pathspec_separator_is_present_before_generated_pathspecs(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    active_python_prefix = repo_root / IGNORED_PYTHON_ENV_DIR
    active_python_prefix.mkdir(parents=True)
    (repo_root / IGNORED_CACHE_DIR).mkdir()

    argv = build_clean_argv(
        repo_root=repo_root,
        active_python_prefix=active_python_prefix,
    )

    assert argv[:4] == (*CLEAN_BASE_ARGV, PATHSPEC_SEPARATOR)


def test_no_cleanup_candidates_return_empty_argv(
    tmp_path: Path,
) -> None:
    repo = create_clean_repo(tmp_path, include_cache=False)

    argv = build_clean_argv(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert argv == ()


def test_inside_repo_active_environment_is_omitted_from_pathspecs(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    active_python_prefix = repo_root / IGNORED_PYTHON_ENV_DIR
    active_python_prefix.mkdir(parents=True)
    (repo_root / IGNORED_CACHE_DIR).mkdir()

    argv = build_clean_argv(
        repo_root=repo_root,
        active_python_prefix=active_python_prefix,
    )

    assert IGNORED_CACHE_DIR in argv
    assert IGNORED_PYTHON_ENV_DIR not in argv
    assert GIT_METADATA_DIR not in argv
    assert GIT_IGNORE_FILE not in argv


def test_outside_repo_active_environment_does_not_remove_pathspecs(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    active_python_prefix = tmp_path / "outside-venv"
    repo_root.mkdir()
    active_python_prefix.mkdir()
    (repo_root / IGNORED_CACHE_DIR).mkdir()

    argv = build_clean_argv(
        repo_root=repo_root,
        active_python_prefix=active_python_prefix,
    )

    assert IGNORED_CACHE_DIR in argv
