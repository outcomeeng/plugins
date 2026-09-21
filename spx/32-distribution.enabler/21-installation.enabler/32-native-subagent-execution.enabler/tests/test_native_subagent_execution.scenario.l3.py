"""Installation evidence grouped by its governing contract."""

import os

import pytest

from outcomeeng_testing.harnesses.installation import observe_codex_subagent_discovery


@pytest.mark.live_subagent_discovery
def test_fresh_codex_session_discovers_every_placed_canonical_subagent() -> None:
    observation = observe_codex_subagent_discovery()

    assert observation.install_exit_code == os.EX_OK, observation.install_stderr
    assert observation.login_exit_code == os.EX_OK, observation.login_stderr
    assert observation.session_exit_code == os.EX_OK, observation.session_stderr
    assert observation.placed_subagent_names
    assert observation.discovered_subagent_names is not None, (
        observation.session_last_message
    )
    assert observation.placed_subagent_names <= observation.discovered_subagent_names
