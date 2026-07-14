"""Property evidence for include rendering."""

from __future__ import annotations

from outcomeeng_testing.harnesses.source_and_templating import (
    recursive_include_property_holds,
    rendered_include_property_holds,
)


def test_body_inlined_verbatim_between_surrounding_content() -> None:
    assert rendered_include_property_holds()


def test_chain_of_n_includes_resolves_to_innermost_body() -> None:
    assert recursive_include_property_holds()
