"""Replayable generated input for agent namespace evidence."""

from collections.abc import Callable
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.agent_names import agent_name_components
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

AGENT_NAME_PROPERTY_SEED: Final = 20260908
AGENT_NAME_PROPERTY_EXAMPLES: Final = settings().max_examples
AGENT_NAME_PROPERTY_REPLAY: Final = (
    "just test spx/18-plugin-build.enabler/54-conversion.enabler/"
    "21-agents.enabler/tests/test_agent_names.property.l1.py"
)


def exercise_agent_names(assert_case: Callable[[tuple[str, str]], None]) -> None:
    """Supply generated cases to assertions owned by the evidence file."""

    @seed(AGENT_NAME_PROPERTY_SEED)
    @settings(max_examples=AGENT_NAME_PROPERTY_EXAMPLES, print_blob=True)
    @given(components=agent_name_components())
    def run_cases(components: tuple[str, str]) -> None:
        assert_case(components)

    run_replayable_property(
        run_cases,
        seed_value=AGENT_NAME_PROPERTY_SEED,
        replay_path=AGENT_NAME_PROPERTY_REPLAY,
    )
