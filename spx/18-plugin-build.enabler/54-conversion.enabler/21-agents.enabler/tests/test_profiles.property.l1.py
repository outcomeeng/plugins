"""Unknown selections never fall back to a central profile."""

import pytest
from pathlib import Path
from outcomeeng.distribution.build import build

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import (
    PROFILE_FIELD,
    ProfileConfigurationError,
    resolve_profile,
)
from outcomeeng_testing.harnesses.distribution import snapshot_files
from outcomeeng_testing.harnesses.profile_validation import prepare_profile_build
from outcomeeng_testing.harnesses.profiles import exercise_unknown_profiles


def test_unknown_profiles_are_rejected() -> None:
    def assert_rejected(profile: str) -> None:
        for target in Target:
            with pytest.raises(ProfileConfigurationError):
                resolve_profile(target, profile)

    exercise_unknown_profiles(assert_rejected)


def test_unknown_profiles_leave_generated_state_unchanged(tmp_path: Path) -> None:
    def assert_rejected(profile: str) -> None:
        source, destination = prepare_profile_build(tmp_path, PROFILE_FIELD, profile)
        before = snapshot_files(destination)
        with pytest.raises(ProfileConfigurationError):
            build(source, destination)
        assert snapshot_files(destination) == before

    exercise_unknown_profiles(assert_rejected)
