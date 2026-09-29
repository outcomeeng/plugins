"""Invalid authored configuration cannot delete or write generated output."""

from pathlib import Path

import pytest

from outcomeeng.distribution.build import build
from outcomeeng.distribution.contracts import (
    PROFILE_DESCRIPTION_GLOBAL,
    Target,
    format_template_call,
)
from outcomeeng.distribution.profiles import (
    PROFILE_FIELD,
    ProfileConfigurationError,
    native_configuration_values,
    resolve_profile,
)
from outcomeeng.models import AgentProfile
from outcomeeng_testing.generators.profiles import profile_name_case_variants
from outcomeeng_testing.harnesses.distribution import snapshot_files
from outcomeeng_testing.harnesses.profile_validation import prepare_profile_build


def test_independent_overrides_stop_before_generated_state_changes(
    tmp_path: Path,
) -> None:
    template_value = format_template_call(
        PROFILE_DESCRIPTION_GLOBAL, AgentProfile.STANDARD
    )
    for target in Target:
        configuration = native_configuration_values(resolve_profile(target))
        for field, literal_value in configuration.items():
            for index, value in enumerate((literal_value, template_value)):
                for skill in (False, True):
                    source, destination = prepare_profile_build(
                        tmp_path / target.value / field / str(index) / str(skill),
                        field,
                        value,
                        skill=skill,
                    )
                    before = snapshot_files(destination)
                    with pytest.raises(ProfileConfigurationError):
                        build(source, destination)
                    assert snapshot_files(destination) == before


def test_unknown_profile_selections_stop_before_generated_state_changes(
    tmp_path: Path,
) -> None:
    for index, profile in enumerate(profile_name_case_variants()):
        source, destination = prepare_profile_build(
            tmp_path / str(index), PROFILE_FIELD, profile
        )
        before = snapshot_files(destination)
        with pytest.raises(ProfileConfigurationError):
            build(source, destination)
        assert snapshot_files(destination) == before
