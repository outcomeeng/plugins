"""Property evidence for transitive reach over generated import chains."""

from __future__ import annotations

from outcomeeng.validation.infrastructure_index import build_infrastructure_index
from outcomeeng_testing.generators.infrastructure_index import ChainSources
from outcomeeng_testing.harnesses.infrastructure_index import index_property


@index_property
def test_every_module_in_an_import_chain_reaches_the_test(
    sources: ChainSources,
) -> None:
    index = build_infrastructure_index(
        package=sources.package,
        module_sources=sources.module_sources,
        test_sources=sources.test_sources,
    )

    for module in sources.chain:
        assert index.reaching_tests(module) == (sources.test,)
