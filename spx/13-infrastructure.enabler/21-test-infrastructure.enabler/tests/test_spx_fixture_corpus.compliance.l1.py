"""Compliance evidence for the shared orchestration fixture corpus rules.

The corpus is read from the pinned `outcomeeng/spx` checkout. No tracked file of
this repository lies under the corpus path. The rule is exercised against the
repository's real tracked files and against a real violating case.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.orchestration_corpus import tracked_corpus_copies
from outcomeeng_testing.generators.orchestration_corpus import (
    copied_corpus_paths,
    unrelated_paths,
)
from outcomeeng_testing.harnesses.orchestration_corpus import (
    tracked_files_of_new_repository,
)
from outcomeeng_testing.harnesses.product_tree import (
    marketplace_root_for_product_tree_root_test,
    marketplace_tracked_files,
)

def _product_root() -> Path:
    return marketplace_root_for_product_tree_root_test(__file__)


def test_no_tracked_file_lies_under_the_corpus_path() -> None:
    tracked = marketplace_tracked_files(_product_root())

    assert tracked_corpus_copies(tracked) == ()


def test_a_tracked_copy_of_the_corpus_is_detected(tmp_path: Path) -> None:
    copied = copied_corpus_paths()
    unrelated = unrelated_paths()

    tracked = tracked_files_of_new_repository(tmp_path, [*copied, *unrelated])

    assert sorted(tracked_corpus_copies(tracked)) == sorted(copied)
