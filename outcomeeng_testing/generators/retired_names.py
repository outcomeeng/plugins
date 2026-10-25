"""Generated forms of the retired L3-test name and of its words kept apart.

Every form composes the source-owned words; the joined forms use every
source-owned joiner, and the separated forms use separators that are no joiner.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

from outcomeeng.validation.retired_names import RETIRED_NAME_JOINERS, RETIRED_NAME_WORDS

LETTER_CASES: Final[tuple[Callable[[str], str], ...]] = (
    str.lower,
    str.upper,
    str.title,
    str.swapcase,
)
# Separators that keep the two words apart: whitespace, and a joiner set off by
# whitespace on both sides.
SEPARATORS: Final = (
    " ",
    "\t",
    *(f" {joiner} " for joiner in RETIRED_NAME_JOINERS if joiner),
)
GENERATED_TEXT_PATH: Final = "generated.md"


def joined_retired_name_forms() -> tuple[str, ...]:
    """Return the words joined by every joiner, in every letter case."""

    return tuple(
        letter_case(joiner.join(RETIRED_NAME_WORDS))
        for joiner in RETIRED_NAME_JOINERS
        for letter_case in LETTER_CASES
    )


def separated_retired_name_forms() -> tuple[str, ...]:
    """Return the words kept apart by every separator, in every letter case."""

    return tuple(
        letter_case(separator.join(RETIRED_NAME_WORDS))
        for separator in SEPARATORS
        for letter_case in LETTER_CASES
    )
