"""Replay policy for central-profile boundary evidence."""

from collections.abc import Callable
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.profiles import unknown_profile_names
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

PROFILE_PROPERTY_SEED: Final = 20260908
PROFILE_PROPERTY_REPLAY: Final = (
    "just test spx/18-plugin-build.enabler/54-conversion.enabler/"
    "21-agents.enabler/tests/test_profiles.property.l1.py"
)


def exercise_unknown_profiles(assert_case: Callable[[str], None]) -> None:
    """Supply generated selections while leaving the verdict in the linked test."""

    @seed(PROFILE_PROPERTY_SEED)
    @settings(print_blob=True)
    @given(profile=unknown_profile_names())
    def run_cases(profile: str) -> None:
        assert_case(profile)

    run_replayable_property(
        run_cases,
        seed_value=PROFILE_PROPERTY_SEED,
        replay_path=PROFILE_PROPERTY_REPLAY,
    )
