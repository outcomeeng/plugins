"""Generated tracked-file paths for the orchestration corpus placement rule.

Violating paths compose the source-owned corpus path with leading directories and
fixture file names; conforming paths place the same file names outside it.
"""

from __future__ import annotations

from typing import Final

from outcomeeng.validation.orchestration_corpus import ORCHESTRATION_CORPUS_PATH

LEADING_DIRECTORIES: Final = ("", "vendor/")
FIXTURE_NAMES: Final = ("case.json", "nested/expected.txt")
UNRELATED_DIRECTORIES: Final = ("docs", "testing/fixtures", "fixtures/orchestration")


def copied_corpus_paths() -> tuple[str, ...]:
    """Return tracked paths that lie under the corpus path."""
    return tuple(
        f"{leading}{ORCHESTRATION_CORPUS_PATH}/{name}"
        for leading in LEADING_DIRECTORIES
        for name in FIXTURE_NAMES
    )


def unrelated_paths() -> tuple[str, ...]:
    """Return tracked paths with the same file names outside the corpus path."""
    return tuple(
        f"{directory}/{name}"
        for directory in UNRELATED_DIRECTORIES
        for name in FIXTURE_NAMES
    )
