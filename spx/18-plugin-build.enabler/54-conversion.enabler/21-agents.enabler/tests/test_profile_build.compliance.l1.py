"""Profile and price data reach generated output only through the build."""

from decimal import Decimal
from pathlib import Path

import pytest

from outcomeeng.distribution.build import build
from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import (
    MODEL_PRICES_DOCUMENT_KEY,
    NATIVE_CONFIGURATION_FIELDS,
    ProfileConfigurationError,
    UsageTokenClass,
    resolve_model_price,
)
from outcomeeng_testing.generators.profile_binding import PROFILE_DESCRIPTION_TOKEN
from outcomeeng_testing.generators.model_prices import priced_identifiers
from outcomeeng_testing.harnesses.distribution import snapshot_files
from outcomeeng_testing.harnesses.model_prices import shipped_price_document
from outcomeeng_testing.harnesses.profile_validation import prepare_profile_build


def test_independent_overrides_stop_before_generated_state_changes(
    tmp_path: Path,
) -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for skill in (False, True):
            source, destination = prepare_profile_build(
                tmp_path / field / str(skill),
                field,
                PROFILE_DESCRIPTION_TOKEN,
                skill=skill,
            )
            before = snapshot_files(destination)
            with pytest.raises(ProfileConfigurationError):
                build(source, destination)
            assert snapshot_files(destination) == before


@pytest.mark.parametrize("target", tuple(Target))
def test_every_price_entry_reaches_the_rendered_sibling_data_file(
    target: Target,
) -> None:
    entries = shipped_price_document(target)[MODEL_PRICES_DOCUMENT_KEY]
    assert set(entries) == priced_identifiers()
    for identifier in priced_identifiers():
        price = resolve_model_price(identifier)
        assert {
            token_class: Decimal(entries[identifier][token_class.value])
            for token_class in UsageTokenClass
        } == {token_class: price.rate(token_class) for token_class in UsageTokenClass}
