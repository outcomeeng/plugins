"""Mapping evidence for deterministic native-profile probe planning."""

from outcomeeng.distribution.native_profile_execution import native_profile_rows
from outcomeeng.distribution.profiles import AGENT_PROFILES


def test_native_profile_rows_cover_the_central_configuration_matrix() -> None:
    """Every central harness/profile configuration has one planned probe row."""
    assert {
        (row.target, row.profile): row.configuration for row in native_profile_rows()
    } == {
        (target, profile): configuration
        for target, profiles in AGENT_PROFILES.items()
        for profile, configuration in profiles.items()
    }


def test_native_profile_artifacts_are_separate_from_disposable_state() -> None:
    for row in native_profile_rows():
        assert row.loading_path.parent == row.definition_path.parent
        assert row.result_path.parent == row.definition_path.parent
        assert not row.definition_path.is_relative_to(row.state_root)
        assert row.native_definition_path.is_relative_to(row.state_root)
        assert len(row.launch_commands) == 1
