"""Every model identity the product selects, for subagent profiles and for evals."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Final


class AgentProfile(StrEnum):
    """The closed set of centrally selected capability and cost profiles."""

    STANDARD = "standard"
    STRONG = "strong"
    FAST = "fast"


class ClaudeModel(StrEnum):
    """Claude model identities the profiles select from."""

    OPUS_5_5 = "claude-opus-5-5"
    SONNET_5_5 = "claude-sonnet-5-5"


class ClaudeEffort(StrEnum):
    """Claude effort levels the profiles select from."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CodexModel(StrEnum):
    """Codex model identities the profiles select from."""

    TERRA = "gpt-5.6-terra"
    SOL = "gpt-5.6-sol"
    LUNA = "gpt-5.6-luna"


class CodexReasoningEffort(StrEnum):
    """Codex reasoning levels the profiles select from."""

    HIGH = "high"


@dataclass(frozen=True)
class ClaudeModelSelection:
    """One Claude model at one effort level."""

    model: ClaudeModel
    effort: ClaudeEffort


@dataclass(frozen=True)
class CodexModelSelection:
    """One Codex model at one reasoning level."""

    model: CodexModel
    reasoning_effort: CodexReasoningEffort


@dataclass(frozen=True)
class SubagentProfileModels:
    """The model selection one subagent profile makes for each harness."""

    claude: ClaudeModelSelection
    codex: CodexModelSelection


SUBAGENT_PROFILE_MODELS: Final[Mapping[AgentProfile, SubagentProfileModels]] = (
    MappingProxyType(
        {
            AgentProfile.STANDARD: SubagentProfileModels(
                claude=ClaudeModelSelection(ClaudeModel.OPUS_5_5, ClaudeEffort.MEDIUM),
                codex=CodexModelSelection(CodexModel.TERRA, CodexReasoningEffort.HIGH),
            ),
            AgentProfile.STRONG: SubagentProfileModels(
                claude=ClaudeModelSelection(ClaudeModel.OPUS_5_5, ClaudeEffort.HIGH),
                codex=CodexModelSelection(CodexModel.SOL, CodexReasoningEffort.HIGH),
            ),
            AgentProfile.FAST: SubagentProfileModels(
                claude=ClaudeModelSelection(ClaudeModel.SONNET_5_5, ClaudeEffort.LOW),
                codex=CodexModelSelection(CodexModel.LUNA, CodexReasoningEffort.HIGH),
            ),
        }
    )
)

EVAL_PROFILE_MODELS: Final[Mapping[AgentProfile, ClaudeModelSelection]] = (
    MappingProxyType(
        {
            AgentProfile.STANDARD: ClaudeModelSelection(
                ClaudeModel.OPUS_5_5, ClaudeEffort.MEDIUM
            ),
            AgentProfile.STRONG: ClaudeModelSelection(
                ClaudeModel.OPUS_5_5, ClaudeEffort.HIGH
            ),
            AgentProfile.FAST: ClaudeModelSelection(
                ClaudeModel.SONNET_5_5, ClaudeEffort.LOW
            ),
        }
    )
)

_CLAUDE_MODEL_PREFIX: Final = "claude-"
_CODEX_MODEL_PREFIX: Final = "gpt-"
_MODEL_SEGMENT_SEPARATOR: Final = "-"

MODEL_IDENTIFIERS: Final = frozenset(
    str(model) for models in (CodexModel, ClaudeModel) for model in models
)
CLAUDE_MODEL_FAMILIES: Final = frozenset(
    model.removeprefix(_CLAUDE_MODEL_PREFIX).split(_MODEL_SEGMENT_SEPARATOR, 1)[0]
    for model in ClaudeModel
)
MODEL_IDENTIFIER_PATTERN: Final = re.compile(
    r"(?<![\w-])(?:"
    + "|".join(
        re.escape(identifier)
        for identifier in sorted(MODEL_IDENTIFIERS | CLAUDE_MODEL_FAMILIES)
    )
    + "|"
    + re.escape(_CODEX_MODEL_PREFIX)
    + r"\d[\w.-]*|"
    + re.escape(_CLAUDE_MODEL_PREFIX)
    + "(?:"
    + "|".join(re.escape(family) for family in sorted(CLAUDE_MODEL_FAMILIES))
    + r")(?:-[\w.-]+)?|"
    + re.escape(_CLAUDE_MODEL_PREFIX)
    + r"[a-z]+-\d[\w.-]*)(?![\w-])",
    re.IGNORECASE,
)
