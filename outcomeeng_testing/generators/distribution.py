"""Generated domains for downstream skill distribution evidence."""

from __future__ import annotations

from dataclasses import dataclass

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng_testing.generators.source_and_templating import source_scenarios


@dataclass(frozen=True)
class DistributionScenario:
    """Generated identifiers and content for one distribution observation."""

    plugin: str
    skill: str
    alternate_skill: str
    action: str
    content: str


def distribution_scenarios() -> tuple[DistributionScenario, ...]:
    """Derive distribution inputs from the production runtime-token domain."""
    scenarios = source_scenarios()
    skill_names = tuple(dict.fromkeys(scenario.skill for scenario in scenarios))
    return tuple(
        DistributionScenario(
            plugin=scenario.plugin,
            skill=scenario.skill,
            alternate_skill=skill_names[
                (skill_names.index(scenario.skill) + 1) % len(skill_names)
            ],
            action=scenario.outer_topic,
            content=scenario.fragment_body,
        )
        for scenario in scenarios
    )


@st.composite
def plugin_skill_mappings(
    draw: st.DrawFn,
) -> dict[str, tuple[str, ...]]:
    """Generate multiple plugins whose skill names are globally distinct."""
    identifiers = tuple(
        dict.fromkeys(
            value
            for scenario in distribution_scenarios()
            for value in (scenario.plugin, scenario.skill, scenario.alternate_skill)
        )
    )
    maximum_plugins = min(4, len(identifiers) // 2)
    plugins = draw(
        st.lists(
            st.sampled_from(identifiers),
            min_size=2,
            max_size=maximum_plugins,
            unique=True,
        )
    )
    skill_candidates = tuple(value for value in identifiers if value not in plugins)
    skill_count = draw(
        st.integers(
            min_value=len(plugins),
            max_value=min(len(skill_candidates), len(plugins) * 4),
        )
    )
    skills = draw(
        st.lists(
            st.sampled_from(skill_candidates),
            min_size=skill_count,
            max_size=skill_count,
            unique=True,
        )
    )
    return {
        plugin: tuple(skills[index :: len(plugins)])
        for index, plugin in enumerate(plugins)
    }


def plugin_skill_mapping_strategy() -> SearchStrategy[dict[str, tuple[str, ...]]]:
    """Expose the generated multi-plugin distribution domain."""
    return plugin_skill_mappings()
