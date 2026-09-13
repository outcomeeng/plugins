"""Invalid native assignments cannot delete or write generated output."""

from pathlib import Path

import pytest

from outcomeeng.distribution.build import build
from outcomeeng.distribution.profiles import (
    NATIVE_CONFIGURATION_FIELDS,
    ProfileConfigurationError,
)
from outcomeeng_testing.harnesses.distribution import snapshot_files
from outcomeeng_testing.harnesses.profile_validation import prepare_profile_build


def test_independent_overrides_stop_before_generated_state_changes(
    tmp_path: Path,
) -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for skill in (False, True):
            source, destination = prepare_profile_build(
                tmp_path / field / str(skill),
                field,
                "{{! profile_description('standard') !}}",
                skill=skill,
            )
            before = snapshot_files(destination)
            with pytest.raises(ProfileConfigurationError):
                build(source, destination)
            assert snapshot_files(destination) == before
