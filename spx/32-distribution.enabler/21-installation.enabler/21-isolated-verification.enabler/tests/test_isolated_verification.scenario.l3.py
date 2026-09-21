"""Installation evidence grouped by its governing contract."""

import os
import tomllib

from outcomeeng.distribution.installation import (
    AGENT_SKILL_NAME_FIELD,
    AGENT_SKILLS_CONFIG_FIELD,
    AGENT_SKILLS_FIELD,
)
from outcomeeng_testing.harnesses.installation import observe_real_installation


def test_real_agent_clis_place_home_agents_and_repeat_full_installation() -> None:
    observation = observe_real_installation()
    assert observation.first_exit_code == os.EX_OK, observation.first_stderr
    assert observation.second_exit_code == os.EX_OK, observation.second_stderr
    assert observation.claude_plugins_second == observation.claude_plugins_first
    assert observation.codex_plugins_second == observation.codex_plugins_first
    assert set(observation.placed_first) == (
        set(observation.placed_initial) | set(observation.shipped_agents)
    )
    assert observation.placed_first == observation.placed_second
    assert observation.installed_skills_first == observation.installed_skills_second
    for name, content in observation.shipped_agents:
        assert dict(observation.placed_first)[name] == content
        for skill in tomllib.loads(content.decode("utf-8"))[AGENT_SKILLS_FIELD][
            AGENT_SKILLS_CONFIG_FIELD
        ]:
            assert skill[AGENT_SKILL_NAME_FIELD] in {
                installed_name
                for installed_name, _, _ in observation.installed_skills_first
            }
    for _, path, content in observation.installed_skills_first:
        assert content
        assert path.is_relative_to(observation.invocation_checkout) or any(
            path.is_relative_to(root) for root in observation.state_roots
        )
    assert observation.unowned_first == observation.unowned_initial
    assert observation.unowned_second == observation.unowned_initial
