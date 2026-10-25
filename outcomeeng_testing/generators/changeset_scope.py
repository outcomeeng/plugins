"""Variable input domains for changeset-scope and merge-classifier evidence."""

from __future__ import annotations

import itertools
import pathlib
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum


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


def distinct_subject_paths(count: int) -> tuple[str, ...]:
    """Return ``count`` distinct repository-relative paths that carry no meaning.

    The values only need to differ from one another: reconciliation compares
    paths as opaque subjects, so any distinct tokens serve.
    """
    return tuple(f"subject-{index}.txt" for index in range(count))


class RemediationFailure(StrEnum):
    """The finite set of changeset-scope failures that carry a remedy."""

    UNSET_ORIGIN_HEAD = "unset-origin-head"
    UNEXPECTED_ORIGIN_HEAD_SHAPE = "unexpected-origin-head-shape"
    DETACHED_HEAD = "detached-head"
    GIT_FAILURE_WITHOUT_STDERR = "git-failure-without-stderr"
    GIT_FAILURE_WITH_STDERR = "git-failure-with-stderr"


@dataclass(frozen=True)
class RemediationCase:
    """One failure and the error class and message content it maps to.

    ``fragments`` are ``str.format`` templates over the placeholders the
    harness scenario and the observed failure supply.
    """

    failure: RemediationFailure
    error_name: str
    fragments: tuple[str, ...]


_SET_HEAD_AUTO = "remote set-head origin --auto"
_SET_HEAD_BRANCH = "remote set-head origin <branch>"
_SWITCH_BRANCH = "switch <branch>"
_SWITCH_NEW_BRANCH = "switch -c <new-branch>"
_VERIFY_REF = "git rev-parse --verify <ref>"
_FETCH_ORIGIN = "git fetch origin"


def remediation_cases() -> tuple[RemediationCase, ...]:
    """Return the failure-to-remedy table the changeset-scope mappings declare.

    Each row restates one mapping sentence of the governing spec: the failure,
    the error class it maps to, and the message content the sentence names.
    """
    return (
        RemediationCase(
            failure=RemediationFailure.UNSET_ORIGIN_HEAD,
            error_name="BaseRefNotConfiguredError",
            fragments=("{repo}", _SET_HEAD_AUTO, _SET_HEAD_BRANCH),
        ),
        RemediationCase(
            failure=RemediationFailure.UNEXPECTED_ORIGIN_HEAD_SHAPE,
            error_name="BaseRefNotConfiguredError",
            fragments=("{value!r}", "{origin_head_prefix}", _SET_HEAD_AUTO),
        ),
        RemediationCase(
            failure=RemediationFailure.DETACHED_HEAD,
            error_name="DetachedHeadError",
            fragments=("{repo}", _SWITCH_BRANCH, _SWITCH_NEW_BRANCH),
        ),
        RemediationCase(
            failure=RemediationFailure.GIT_FAILURE_WITHOUT_STDERR,
            error_name="ScopeResolutionError",
            fragments=("{command}", "exited {status}", _VERIFY_REF, _FETCH_ORIGIN),
        ),
        RemediationCase(
            failure=RemediationFailure.GIT_FAILURE_WITH_STDERR,
            error_name="ScopeResolutionError",
            fragments=("{stderr}",),
        ),
    )
