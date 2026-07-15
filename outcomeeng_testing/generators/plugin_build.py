"""Generated source domains for whole-pipeline build properties."""

from __future__ import annotations

from dataclasses import dataclass

from hypothesis import strategies as st

from outcomeeng.distribution.build import FORMATTER_VERSION_OUTPUT
from outcomeeng_testing.generators.fragments import inert_fragment_bodies
from outcomeeng_testing.generators.source_and_templating import (
    SourceScenario,
    source_scenarios,
)


@dataclass(frozen=True)
class PluginBuildPlugin:
    """One generated plugin spanning every source artifact category."""

    scenario: SourceScenario
    body: str
    opaque_body: bytes


@dataclass(frozen=True)
class PluginBuildSource:
    """One valid variable multi-plugin source tree for build properties."""

    plugins: tuple[PluginBuildPlugin, ...]


PLUGIN_BUILD_MIN_PLUGINS = 2
PLUGIN_BUILD_MAX_PLUGINS = 3
PLUGIN_BUILD_MAX_OPAQUE_BYTES = 64


def nonmatching_formatter_versions() -> st.SearchStrategy[str]:
    """Generate formatter version output outside the accepted source contract."""
    return st.text().filter(lambda output: output.strip() != FORMATTER_VERSION_OUTPUT)


@st.composite
def plugin_build_sources(
    draw: st.DrawFn,
) -> PluginBuildSource:
    """Generate varied buildable plugin source from source-owned coordinates."""
    scenarios = draw(
        st.lists(
            st.sampled_from(source_scenarios()),
            min_size=PLUGIN_BUILD_MIN_PLUGINS,
            max_size=PLUGIN_BUILD_MAX_PLUGINS,
            unique_by=lambda scenario: scenario.plugin,
        )
    )
    return PluginBuildSource(
        plugins=tuple(
            PluginBuildPlugin(
                scenario=scenario,
                body=draw(inert_fragment_bodies()),
                opaque_body=draw(st.binary(max_size=PLUGIN_BUILD_MAX_OPAQUE_BYTES)),
            )
            for scenario in scenarios
        )
    )
