"""Unknown selections never fall back to a central profile."""

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import ProfileConfigurationError, resolve_profile
from outcomeeng_testing.harnesses.profiles import exercise_unknown_profiles


def test_unknown_profiles_are_rejected() -> None:
    targets = tuple(Target)

    def assert_rejected(profile: str) -> None:
        assert targets
        for target in targets:
            with pytest.raises(ProfileConfigurationError):
                resolve_profile(target, profile)

    exercise_unknown_profiles(assert_rejected)
