"""Ambient-state and repository-config evidence for installation."""

from outcomeeng.distribution.installation import CODEX_CONFIG_PATH
from outcomeeng_testing.harnesses.installation import observe_codex_config_independence


def test_repository_codex_config_has_no_installation_semantics() -> None:
    observation = observe_codex_config_independence()

    assert observation.before.commands == observation.after.commands
    assert observation.before.claude_plugins == observation.after.claude_plugins
    assert observation.before.codex_plugins == observation.after.codex_plugins
    assert observation.config_bytes
    assert all(
        str(CODEX_CONFIG_PATH) not in argument
        for command in observation.after.commands
        for argument in command.argv
    )
