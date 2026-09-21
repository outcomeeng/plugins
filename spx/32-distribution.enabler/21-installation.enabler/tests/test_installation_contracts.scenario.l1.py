"""Installation evidence grouped by its governing contract."""

import os

from outcomeeng.validation._steps import RECIPE_TEST
from outcomeeng_testing.harnesses.installation import observe_verification_recipe


def test_verification_recipe_uses_pytest_discovery_for_the_node() -> None:
    observation = observe_verification_recipe()

    assert observation.exit_code == os.EX_OK, observation.stderr
    assert observation.invoked == (
        RECIPE_TEST,
        "spx/32-distribution.enabler/21-installation.enabler",
    )
