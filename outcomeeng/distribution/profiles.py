"""Central profiles and complete harness-native agent configurations."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from outcomeeng.distribution.contracts import Target

PROFILE_FIELD: Final = "profile"


class AgentProfile(StrEnum):
    """The closed set of centrally selected capability and cost profiles."""

    STANDARD = "standard"
    STRONG = "strong"
    FAST = "fast"


class CodexModel(StrEnum):
    """Model identities available to the central native profiles."""

    TERRA = "gpt-5.6-terra"
    SOL = "gpt-5.6-sol"
    LUNA = "gpt-5.6-luna"


class ClaudeModel(StrEnum):
    """Model identities available to the central native profiles."""

    OPUS = "opus"
    HAIKU = "haiku"


class CodexReasoningEffort(StrEnum):
    """Native reasoning controls used by the supported profiles."""

    HIGH = "high"


class ClaudeEffort(StrEnum):
    """Native effort controls used by the supported profiles."""

    MEDIUM = "medium"
    HIGH = "high"


MODEL_IDENTIFIERS: Final = frozenset(
    str(model) for models in (CodexModel, ClaudeModel) for model in models
)
MODEL_IDENTIFIER_PATTERN: Final = re.compile(
    r"(?<![\w-])(?:"
    + "|".join(re.escape(model) for model in sorted(MODEL_IDENTIFIERS))
    + r"|gpt-\d[\w.-]*|claude-(?:"
    + "|".join(re.escape(model) for model in ClaudeModel)
    + r")(?:-[\w.-]+)?|claude-[a-z]+-\d[\w.-]*)(?![\w-])",
    re.IGNORECASE,
)


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
    """A complete native configuration, including intentional control absence."""

    model: ClaudeModel
    effort: ClaudeEffort | None

    def __post_init__(self) -> None:
        if not isinstance(self.model, ClaudeModel):
            raise ProfileConfigurationError("invalid native Claude model")
        if self.model is ClaudeModel.HAIKU:
            if self.effort is not None:
                raise ProfileConfigurationError(
                    "the selected model has no effort control"
                )
        elif not isinstance(self.effort, ClaudeEffort):
            raise ProfileConfigurationError("the selected model requires native effort")


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
                AgentProfile.STANDARD: CodexConfiguration(
                    CodexModel.TERRA, CodexReasoningEffort.HIGH
                ),
                AgentProfile.STRONG: CodexConfiguration(
                    CodexModel.SOL, CodexReasoningEffort.HIGH
                ),
                AgentProfile.FAST: CodexConfiguration(
                    CodexModel.LUNA, CodexReasoningEffort.HIGH
                ),
            }
        ),
        Target.CLAUDE: MappingProxyType(
            {
                AgentProfile.STANDARD: ClaudeConfiguration(
                    ClaudeModel.OPUS, ClaudeEffort.MEDIUM
                ),
                AgentProfile.STRONG: ClaudeConfiguration(
                    ClaudeModel.OPUS, ClaudeEffort.HIGH
                ),
                AgentProfile.FAST: ClaudeConfiguration(ClaudeModel.HAIKU, None),
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
    selected_syntax = (
        (ProfileSyntax.TOML if target is Target.CODEX else ProfileSyntax.YAML)
        if syntax is None
        else ProfileSyntax(syntax)
    )
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
