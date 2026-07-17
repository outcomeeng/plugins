"""Variable input domains for changeset-scope and merge-classifier evidence."""

from __future__ import annotations

import itertools
import pathlib
from collections.abc import Iterator, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ChangesetScopeCase:
    """Generated branch and path inputs for one synthetic Git topology."""

    base_branch: str
    feature_branch: str
    initial_file: str
    merged_file: str
    feature_file: str
    working_file: str


@dataclass(frozen=True)
class ClassificationPathCase:
    """One finite path collection in the merge classifier's mapping domain."""

    paths: tuple[str, ...]


@dataclass(frozen=True)
class CoordinationNoteRecognitionCase:
    """One source-derived path and its coordination-note recognition result."""

    path: str
    expected: bool


def changeset_scope_cases() -> Iterator[ChangesetScopeCase]:
    """Generate reproducible branch and path alternatives without a fixed case bag."""
    for index in itertools.count():
        token = format(index, "x")
        yield ChangesetScopeCase(
            base_branch=f"base-{token}",
            feature_branch=f"feature/{token}",
            initial_file=f"initial/{token}.txt",
            merged_file=f"merged/{token}.txt",
            feature_file=f"feature/{token}.txt",
            working_file=f"working-{token}.py",
        )


def classification_path_cases(
    coordination_note_basenames: Sequence[str],
) -> tuple[ClassificationPathCase, ...]:
    """Compose the empty, note-only, mixed, and duplicate mapping cases."""
    generated_cases = changeset_scope_cases()
    note_parent = next(generated_cases).feature_branch
    ordinary_path = next(generated_cases).feature_file
    note_path = pathlib.PurePosixPath(
        note_parent,
        coordination_note_basenames[0],
    ).as_posix()
    return (
        ClassificationPathCase(paths=()),
        ClassificationPathCase(paths=(note_path,)),
        ClassificationPathCase(paths=(note_path, ordinary_path)),
        ClassificationPathCase(paths=(note_path, ordinary_path, ordinary_path)),
    )


def coordination_note_recognition_cases(
    coordination_note_basenames: Sequence[str],
) -> tuple[CoordinationNoteRecognitionCase, ...]:
    """Derive positive paths and near misses from every source-owned basename."""
    generated_parent = next(changeset_scope_cases()).feature_branch
    cases: list[CoordinationNoteRecognitionCase] = []
    for basename in coordination_note_basenames:
        suffix = pathlib.PurePosixPath(basename).suffix
        stem = basename.removesuffix(suffix)
        near_misses = (
            basename.lower(),
            basename + suffix,
            stem[:-1] + stem[:1] + suffix,
        )
        paths = (
            basename,
            pathlib.PurePosixPath(generated_parent, basename).as_posix(),
        )
        cases.extend(
            CoordinationNoteRecognitionCase(path=path, expected=True) for path in paths
        )
        cases.extend(
            CoordinationNoteRecognitionCase(path=path, expected=False)
            for near_miss in near_misses
            for path in (
                near_miss,
                pathlib.PurePosixPath(generated_parent, near_miss).as_posix(),
            )
        )
    return tuple(cases)
