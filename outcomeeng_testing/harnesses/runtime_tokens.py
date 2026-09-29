"""Filesystem lifecycle and undecided observations for runtime-token evidence."""

from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import RUNTIME_TOKEN_REGISTRY, RuntimeTokenKind
from outcomeeng.distribution.contracts import SKILL_FILENAME, SOURCE_ROOT_NAME
from outcomeeng.validation._git import run_git_command
from outcomeeng.validation._steps import (
    RUNTIME_TOKEN_COMMAND_ARGV,
    runtime_token_step,
)
from outcomeeng.validation.profile_configuration import CONFIGURATION_ONLY_OPTION
from outcomeeng.validation.runtime_tokens import (
    RUNTIME_TOKEN_IGNORE,
    Violation,
    is_ignored,
    main,
    scan_file,
    scan_paths,
)


@dataclass(frozen=True)
class ScannerObservation:
    """Input identity, scanner findings, and command output without a verdict."""

    path: Path
    source: str
    violations: tuple[Violation, ...]
    output: str
    exit_code: int
    ignored: bool
    unignored_violations: tuple[Violation, ...]


def observe_source(
    source: str,
    *,
    relative_path: Path = Path(SKILL_FILENAME),
    ignore: frozenset[str] = RUNTIME_TOKEN_IGNORE,
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> ScannerObservation:
    """Scan one disposable authored input through the file and command boundaries."""
    with TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [str(path)], repo_root=root, ignore=ignore, registry=registry
            )
        return ScannerObservation(
            path=path,
            source=source,
            violations=tuple(
                scan_file(path, repo_root=root, ignore=ignore, registry=registry)
            ),
            output=output.getvalue(),
            exit_code=exit_code,
            ignored=is_ignored(path, repo_root=root, ignore=ignore),
            unignored_violations=tuple(
                scan_file(path, repo_root=root, ignore=frozenset(), registry=registry)
            ),
        )


@dataclass(frozen=True)
class AuthoredTreeEnforcement:
    """The gate step's full-scan files beside an independently derived inventory.

    Returns both sets and the per-file ignore observations rather than their
    agreement, so the linked test owns every comparison the assertion claims.
    """

    enforced_roots: tuple[Path, ...]
    expected_files: frozenset[Path]
    gate_files: frozenset[Path]
    raw_token_violations: tuple[Violation, ...]
    ignored_files: frozenset[Path]
    ignore_listed_files: frozenset[Path]


def authored_tree_enforcement() -> AuthoredTreeEnforcement:
    """Return the authored-tree enforcement observations, undecided.

    The gate files are the arguments the gate's runtime-token step passes
    before its configuration-only marker, read from the step as the gate
    builds it at the moment the inventory is taken.
    """
    repo_root = Path.cwd().resolve()
    source_root = repo_root / SOURCE_ROOT_NAME
    roots = (source_root,)
    expected_files = {
        path.resolve()
        for root in roots
        if root.is_dir()
        for path in root.rglob("*")
        if path.is_file()
    }
    argv = runtime_token_step().argv
    full_scan_arguments = argv[
        len(RUNTIME_TOKEN_COMMAND_ARGV) : argv.index(CONFIGURATION_ONLY_OPTION)
    ]
    gate_files = {Path(raw_path).resolve() for raw_path in full_scan_arguments}
    return AuthoredTreeEnforcement(
        enforced_roots=roots,
        expected_files=frozenset(expected_files),
        gate_files=frozenset(gate_files),
        raw_token_violations=tuple(scan_paths(gate_files)),
        ignored_files=frozenset(path for path in gate_files if is_ignored(path)),
        ignore_listed_files=frozenset(
            path
            for path in gate_files
            if path.relative_to(repo_root).as_posix() in RUNTIME_TOKEN_IGNORE
        ),
    )


# Git's listing of the tracked files under one pathspec, NUL-separated so a
# path carrying whitespace or a newline stays one entry.
_TRACKED_FILES_ARGV = ("git", "ls-files", "-z", "--")


class TrackedFilesUnavailable(RuntimeError):
    """Git could not list the checkout's tracked files."""


def tracked_source_files() -> frozenset[Path]:
    """Return every tracked file under the checkout's source root, resolved.

    The tracked set is fixed for the whole session, so it bounds from below a
    file list captured at import time even while the session writes untracked
    files, such as bytecode caches, beneath the same root.
    """
    repo_root = Path.cwd().resolve()
    result = run_git_command((*_TRACKED_FILES_ARGV, SOURCE_ROOT_NAME), repo_root)
    if result.returncode != 0:
        raise TrackedFilesUnavailable(result.stderr or result.stdout)
    return frozenset(
        (repo_root / entry).resolve() for entry in result.stdout.split("\0") if entry
    )
