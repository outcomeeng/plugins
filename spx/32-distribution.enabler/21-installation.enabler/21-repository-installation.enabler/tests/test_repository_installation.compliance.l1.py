"""Ambient-state and repository-config evidence for installation."""

from outcomeeng.distribution.installation import CODEX_CONFIG_PATH
from outcomeeng_testing.harnesses.installation import (
    VERIFICATION_TEST,
    observe_codex_config_independence,
    observe_verification_recipe,
)


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


def test_verification_recipe_aliases_the_exact_l2_evidence() -> None:
    observation = observe_verification_recipe()
    output = observation.stdout + observation.stderr

    assert observation.exit_code == 0, observation.stderr
    assert f"just test {VERIFICATION_TEST}" in output
    assert "install-marketplace" not in output
