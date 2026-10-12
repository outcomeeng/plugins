"""Unnamed identifiers stay unpriced and prices live only in the configuration owner."""

from pathlib import Path

import pytest

from outcomeeng.distribution import profiles
from outcomeeng.distribution.profiles import (
    ModelPrice,
    UnpricedModelError,
    resolve_model_price,
)
from outcomeeng_testing.generators.model_prices import (
    copied_table_identifiers,
    price_table_copy_sources,
    priced_identifiers,
    source_without_price_table,
    unrelated_price_class_source,
    unpriced_identifiers,
)
from outcomeeng_testing.harnesses.model_prices import (
    observe_price_sites,
    production_python_sources,
)


def test_identifiers_no_price_entry_names_resolve_as_unpriced() -> None:
    named = priced_identifiers()
    for identifier in unpriced_identifiers():
        assert identifier not in named
        with pytest.raises(UnpricedModelError):
            resolve_model_price(identifier)


def test_identifiers_a_price_entry_names_are_not_reported_as_unpriced() -> None:
    for identifier in priced_identifiers():
        assert isinstance(resolve_model_price(identifier), ModelPrice)


def test_every_priced_identifier_is_named_once_in_the_configuration_owner() -> None:
    owner = Path(profiles.__file__).resolve()
    sites = observe_price_sites(production_python_sources(), priced_identifiers())
    named = [site for site in sites if site.identifier is not None]
    for identifier in priced_identifiers():
        holders = [
            site.path.resolve() for site in named if site.identifier == identifier
        ]
        assert holders == [owner]
    assert {site.path.resolve() for site in sites} == {owner}


def test_a_second_price_table_is_observed_in_any_source(tmp_path: Path) -> None:
    violating = []
    for index, source in enumerate(price_table_copy_sources()):
        path = tmp_path / f"violating_{index}.py"
        path.write_text(source, encoding="utf-8")
        violating.append(path)
    conforming = tmp_path / "conforming.py"
    conforming.write_text(source_without_price_table(), encoding="utf-8")

    for path in violating:
        sites = observe_price_sites([path, conforming], copied_table_identifiers())

        assert {site.path for site in sites} == {path}
        assert {site.identifier for site in sites} >= copied_table_identifiers()
        assert [site for site in sites if site.identifier is None], path.read_text(
            encoding="utf-8"
        )


def test_a_same_named_class_from_another_module_is_not_a_price_table(
    tmp_path: Path,
) -> None:
    unrelated = tmp_path / "unrelated.py"
    unrelated.write_text(unrelated_price_class_source(), encoding="utf-8")

    sites = observe_price_sites([unrelated], frozenset())

    assert sites == []
