"""Central profiles and complete harness-native agent configurations."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from outcomeeng.distribution.contracts import Target
from outcomeeng.models import (
    SUBAGENT_PROFILE_MODELS,
    AgentProfile,
    ClaudeEffort,
    ClaudeModel,
    CodexModel,
    CodexReasoningEffort,
)

PROFILE_FIELD: Final = "profile"


class ProfileSyntax(StrEnum):
    """Serialization surfaces for complete configuration examples."""

    YAML = "yaml"
    TOML = "toml"
    JSON = "json"


class ProfileConfigurationError(ValueError):
    """A selection or native configuration violates the profile contract."""


@dataclass(frozen=True)
class CodexConfiguration:
    """A complete native configuration with mandatory reasoning selection."""

    model: CodexModel
    model_reasoning_effort: CodexReasoningEffort

    def __post_init__(self) -> None:
        if not isinstance(self.model, CodexModel) or not isinstance(
            self.model_reasoning_effort, CodexReasoningEffort
        ):
            raise ProfileConfigurationError("invalid native Codex configuration")


@dataclass(frozen=True)
class ClaudeConfiguration:
    """A complete native configuration with mandatory effort selection."""

    model: ClaudeModel
    effort: ClaudeEffort

    def __post_init__(self) -> None:
        if not isinstance(self.model, ClaudeModel) or not isinstance(
            self.effort, ClaudeEffort
        ):
            raise ProfileConfigurationError("invalid native Claude configuration")


type NativeConfiguration = CodexConfiguration | ClaudeConfiguration
type ProfileRegistry = Mapping[Target, Mapping[AgentProfile, NativeConfiguration]]

NATIVE_CONFIGURATION_TYPES: Final = MappingProxyType(
    {Target.CODEX: CodexConfiguration, Target.CLAUDE: ClaudeConfiguration}
)
NATIVE_CONFIGURATION_FIELDS: Final = frozenset(
    field.name
    for configuration_type in NATIVE_CONFIGURATION_TYPES.values()
    for field in fields(configuration_type)
)
AGENT_PROFILES: Final[ProfileRegistry] = MappingProxyType(
    {
        Target.CODEX: MappingProxyType(
            {
                profile: CodexConfiguration(
                    models.codex.model, models.codex.reasoning_effort
                )
                for profile, models in SUBAGENT_PROFILE_MODELS.items()
            }
        ),
        Target.CLAUDE: MappingProxyType(
            {
                profile: ClaudeConfiguration(models.claude.model, models.claude.effort)
                for profile, models in SUBAGENT_PROFILE_MODELS.items()
            }
        ),
    }
)


def resolve_profile(
    target: Target,
    profile: str | None = None,
    *,
    profiles: ProfileRegistry = AGENT_PROFILES,
) -> NativeConfiguration:
    """Resolve one profile directly, rejecting incomplete or foreign registries."""
    try:
        selected = AgentProfile.STANDARD if profile is None else AgentProfile(profile)
    except ValueError as exc:
        raise ProfileConfigurationError(f"unknown agent profile: {profile!r}") from exc
    if set(profiles) != set(Target):
        raise ProfileConfigurationError(
            "profiles must cover exactly the supported harnesses"
        )
    for harness, configurations in profiles.items():
        if set(configurations) != set(AgentProfile):
            raise ProfileConfigurationError(
                f"{harness}: profiles must contain exactly Standard, Strong, and Fast"
            )
        for name, configuration in configurations.items():
            if not isinstance(configuration, NATIVE_CONFIGURATION_TYPES[harness]):
                raise ProfileConfigurationError(
                    f"{harness}/{name}: incompatible native configuration"
                )
    return profiles[target][selected]


def native_configuration_values(configuration: NativeConfiguration) -> dict[str, str]:
    """Expose only the controls present in the complete native configuration."""
    return {
        key: str(value)
        for key, value in asdict(configuration).items()
        if value is not None
    }


def reject_configuration_overrides(values: Mapping[str, object]) -> None:
    """Reject authored native fields even when their values use templates."""
    overrides = sorted(NATIVE_CONFIGURATION_FIELDS.intersection(values))
    if overrides:
        raise ProfileConfigurationError(
            f"native configuration overrides are forbidden; select a profile: {', '.join(overrides)}"
        )


def render_profile_configuration(
    target: Target,
    profile: str | None = None,
    *,
    syntax: ProfileSyntax | None = None,
    profiles: ProfileRegistry = AGENT_PROFILES,
) -> str:
    """Serialize a complete profile as native configuration or a JSON object."""
    values = native_configuration_values(
        resolve_profile(target, profile, profiles=profiles)
    )
    if syntax is None:
        selected_syntax = (
            ProfileSyntax.TOML if target is Target.CODEX else ProfileSyntax.YAML
        )
    else:
        selected_syntax = ProfileSyntax(syntax)
    if selected_syntax is ProfileSyntax.JSON:
        return json.dumps(values, ensure_ascii=False)
    separator = " = " if selected_syntax is ProfileSyntax.TOML else ": "
    return "\n".join(
        f"{key}{separator}{json.dumps(value, ensure_ascii=False)}"
        for key, value in values.items()
    )


def describe_profile(
    target: Target,
    profile: str | None = None,
    *,
    profiles: ProfileRegistry = AGENT_PROFILES,
) -> str:
    """Describe the entire native configuration without losing omitted controls."""
    configuration = resolve_profile(target, profile, profiles=profiles)
    values = native_configuration_values(configuration)
    return ", ".join(
        f"`{field.name}={values[field.name]}`"
        if field.name in values
        else f"no `{field.name}` field"
        for field in fields(configuration)
    )
