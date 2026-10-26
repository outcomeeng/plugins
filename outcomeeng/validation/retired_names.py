"""Find the retired name of the L3 tests in repository text.

The tests at execution level ``l3`` carry one name, L3 tests, and one command,
``just test-l3``.  Their retired name is two words joined by a hyphen, by an
underscore, or directly, in any letter case.  The pattern is assembled from its
words, so this module carries no joined form of the name it detects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Final

RETIRED_NAME_WORDS: Final = ("on", "demand")
# A hyphen, an underscore, or nothing joins the words into the retired name.
RETIRED_NAME_JOINERS: Final = ("-", "_", "")
RETIRED_NAME_PATTERN: Final = re.compile(
    "(?:{})".format("|".join(map(re.escape, RETIRED_NAME_JOINERS))).join(
        RETIRED_NAME_WORDS
    ),
    flags=re.IGNORECASE,
)


def retired_name_lines(texts: Mapping[str, str]) -> tuple[str, ...]:
    """Return ``path:line`` for every line of ``texts`` carrying the retired name."""
    return tuple(
        f"{path}:{number}"
        for path, text in texts.items()
        for number, line in enumerate(text.splitlines(), start=1)
        if RETIRED_NAME_PATTERN.search(line)
    )


__all__ = [
    "RETIRED_NAME_JOINERS",
    "RETIRED_NAME_PATTERN",
    "RETIRED_NAME_WORDS",
    "retired_name_lines",
]
