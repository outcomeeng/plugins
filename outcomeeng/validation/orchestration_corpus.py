"""Source-owned rules for the shared orchestration fixture corpus.

The corpus lives in the pinned `outcomeeng/spx` checkout and is never copied into
this repository. Tests that read it obtain its directory from the harness module
named here, so the checkout step the workflow declares stays the only owner of
the location.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import PurePosixPath
from typing import Final

ORCHESTRATION_CORPUS_PATH: Final = "testing/fixtures/orchestration"
CORPUS_HARNESS_MODULE: Final = "outcomeeng_testing.harnesses.orchestration_corpus"
TEST_EVIDENCE_DIRECTORY: Final = "tests"


def tracked_corpus_copies(paths: Iterable[str]) -> tuple[str, ...]:
    """Return every tracked path that lies under the corpus path."""
    corpus = PurePosixPath(ORCHESTRATION_CORPUS_PATH).parts
    return tuple(path for path in paths if _lies_under(PurePosixPath(path), corpus))


def corpus_readers_bypassing_harness(
    test_texts: Mapping[str, str],
) -> tuple[str, ...]:
    """Return every test file that names the corpus path without importing the harness."""
    return tuple(
        path
        for path, text in sorted(test_texts.items())
        if _is_test_evidence(PurePosixPath(path))
        and ORCHESTRATION_CORPUS_PATH in text
        and CORPUS_HARNESS_MODULE not in text
    )


def _lies_under(path: PurePosixPath, corpus: tuple[str, ...]) -> bool:
    directories = path.parts[:-1]
    return any(
        directories[start : start + len(corpus)] == corpus
        for start in range(len(directories) - len(corpus) + 1)
    )


def _is_test_evidence(path: PurePosixPath) -> bool:
    return TEST_EVIDENCE_DIRECTORY in path.parts[:-1]


__all__ = [
    "CORPUS_HARNESS_MODULE",
    "ORCHESTRATION_CORPUS_PATH",
    "TEST_EVIDENCE_DIRECTORY",
    "corpus_readers_bypassing_harness",
    "tracked_corpus_copies",
]
