"""Scenario evidence for a pinned spx checkout that lacks the orchestration corpus.

Given a checkout without the corpus directory, the harness fails naming the
missing path; it neither returns a path nor skips.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.validation.orchestration_corpus import ORCHESTRATION_CORPUS_PATH
from outcomeeng_testing.harnesses.orchestration_corpus import (
    OrchestrationCorpusMissingError,
    orchestration_corpus_directory,
)


def test_checkout_without_the_corpus_fails_naming_the_missing_path(
    tmp_path: Path,
) -> None:
    with pytest.raises(OrchestrationCorpusMissingError) as raised:
        orchestration_corpus_directory(tmp_path)

    assert str(tmp_path / ORCHESTRATION_CORPUS_PATH) in str(raised.value)


def test_checkout_with_the_corpus_resolves_its_directory(tmp_path: Path) -> None:
    corpus = tmp_path / ORCHESTRATION_CORPUS_PATH
    corpus.mkdir(parents=True)

    assert orchestration_corpus_directory(tmp_path) == corpus
