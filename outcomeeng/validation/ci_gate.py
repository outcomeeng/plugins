"""Source-owned CI quality-gate toolchain contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class CiToolRequirement:
    """One tool the CI gate must provision and optionally verify."""

    version_environment: str | None
    provision_fragment: str
    verification_fragment: str | None


@dataclass(frozen=True)
class CiStepEnvironmentRequirement:
    """One environment variable required by a named CI gate step."""

    step_name: str
    environment_name: str


CI_TOOL_REQUIREMENTS: Final = (
    CiToolRequirement("UV_VERSION", "astral-sh/setup-uv@", None),
    CiToolRequirement(None, "oven-sh/setup-bun@", None),
    CiToolRequirement(
        "JUST_VERSION",
        "casey/just/releases/download/${JUST_VERSION}",
        "just --version",
    ),
    CiToolRequirement(
        "ACTIONLINT_VERSION",
        "rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}",
        "actionlint -version",
    ),
    CiToolRequirement(
        "SHELLCHECK_VERSION",
        "koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}",
        "shellcheck --version",
    ),
    CiToolRequirement(
        "CLAUDE_CLI_VERSION",
        "@anthropic-ai/claude-code@${CLAUDE_CLI_VERSION}",
        "claude --version",
    ),
    CiToolRequirement(
        "CODEX_CLI_VERSION",
        "@openai/codex@${CODEX_CLI_VERSION}",
        "codex --version",
    ),
    CiToolRequirement(
        "DPRINT_VERSION",
        "dprint@${DPRINT_VERSION}",
        "dprint --version",
    ),
    CiToolRequirement(
        "SPX_VERSION",
        "@outcomeeng/spx@${SPX_VERSION}",
        "spx --version",
    ),
    CiToolRequirement(None, "actions/checkout@", None),
)
CI_STEP_ENVIRONMENT_REQUIREMENTS: Final = (
    CiStepEnvironmentRequirement("Run quality gate", "GH_TOKEN"),
)


__all__ = [
    "CI_STEP_ENVIRONMENT_REQUIREMENTS",
    "CI_TOOL_REQUIREMENTS",
    "CiStepEnvironmentRequirement",
    "CiToolRequirement",
]
