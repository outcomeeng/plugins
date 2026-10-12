"""Central profiles and complete harness-native agent configurations."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from outcomeeng.distribution.contracts import Target

PROFILE_FIELD: Final = "profile"


class AgentProfile(StrEnum):
    """The closed set of centrally selected capability and cost profiles."""

    STANDARD = "standard"
    STRONG = "strong"
    EXECUTOR = "executor"
    FAST = "fast"


class CodexModel(StrEnum):
    """Model identities available to the central native profiles."""

    SOL = "gpt-6.1-sol"
    ASTRA = "gpt-6-astra"
    LUNA = "gpt-6-luna"


class ClaudeModel(StrEnum):
    """Model identities available to the central native profiles."""

    OPUS = "opus"
    SONNET = "sonnet"
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
CODEX_STANDARD_CONFIGURATION: Final = CodexConfiguration(
    CodexModel.SOL, CodexReasoningEffort.HIGH
)
AGENT_PROFILES: Final[ProfileRegistry] = MappingProxyType(
    {
        Target.CODEX: MappingProxyType(
            {
                AgentProfile.STANDARD: CODEX_STANDARD_CONFIGURATION,
                AgentProfile.STRONG: CodexConfiguration(
                    CodexModel.ASTRA, CodexReasoningEffort.HIGH
                ),
                AgentProfile.EXECUTOR: CODEX_STANDARD_CONFIGURATION,
                AgentProfile.FAST: CodexConfiguration(
                    CodexModel.LUNA, CodexReasoningEffort.HIGH
                ),
            }
        ),
        Target.CLAUDE: MappingProxyType(
            {
                AgentProfile.STANDARD: ClaudeConfiguration(
                    ClaudeModel.SONNET, ClaudeEffort.MEDIUM
                ),
                AgentProfile.STRONG: ClaudeConfiguration(
                    ClaudeModel.OPUS, ClaudeEffort.HIGH
                ),
                AgentProfile.EXECUTOR: ClaudeConfiguration(
                    ClaudeModel.SONNET, ClaudeEffort.HIGH
                ),
                AgentProfile.FAST: ClaudeConfiguration(ClaudeModel.HAIKU, None),
            }
        ),
    }
)


class UsageTokenClass(StrEnum):
    """Usage token classes a model price covers."""

    INPUT = "input"
    CACHE_READ = "cache_read"
    CACHE_WRITE_5M = "cache_write_5m"
    CACHE_WRITE_1H = "cache_write_1h"
    OUTPUT = "output"


class UnpricedModelError(LookupError):
    """A model identifier that no price entry names."""


@dataclass(frozen=True)
class ModelPrice:
    """Prices in USD per million tokens, one for every usage token class."""

    input: Decimal
    cache_read: Decimal
    cache_write_5m: Decimal
    cache_write_1h: Decimal
    output: Decimal

    def rate(self, token_class: UsageTokenClass) -> Decimal:
        """Return the price of one usage token class."""
        return Decimal(getattr(self, UsageTokenClass(token_class).value))


def _price(*rates: str) -> ModelPrice:
    return ModelPrice(*(Decimal(rate) for rate in rates))


MODEL_PRICES: Final[Mapping[ClaudeModel, Mapping[str, ModelPrice]]] = MappingProxyType(
    {
        ClaudeModel.OPUS: MappingProxyType(
            {
                "claude-opus-5-5": _price("4", ".2", "5", "8", "20"),
                "claude-opus-4-6": _price("5", ".5", "6.25", "10", "25"),
            }
        ),
        ClaudeModel.SONNET: MappingProxyType(
            {
                "claude-sonnet-5-5": _price("2", ".1", "2.5", "4", "10"),
                "claude-sonnet-4-6": _price("3", ".3", "3.75", "6", "15"),
            }
        ),
    }
)


def resolve_model_price(
    identifier: str,
    *,
    prices: Mapping[ClaudeModel, Mapping[str, ModelPrice]] = MODEL_PRICES,
) -> ModelPrice:
    """Resolve a price by exact model identifier, with no fallback."""
    for entries in prices.values():
        if identifier in entries:
            return entries[identifier]
    raise UnpricedModelError(f"unpriced model identifier: {identifier!r}")


MODEL_PRICES_VARIABLE: Final = "model_prices_json"
MODEL_PRICES_DOCUMENT_KEY: Final = "prices"


def model_price_document(
    prices: Mapping[ClaudeModel, Mapping[str, ModelPrice]] = MODEL_PRICES,
) -> dict[str, dict[str, dict[str, str]]]:
    """Return every price entry as the document the build renders for shipped skills."""
    return {
        MODEL_PRICES_DOCUMENT_KEY: {
            identifier: {
                token_class.value: str(price.rate(token_class))
                for token_class in UsageTokenClass
            }
            for entries in prices.values()
            for identifier, price in entries.items()
        }
    }


def model_price_render_variables() -> dict[str, object]:
    """Return the build variable carrying the rendered price document."""
    return {MODEL_PRICES_VARIABLE: json.dumps(model_price_document(), indent=2)}


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
                f"{harness}: profiles must contain exactly "
                + ", ".join(str(profile) for profile in AgentProfile)
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
