"""Installation evidence grouped by its governing contract."""

from outcomeeng_testing.harnesses.installation import observe_verification_recipe


def test_verification_recipe_uses_pytest_discovery_for_the_node() -> None:
    observation = observe_verification_recipe()

    assert observation.exit_code == 0, observation.stderr
    assert observation.invoked == (
        "test",
        "spx/32-distribution.enabler/21-installation.enabler",
    )
