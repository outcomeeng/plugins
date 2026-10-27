"""Source-owned rules for the shared orchestration fixture corpus.

The corpus lives in the pinned `outcomeeng/spx` checkout and is never copied into
this repository. Tests that read it obtain its directory from the harness module
named here, so the checkout step the workflow declares stays the only owner of
the location.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Final

ORCHESTRATION_CORPUS_PATH: Final = "testing/fixtures/orchestration"


def tracked_corpus_copies(paths: Iterable[str]) -> tuple[str, ...]:
    """Return every tracked path that lies under the corpus path."""
    corpus = PurePosixPath(ORCHESTRATION_CORPUS_PATH).parts
    return tuple(path for path in paths if _lies_under(PurePosixPath(path), corpus))


def _lies_under(path: PurePosixPath, corpus: tuple[str, ...]) -> bool:
    directories = path.parts[:-1]
    return any(
        directories[start : start + len(corpus)] == corpus
        for start in range(len(directories) - len(corpus) + 1)
    )


__all__ = [
    "ORCHESTRATION_CORPUS_PATH",
    "tracked_corpus_copies",
]
