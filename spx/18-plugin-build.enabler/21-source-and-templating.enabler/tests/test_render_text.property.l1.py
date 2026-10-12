"""Property evidence for include rendering."""

from __future__ import annotations

from outcomeeng_testing.harnesses.source_and_templating import (
    RenderedInclude,
    recursive_include_property_holds,
    run_rendered_include_property,
)


def test_body_inlined_verbatim_between_surrounding_content() -> None:
    def assert_inlined(observed: RenderedInclude) -> None:
        expected = "\n".join((observed.prefix, observed.body, observed.suffix))
        assert observed.rendered == expected

    run_rendered_include_property(assert_inlined)


def test_chain_of_n_includes_resolves_to_innermost_body() -> None:
    assert recursive_include_property_holds()
