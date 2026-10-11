"""Identifier domains and source text around the central model price entries."""

import re
from collections.abc import Iterator

from outcomeeng.distribution.profiles import (
    MODEL_PRICES,
    ClaudeModel,
    CodexModel,
    ModelPrice,
)

_VERSION_SEGMENT = re.compile(r"\d+")


def priced_identifiers() -> frozenset[str]:
    """Return every model identifier a price entry names."""
    return frozenset(
        identifier for entries in MODEL_PRICES.values() for identifier in entries
    )


def _neighbours(identifier: str) -> Iterator[str]:
    """Yield identifiers beside a priced one that no price entry names."""
    segments = identifier.split("-")
    for index, segment in enumerate(segments):
        if _VERSION_SEGMENT.fullmatch(segment):
            bumped = [*segments]
            bumped[index] = str(int(segment) + 1)
            yield "-".join(bumped)
    yield "-".join(segments[:-1])
    yield f"{identifier}-latest"
    yield identifier.upper()
    yield f" {identifier} "


def _haiku_identifiers(priced: frozenset[str]) -> Iterator[str]:
    """Yield identifiers of the unpriced family, versioned like the priced ones."""
    for identifier in priced:
        family = identifier.split("-")[1]
        yield identifier.replace(family, ClaudeModel.HAIKU.value, 1)
    yield ClaudeModel.HAIKU.value


def unpriced_identifiers() -> tuple[str, ...]:
    """Return identifiers outside the price entries, in a stable order.

    Covers an unlisted version of a profile-named family, a haiku identifier,
    a Codex identifier, and a bare family name.
    """
    priced = priced_identifiers()
    candidates = [
        *(
            neighbour
            for identifier in sorted(priced)
            for neighbour in _neighbours(identifier)
        ),
        *_haiku_identifiers(priced),
        *(str(model) for model in CodexModel),
        *(str(family) for family in MODEL_PRICES),
    ]
    return tuple(
        dict.fromkeys(candidate for candidate in candidates if candidate not in priced)
    )


def price_table_copy_source() -> str:
    """Return Python source holding a second price table for the priced identifiers."""
    rows = "\n".join(
        f'    "{identifier}": {ModelPrice.__name__}(1, 1, 1, 1, 1),'
        for identifier in sorted(priced_identifiers())
    )
    return f"PRICES = {{\n{rows}\n}}\n"


def source_without_price_table() -> str:
    """Return Python source that names no priced identifier and builds no price."""
    return "VALUE = 1\n"
