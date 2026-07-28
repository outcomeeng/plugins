"""Filesystem, Git, and Hypothesis harnesses for hygiene evidence."""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from hypothesis import seed, settings

from outcomeeng.hygiene.clean import GIT_METADATA_DIR, Runner
from outcomeeng_testing.generators.hygiene import (
    CleanWorkspaceCase,
    XmlSpacingWorkspaceCase,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

HYGIENE_EVIDENCE_SEED = 20260728
HYGIENE_EVIDENCE_EXAMPLES = 40
HYGIENE_EVIDENCE_REPLAY_PATH = "just test spx/21-hygiene.enabler/tests"
SUBPROCESS_TIMEOUT_SECONDS = 10
STAGED_MARKDOWN_FILENAME = "staged.md"
UNSTAGED_MARKDOWN_FILENAME = "unstaged.md"
GIT_IGNORE_FILENAME = ".gitignore"


@dataclass(frozen=True)
class CleanWorkspace:
    """Temporary Git worktree arranged for cleanup evidence."""

    root: Path
    active_python_prefix: Path
    staged_path: Path
    unstaged_path: Path
    ignored_paths: tuple[Path, ...]
    untracked_paths: tuple[Path, ...]

    def snapshot(self) -> dict[Path, bytes]:
        """Return observable non-metadata worktree bytes."""
        return {
            path.relative_to(self.root): path.read_bytes()
            for path in sorted(self.root.rglob("*"))
            if path.is_file()
            and GIT_METADATA_DIR not in path.relative_to(self.root).parts
        }

    def tracked_bytes(self) -> tuple[bytes, bytes]:
        """Return tracked staged and unstaged worktree bytes."""
        return self.staged_path.read_bytes(), self.unstaged_path.read_bytes()

    def untracked_bytes(self) -> tuple[bytes, ...]:
        """Return untracked, non-ignored worktree bytes."""
        return tuple(path.read_bytes() for path in self.untracked_paths)


@dataclass(frozen=True)
class XmlSpacingWorkspace:
    """Temporary Git worktree with one target and one non-target path."""

    target_path: Path
    non_target_path: Path


@dataclass(frozen=True)
class SubprocessRunner:
    """Real subprocess implementation of the cleanup runner protocol."""

    cwd: Path

    def __call__(self, argv: Sequence[str]) -> int:
        """Run cleanup argv in the arranged worktree."""
        return subprocess.run(
            tuple(argv),
            cwd=self.cwd,
            check=False,
            capture_output=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
        ).returncode


def hygiene_generated_evidence(
    evidence_run: Callable[[], None],
) -> Callable[[], None]:
    """Apply reproducible Hypothesis policy to generated hygiene evidence."""
    configured = seed(HYGIENE_EVIDENCE_SEED)(
        settings(
            max_examples=HYGIENE_EVIDENCE_EXAMPLES,
            deadline=None,
            print_blob=True,
        )(evidence_run)
    )

    def run_evidence() -> None:
        run_replayable_property(
            configured,
            seed_value=HYGIENE_EVIDENCE_SEED,
            replay_path=HYGIENE_EVIDENCE_REPLAY_PATH,
        )

    return run_evidence


@contextmanager
def markdown_file(content: str) -> Iterator[Path]:
    """Yield a temporary markdown file containing generated content."""
    with TemporaryDirectory() as directory:
        path = Path(directory) / STAGED_MARKDOWN_FILENAME
        path.write_text(content, encoding="utf-8", newline="")
        yield path


@contextmanager
def clean_workspace(case: CleanWorkspaceCase) -> Iterator[CleanWorkspace]:
    """Yield a Git worktree carrying generated tracked and ignored content."""
    with TemporaryDirectory() as directory:
        temporary_root = Path(directory)
        root = temporary_root / "repo"
        active_python_prefix = temporary_root / "active-python"
        root.mkdir()
        active_python_prefix.mkdir()
        staged_path = root / STAGED_MARKDOWN_FILENAME
        unstaged_path = root / UNSTAGED_MARKDOWN_FILENAME
        staged_path.write_bytes(case.staged_content)
        unstaged_path.write_bytes(case.unstaged_index_content)
        (root / GIT_IGNORE_FILENAME).write_text(
            "".join(f"{name}\n" for name, _ in case.ignored_files),
            encoding="utf-8",
        )
        for name, content in case.ignored_files:
            (root / name).write_bytes(content)
        for name, content in case.untracked_files:
            (root / name).write_bytes(content)
        _run_git(root, "init")
        _run_git(
            root,
            "add",
            GIT_IGNORE_FILENAME,
            STAGED_MARKDOWN_FILENAME,
            UNSTAGED_MARKDOWN_FILENAME,
        )
        unstaged_path.write_bytes(case.unstaged_worktree_content)
        yield CleanWorkspace(
            root=root,
            active_python_prefix=active_python_prefix,
            staged_path=staged_path,
            unstaged_path=unstaged_path,
            ignored_paths=tuple(root / name for name, _ in case.ignored_files),
            untracked_paths=tuple(root / name for name, _ in case.untracked_files),
        )


@contextmanager
def xml_spacing_workspace(
    case: XmlSpacingWorkspaceCase,
) -> Iterator[XmlSpacingWorkspace]:
    """Yield staged target and unstaged non-target markdown paths."""
    with TemporaryDirectory() as directory:
        root = Path(directory)
        target_path = root / STAGED_MARKDOWN_FILENAME
        non_target_path = root / UNSTAGED_MARKDOWN_FILENAME
        target_path.write_text(case.target_content, encoding="utf-8", newline="")
        non_target_path.write_text(
            case.non_target_index_content,
            encoding="utf-8",
            newline="",
        )
        _run_git(root, "init")
        _run_git(root, "add", STAGED_MARKDOWN_FILENAME, UNSTAGED_MARKDOWN_FILENAME)
        non_target_path.write_text(
            case.non_target_worktree_content,
            encoding="utf-8",
            newline="",
        )
        yield XmlSpacingWorkspace(
            target_path=target_path,
            non_target_path=non_target_path,
        )


def _run_git(root: Path, *args: str) -> None:
    subprocess.run(
        ("git", *args),
        cwd=root,
        check=True,
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )


__all__ = [
    "CleanWorkspace",
    "SubprocessRunner",
    "XmlSpacingWorkspace",
    "clean_workspace",
    "hygiene_generated_evidence",
    "markdown_file",
    "xml_spacing_workspace",
]


_: type[Runner] = SubprocessRunner
