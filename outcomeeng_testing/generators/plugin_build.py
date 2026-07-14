"""Generated source domains for whole-pipeline build properties."""

from __future__ import annotations

from dataclasses import dataclass

from hypothesis import strategies as st

from outcomeeng_testing.generators.fragments import inert_fragment_bodies
from outcomeeng_testing.generators.source_and_templating import source_scenarios


@dataclass(frozen=True)
class PluginBuildSource:
    """One valid variable source tree for build property evidence."""

    plugin: str
    skill: str
    body: str


@st.composite
def plugin_build_sources(
    draw: st.DrawFn,
) -> PluginBuildSource:
    """Generate varied buildable plugin source from source-owned coordinates."""
    scenario = draw(st.sampled_from(source_scenarios()))
    return PluginBuildSource(
        plugin=scenario.plugin,
        skill=scenario.skill,
        body=draw(inert_fragment_bodies()),
    )
