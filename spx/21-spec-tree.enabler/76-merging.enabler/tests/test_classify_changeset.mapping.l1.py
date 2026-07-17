"""Mapping evidence for merge changeset classification."""

from __future__ import annotations

import pathlib

from outcomeeng_testing.generators.changeset_scope import (
    classification_path_cases,
    coordination_note_recognition_cases,
)
from outcomeeng_testing.harnesses.changeset_scope import (
    MERGE_CLASSIFIER,
    MERGE_CONTRACT,
)


def test_classifier_counts_unique_change_kinds() -> None:
    for case in classification_path_cases(MERGE_CONTRACT.COORDINATION_NOTE_BASENAMES):
        assert MERGE_CLASSIFIER.classify(list(case.paths)) == (
            len(frozenset(case.paths)),
            sum(
                pathlib.PurePosixPath(path).name
                not in MERGE_CONTRACT.COORDINATION_NOTE_BASENAMES
                for path in frozenset(case.paths)
            ),
        )


def test_classifier_recognizes_source_owned_note_basenames() -> None:
    for case in coordination_note_recognition_cases(
        MERGE_CONTRACT.COORDINATION_NOTE_BASENAMES
    ):
        assert MERGE_CLASSIFIER.is_coordination_note(case.path) is case.expected
