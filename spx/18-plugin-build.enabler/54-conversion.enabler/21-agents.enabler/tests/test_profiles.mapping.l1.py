"""Direct profile resolution across the complete central domain."""

from dataclasses import fields, replace

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import (
    AGENT_PROFILES,
    NATIVE_CONFIGURATION_FIELDS,
    NATIVE_CONFIGURATION_TYPES,
    ProfileConfigurationError,
    reject_configuration_overrides,
    resolve_profile,
)
from outcomeeng.models import AgentProfile


def test_every_profile_resolves_directly_in_its_native_harness() -> None:
    targets = tuple(Target)
    profiles = tuple(AgentProfile)

    assert targets
    assert profiles
    for target in targets:
        for profile in profiles:
            resolved = resolve_profile(target, profile)
            assert resolved is AGENT_PROFILES[target][profile]
            assert isinstance(resolved, NATIVE_CONFIGURATION_TYPES[target])
        assert resolve_profile(target) is AGENT_PROFILES[target][AgentProfile.STANDARD]


def test_resolver_uses_the_supplied_complete_registry() -> None:
    cases = tuple(
        (target, profile, replacement)
        for target in Target
        for profile in AgentProfile
        for replacement in AGENT_PROFILES[target].values()
    )

    assert cases
    for target, profile, replacement in cases:
        profiles = {
            **AGENT_PROFILES,
            target: {**AGENT_PROFILES[target], profile: replacement},
        }
        assert resolve_profile(target, profile, profiles=profiles) is replacement


def test_foreign_harness_configurations_are_rejected() -> None:
    cases = tuple(
        (target, profile, configuration)
        for target in Target
        for foreign_target in set(Target) - {target}
        for profile in AgentProfile
        for configuration in AGENT_PROFILES[foreign_target].values()
    )

    assert cases
    for target, profile, configuration in cases:
        profiles = {
            **AGENT_PROFILES,
            target: {**AGENT_PROFILES[target], profile: configuration},
        }
        with pytest.raises(ProfileConfigurationError):
            resolve_profile(target, profile, profiles=profiles)


def test_incomplete_profile_registries_are_rejected() -> None:
    targets = tuple(Target)
    omissions = tuple(AgentProfile)

    assert targets
    assert omissions
    for target in targets:
        with pytest.raises(ProfileConfigurationError):
            resolve_profile(target, profiles={target: AGENT_PROFILES[target]})
        for omitted in omissions:
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
    assert NATIVE_CONFIGURATION_FIELDS
    for field in NATIVE_CONFIGURATION_FIELDS:
        with pytest.raises(ProfileConfigurationError):
            reject_configuration_overrides({field: None})


def test_absent_native_control_is_rejected_for_every_configuration() -> None:
    configurations = tuple(
        configuration
        for target in Target
        for configuration in AGENT_PROFILES[target].values()
    )

    assert configurations
    for configuration in configurations:
        controls = fields(configuration)
        assert controls
        for control in controls:
            with pytest.raises(ProfileConfigurationError):
                # Deliberately violate the constructor type to exercise runtime rejection.
                replace(configuration, **{control.name: None})  # type: ignore[arg-type]
