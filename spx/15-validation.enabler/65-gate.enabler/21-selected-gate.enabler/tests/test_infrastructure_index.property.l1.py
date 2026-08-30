"""Property evidence for transitive reach over generated import chains."""

from __future__ import annotations

from outcomeeng_testing.harnesses.infrastructure_index import (
    chain_layout,
    index_property,
    synthetic_repository,
)


@index_property
def test_every_module_in_an_import_chain_reaches_the_test(
    chain: tuple[str, ...],
) -> None:
    with synthetic_repository() as repo:
        layout = chain_layout(repo, chain)

    for module in layout.modules:
        assert layout.index.reaching_tests(module) == (layout.test,)
