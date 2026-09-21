"""Level-1 compliance evidence for workspace cleanup.

Covers the compliance assertions in `clean.md` whose verdict a command can
produce: the argv the builder composes, the paths it omits, and the empty argv
it returns when nothing is left to clean. The declared base command and
protected set are values the module complies with rather than behavior, so
their evidence is audit and no case here pins them.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.hygiene.clean import (
    CLEAN_BASE_ARGV,
    GIT_IGNORE_FILE,
    GIT_METADATA_DIR,
    PATHSPEC_SEPARATOR,
    SPX_STORE_DIR,
    build_clean_argv,
    build_clean_pathspecs,
)
from outcomeeng_testing.harnesses.clean import (
    EnvironmentPlacement,
    IGNORED_CACHE_DIR,
    IGNORED_PYTHON_ENV_DIR,
    create_clean_repo,
)


def test_pathspec_separator_is_present_before_generated_pathspecs(
    tmp_path: Path,
) -> None:
    repo = create_clean_repo(tmp_path)

    argv = build_clean_argv(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
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
    repo = create_clean_repo(tmp_path)

    argv = build_clean_argv(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert IGNORED_CACHE_DIR in argv
    assert IGNORED_PYTHON_ENV_DIR not in argv
    assert GIT_METADATA_DIR not in argv
    assert GIT_IGNORE_FILE not in argv


def test_session_store_is_omitted_while_cache_remains(tmp_path: Path) -> None:
    repo = create_clean_repo(tmp_path)

    pathspecs = build_clean_pathspecs(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert SPX_STORE_DIR not in pathspecs
    assert IGNORED_CACHE_DIR in pathspecs


def test_inside_repo_symlinked_active_environment_is_omitted_from_pathspecs(
    tmp_path: Path,
) -> None:
    repo = create_clean_repo(tmp_path, environment=EnvironmentPlacement.SYMLINKED)

    argv = build_clean_argv(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert IGNORED_CACHE_DIR in argv
    assert IGNORED_PYTHON_ENV_DIR not in argv


def test_inside_repo_symlink_target_active_environment_is_omitted_from_pathspecs(
    tmp_path: Path,
) -> None:
    repo = create_clean_repo(
        tmp_path,
        environment=EnvironmentPlacement.SYMLINK_TARGET,
    )

    argv = build_clean_argv(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert IGNORED_CACHE_DIR in argv
    assert IGNORED_PYTHON_ENV_DIR not in argv


def test_outside_repo_active_environment_does_not_remove_pathspecs(
    tmp_path: Path,
) -> None:
    repo = create_clean_repo(tmp_path, environment=EnvironmentPlacement.OUTSIDE)

    argv = build_clean_argv(
        repo_root=repo.root,
        active_python_prefix=repo.active_python_prefix,
    )

    assert IGNORED_CACHE_DIR in argv
