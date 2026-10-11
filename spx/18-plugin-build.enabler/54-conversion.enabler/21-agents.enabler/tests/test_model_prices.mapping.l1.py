"""Every priced model identifier resolves to its price for each usage token class."""

from dataclasses import asdict, fields

from outcomeeng.distribution.profiles import (
    MODEL_PRICES,
    ClaudeModel,
    ModelPrice,
    UsageTokenClass,
    resolve_model_price,
)


def test_every_priced_identifier_resolves_to_its_price_for_each_usage_token_class() -> (
    None
):
    for entries in MODEL_PRICES.values():
        for identifier, entry in entries.items():
            resolved = resolve_model_price(identifier)
            assert resolved is entry
            for token_class in UsageTokenClass:
                assert resolved.rate(token_class) == asdict(entry)[token_class.value]


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
