"""Property evidence for unconditional plugin namespaces."""

from outcomeeng.distribution.build import (
    FLAT_AGENT_PLUGIN_SEPARATOR,
    NATIVE_AGENT_PLUGIN_SEPARATOR,
    agent_capability,
    agent_dispatch_name,
    agent_slug,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.harnesses.agent_names import exercise_agent_names


def test_names_preserve_plugin_and_unchanged_authored_role() -> None:
    exercise_agent_names(assert_names_preserve_components)


def assert_names_preserve_components(components: tuple[str, str]) -> None:
    plugin, suffix = components
    for role in (suffix, plugin, f"{plugin}-{suffix}"):
        for target in Target:
            capability = agent_capability(target)
            definition = agent_slug(plugin, role, capability=capability)
            dispatch = agent_dispatch_name(plugin, role, capability=capability)

            if capability.namespaced:
                assert definition == role
                assert dispatch.split(NATIVE_AGENT_PLUGIN_SEPARATOR) == [plugin, role]
            else:
                assert definition.split(FLAT_AGENT_PLUGIN_SEPARATOR) == [plugin, role]
                assert dispatch == definition
