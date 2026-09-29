"""Property evidence for unconditional plugin namespaces."""

from outcomeeng.distribution.build import (
    FLAT_AGENT_PLUGIN_SEPARATOR,
    NATIVE_AGENT_PLUGIN_SEPARATOR,
    agent_capability,
    agent_dispatch_name,
    agent_slug,
)
from outcomeeng.distribution.contracts import Target
from outcomeeng_testing.generators.agent_names import AgentNameCase
from outcomeeng_testing.harnesses.agent_names import exercise_agent_names


def test_names_preserve_plugin_and_unchanged_authored_role() -> None:
    targets = tuple(Target)

    def assert_names_preserve_components(case: AgentNameCase) -> None:
        assert targets
        assert case.roles
        for role in case.roles:
            for target in targets:
                capability = agent_capability(target)
                definition = agent_slug(case.plugin, role, capability=capability)
                dispatch = agent_dispatch_name(case.plugin, role, capability=capability)

                if capability.namespaced:
                    assert definition == role
                    assert dispatch.split(NATIVE_AGENT_PLUGIN_SEPARATOR) == [
                        case.plugin,
                        role,
                    ]
                else:
                    assert definition.split(FLAT_AGENT_PLUGIN_SEPARATOR) == [
                        case.plugin,
                        role,
                    ]
                    assert dispatch == definition

    exercise_agent_names(assert_names_preserve_components)
