"""Direct profile resolution across the complete central domain."""

from dataclasses import replace

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import (
    AGENT_PROFILES,
    NATIVE_CONFIGURATION_FIELDS,
    NATIVE_CONFIGURATION_TYPES,
    AgentProfile,
    ClaudeConfiguration,
    ClaudeEffort,
    ClaudeModel,
    ProfileConfigurationError,
    reject_configuration_overrides,
    resolve_profile,
)


def test_every_profile_resolves_directly_in_its_native_harness() -> None:
    for target in Target:
        for profile in AgentProfile:
            resolved = resolve_profile(target, profile)
            assert resolved is AGENT_PROFILES[target][profile]
            assert isinstance(resolved, NATIVE_CONFIGURATION_TYPES[target])
        assert resolve_profile(target) is AGENT_PROFILES[target][AgentProfile.STANDARD]


def test_resolver_uses_the_supplied_complete_registry() -> None:
    for target in Target:
        for profile in AgentProfile:
            for replacement in AGENT_PROFILES[target].values():
                profiles = {
                    **AGENT_PROFILES,
                    target: {**AGENT_PROFILES[target], profile: replacement},
                }
                assert (
                    resolve_profile(target, profile, profiles=profiles) is replacement
                )


def test_foreign_harness_configurations_are_rejected() -> None:
    for target in Target:
        for foreign_target in set(Target) - {target}:
            for profile in AgentProfile:
                for configuration in AGENT_PROFILES[foreign_target].values():
                    profiles = {
                        **AGENT_PROFILES,
                        target: {**AGENT_PROFILES[target], profile: configuration},
                    }
                    with pytest.raises(ProfileConfigurationError):
                        resolve_profile(target, profile, profiles=profiles)


def test_incomplete_profile_registries_are_rejected() -> None:
    for target in Target:
        with pytest.raises(ProfileConfigurationError):
            resolve_profile(target, profiles={target: AGENT_PROFILES[target]})
        for omitted in AgentProfile:
            profiles = {
                **AGENT_PROFILES,
                target: {
                    profile: configuration
                    for profile, configuration in AGENT_PROFILES[target].items()
                    if profile is not omitted
                },
            }
            with pytest.raises(ProfileConfigurationError):
                resolve_profile(target, profiles=profiles)


def test_every_native_field_is_rejected_as_an_authored_override() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        with pytest.raises(ProfileConfigurationError):
            reject_configuration_overrides({field: None})


def test_native_effort_absence_matches_the_model_capability() -> None:
    for effort in ClaudeEffort:
        with pytest.raises(ProfileConfigurationError):
            ClaudeConfiguration(ClaudeModel.HAIKU, effort)
    with pytest.raises(ProfileConfigurationError):
        ClaudeConfiguration(ClaudeModel.OPUS, None)
    for configuration in AGENT_PROFILES[Target.CODEX].values():
        with pytest.raises(ProfileConfigurationError):
            # Deliberately violate the constructor type to exercise runtime rejection.
            replace(configuration, model_reasoning_effort=None)  # type: ignore[arg-type]
