"""Network-backed real-agent state-boundary evidence."""

import json

from outcomeeng.distribution.installation import (
    CLAUDE_ENABLED_PLUGINS_FIELD,
    MARKETPLACE_NAME,
    SPEC_TREE_PLUGIN,
)
from outcomeeng_testing.harnesses.installation import (
    observe_real_first_install,
    observe_real_installation,
)


def test_first_install_ends_with_the_bootstrapped_selection_enabled() -> None:
    observation = observe_real_first_install()

    assert observation.initial_project_settings is None
    assert observation.exit_code == 0, observation.stderr
    assert observation.project_settings_after is not None
    document = json.loads(observation.project_settings_after)
    assert document[CLAUDE_ENABLED_PLUGINS_FIELD] == {
        f"{SPEC_TREE_PLUGIN}@{MARKETPLACE_NAME}": True
    }


def test_isolated_installation_preserves_persistent_agent_state() -> None:
    observation = observe_real_installation()

    assert observation.first_exit_code == 0, observation.first_stderr
    assert observation.second_exit_code == 0, observation.second_stderr
    assert observation.persistent_mode_first & 0o777 == 0
    assert observation.persistent_mode_second & 0o777 == 0
    assert observation.persistent_initial == observation.persistent_first
    assert observation.persistent_initial == observation.persistent_second
