"""Property evidence for transitive reach over generated import chains."""

from __future__ import annotations

from outcomeeng.validation.infrastructure_index import build_infrastructure_index
from outcomeeng_testing.harnesses.infrastructure_index import (
    chain_sources,
    index_property,
)


@index_property
def test_every_module_in_an_import_chain_reaches_the_test(
    chain: tuple[str, ...],
) -> None:
    sources = chain_sources(chain)

    index = build_infrastructure_index(
        package=sources.package,
        module_sources=sources.module_sources,
        test_sources=sources.test_sources,
    )

    for module in sources.modules:
        assert index.reaching_tests(module) == (sources.test,)
