"""Level-1 conformance evidence for the bump include-index adapter."""

from __future__ import annotations

from outcomeeng_testing.harnesses.bump import observe_real_include_index


def test_include_index_conforms_to_the_directives_in_authored_sources() -> None:
    handle, index = observe_real_include_index()

    assert index.get(handle.include_target) == frozenset({handle.including_plugin})
    assert handle.unrelated_plugin not in {
        plugin for plugins in index.values() for plugin in plugins
    }
