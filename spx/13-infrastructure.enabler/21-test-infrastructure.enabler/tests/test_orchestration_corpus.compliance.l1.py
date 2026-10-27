"""Compliance evidence for the shared orchestration fixture corpus rules.

The corpus is read from the pinned `outcomeeng/spx` checkout. No tracked file of
this repository lies under the corpus path, and every test that names the corpus
path imports the harness that resolves it. Each rule is exercised against the
repository's real tracked files and against a real violating case.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.orchestration_corpus import (
    CORPUS_HARNESS_MODULE,
    ORCHESTRATION_CORPUS_PATH,
    TEST_EVIDENCE_DIRECTORY,
    corpus_readers_bypassing_harness,
    tracked_corpus_copies,
)
from outcomeeng_testing.harnesses.orchestration_corpus import (
    tracked_files_of_new_repository,
)
from outcomeeng_testing.harnesses.product_tree import (
    marketplace_root_for_product_tree_root_test,
    marketplace_tracked_files,
    marketplace_tracked_texts,
)

COPIED_FIXTURE_NAME = "case.json"
READER_FILE_NAME = "test_reader.py"


def _product_root() -> Path:
    return marketplace_root_for_product_tree_root_test(__file__)


def test_no_tracked_file_lies_under_the_corpus_path() -> None:
    tracked = marketplace_tracked_files(_product_root())

    assert tracked_corpus_copies(tracked) == ()


def test_a_tracked_copy_of_the_corpus_is_detected(tmp_path: Path) -> None:
    copied = f"{ORCHESTRATION_CORPUS_PATH}/{COPIED_FIXTURE_NAME}"
    unrelated = f"docs/{COPIED_FIXTURE_NAME}"

    tracked = tracked_files_of_new_repository(tmp_path, [copied, unrelated])

    assert tracked_corpus_copies(tracked) == (copied,)


def test_every_test_that_names_the_corpus_path_imports_the_harness() -> None:
    texts = marketplace_tracked_texts(_product_root())

    assert corpus_readers_bypassing_harness(texts) == ()


def test_a_test_naming_the_corpus_path_without_the_harness_is_detected() -> None:
    reader = f"spx/node/{TEST_EVIDENCE_DIRECTORY}/{READER_FILE_NAME}"
    texts = {
        reader: f'CORPUS = "{ORCHESTRATION_CORPUS_PATH}"\n',
        f"spx/node/{TEST_EVIDENCE_DIRECTORY}/test_conforming.py": (
            f'import {CORPUS_HARNESS_MODULE}\nCORPUS = "{ORCHESTRATION_CORPUS_PATH}"\n'
        ),
    }

    assert corpus_readers_bypassing_harness(texts) == (reader,)
