"""Mapping evidence for merge changeset classification."""

from __future__ import annotations

from outcomeeng_testing.harnesses.changeset_scope import (
    classification_counts_comparison,
    coordination_note_basename_comparison,
)


def test_classifier_counts_unique_change_kinds() -> None:
    assert (
        classification_counts_comparison().actual
        == classification_counts_comparison().expected
    )


def test_classifier_recognizes_source_owned_note_basenames() -> None:
    assert (
        coordination_note_basename_comparison().actual
        == coordination_note_basename_comparison().expected
    )
