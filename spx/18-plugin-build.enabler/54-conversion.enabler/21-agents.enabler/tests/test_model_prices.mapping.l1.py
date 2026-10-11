"""Every priced model identifier resolves to its price for each usage token class."""

from dataclasses import asdict, fields
from decimal import Decimal
from typing import Final

import pytest

from outcomeeng.distribution.profiles import (
    MODEL_PRICES,
    ClaudeModel,
    ModelPrice,
    UsageTokenClass,
    resolve_model_price,
)


PRICED_IDENTIFIERS: Final = (
    (ClaudeModel.OPUS, "claude-opus-5-5"),
    (ClaudeModel.OPUS, "claude-opus-4-6"),
    (ClaudeModel.SONNET, "claude-sonnet-5-5"),
    (ClaudeModel.SONNET, "claude-sonnet-4-6"),
)


@pytest.mark.parametrize(("family", "identifier"), PRICED_IDENTIFIERS)
def test_each_named_identifier_resolves_to_its_price_for_each_usage_token_class(
    family: ClaudeModel, identifier: str
) -> None:
    assert identifier in MODEL_PRICES[family]
    entry = MODEL_PRICES[family][identifier]
    resolved = resolve_model_price(identifier)
    assert resolved is entry
    for token_class in UsageTokenClass:
        rate = resolved.rate(token_class)
        assert isinstance(rate, Decimal)
        assert rate == asdict(entry)[token_class.value]


def test_the_price_entries_name_exactly_the_four_identifiers() -> None:
    named = {
        (family, identifier)
        for family, entries in MODEL_PRICES.items()
        for identifier in entries
    }
    assert named == set(PRICED_IDENTIFIERS)


def test_a_price_covers_exactly_the_usage_token_classes() -> None:
    assert {field.name for field in fields(ModelPrice)} == {
        token_class.value for token_class in UsageTokenClass
    }


def test_price_entries_group_under_profile_named_families() -> None:
    claimed: list[str] = []
    for family, entries in MODEL_PRICES.items():
        assert family in frozenset(ClaudeModel) - {ClaudeModel.HAIKU}
        for identifier in entries:
            assert identifier.startswith(f"claude-{family.value}-")
            claimed.append(identifier)
    assert len(claimed) == len(set(claimed))
