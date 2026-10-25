"""Compliance evidence that no tracked file carries the retired name of the L3 tests."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from outcomeeng_testing.harnesses.spec_tree import marketplace_tracked_files

REPO_ROOT: Final = Path(__file__).resolve().parents[4]
FIRST_WORD: Final = "on"
SECOND_WORD: Final = "demand"
JOINERS: Final = ("-", "_", "")
# The pattern is assembled from its words, so this file carries no banned form.
RETIRED_NAME: Final = re.compile(f"{FIRST_WORD}[-_]?{SECOND_WORD}", flags=re.IGNORECASE)


def _offending_lines(texts: dict[str, str]) -> list[str]:
    """Return ``path:line`` for every line of ``texts`` carrying the retired name."""
    return [
        f"{path}:{number}"
        for path, text in texts.items()
        for number, line in enumerate(text.splitlines(), start=1)
        if RETIRED_NAME.search(line)
    ]


def _tracked_texts() -> dict[str, str]:
    """Return the decoded content of every tracked text file in the checkout."""
    texts: dict[str, str] = {}
    for path in marketplace_tracked_files(REPO_ROOT):
        try:
            texts[path] = (REPO_ROOT / path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
    return texts


def test_no_tracked_file_carries_the_retired_name() -> None:
    assert _offending_lines(_tracked_texts()) == []


def test_every_joined_form_of_the_retired_name_is_detected() -> None:
    forms = [
        case(f"{FIRST_WORD}{joiner}{SECOND_WORD}")
        for joiner in JOINERS
        for case in (str.lower, str.upper, str.title)
    ]

    assert _offending_lines({"fixture.md": "\n".join(forms)}) == [
        f"fixture.md:{number}" for number in range(1, len(forms) + 1)
    ]


def test_the_two_words_apart_are_not_the_retired_name() -> None:
    assert _offending_lines({"fixture.md": f"{FIRST_WORD} {SECOND_WORD}"}) == []
