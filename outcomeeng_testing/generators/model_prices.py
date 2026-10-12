"""Identifier domains and source text around the central model price entries."""

import re
from collections.abc import Iterator
from typing import Final

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


_COPIED_TABLE_IDENTIFIERS: Final = (
    "generator-owned-model-a",
    "generator-owned-model-b",
)


def copied_table_identifiers() -> frozenset[str]:
    """Return the identifiers the generated second price table names."""
    return frozenset(_COPIED_TABLE_IDENTIFIERS)


def _price_class_module() -> str:
    return ModelPrice.__module__


def _price_class_name() -> str:
    return ModelPrice.__name__


def _table_source(imports: str, constructor: str) -> str:
    rows = "\n".join(
        f'    "{identifier}": {constructor}(1, 1, 1, 1, 1),'
        for identifier in _COPIED_TABLE_IDENTIFIERS
    )
    return f"{imports}\nPRICES = {{\n{rows}\n}}\n"


_ALIAS: Final = "AliasedPriceConstructor"
_MODULE_ALIAS: Final = "aliased_price_owner"


def price_table_copy_sources() -> tuple[str, ...]:
    """Return Python sources each holding a second price table built from generator-owned identifiers.

    The sources reach the price class through each import binding that names
    it: a direct import, an aliased import, an imported module's attribute, an
    aliased module's attribute, a fully dotted module attribute, and an alias
    assignment of a bound name.
    """
    module, name = _price_class_module(), _price_class_name()
    package, _, leaf = module.rpartition(".")
    return (
        _table_source(f"from {module} import {name}", name),
        _table_source(f"from {module} import {name} as {_ALIAS}", _ALIAS),
        _table_source(f"from {package} import {leaf}", f"{leaf}.{name}"),
        _table_source(
            f"from {package} import {leaf} as {_MODULE_ALIAS}",
            f"{_MODULE_ALIAS}.{name}",
        ),
        _table_source(f"import {module} as {_MODULE_ALIAS}", f"{_MODULE_ALIAS}.{name}"),
        _table_source(f"import {module}", f"{module}.{name}"),
        _table_source(
            f"from {module} import {name} as Inner\n{_ALIAS} = Inner", _ALIAS
        ),
    )


def unrelated_price_class_source() -> str:
    """Return Python source constructing a same-named class that is not the price class."""
    return _table_source(
        f"from unrelated_owner import {_price_class_name()}", _price_class_name()
    )


def source_without_price_table() -> str:
    """Return Python source that names no priced identifier and builds no price."""
    return "VALUE = 1\n"
