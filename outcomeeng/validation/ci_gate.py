"""Source-owned CI quality-gate toolchain contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from outcomeeng.validation.selected_gate import RECIPE_CHECK_FULL

GATE_JOB_NAME: Final = "check"
PYTHON_SETUP_STEP_NAME: Final = "Set up Python"
PINNED_VERSION_ENVIRONMENT_SUFFIX: Final = "_VERSION"
GATE_PULL_REQUEST_EVENT: Final = "pull_request"
GATE_PUSH_EVENT: Final = "push"
GATE_PUSH_BRANCH: Final = "main"
JUST_BINARY: Final = "just"
GATE_RECIPE_COMMAND: Final = f"{JUST_BINARY} {RECIPE_CHECK_FULL}"
CONTINUE_ON_ERROR_FALSY: Final = (None, "false")
FAIL_FAST_PREAMBLE: Final = "set -euo pipefail"
TRAP_COMMAND_PREFIX: Final = "trap "
SOFT_PASS_SHELL_SNIPPETS: Final = (
    "|| true",
    "|| :",
    "|| exit 0",
    "set +e",
    "exit 0",
    "if !",
)


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
    CiToolRequirement(None, "actions/setup-python@", None),
)
CI_STEP_ENVIRONMENT_REQUIREMENTS: Final = (
    CiStepEnvironmentRequirement("Run quality gate", "GH_TOKEN"),
)
MAXIMUM_JOB_TIMEOUT_MINUTES: Final = 30
REUSABLE_WORKFLOW_CALL_KEY: Final = "uses"
JOB_TIMEOUT_KEY: Final = "timeout-minutes"
WORKFLOW_FILE_GLOBS: Final = ("*.yml", "*.yaml")


__all__ = [
    "CI_STEP_ENVIRONMENT_REQUIREMENTS",
    "CI_TOOL_REQUIREMENTS",
    "CONTINUE_ON_ERROR_FALSY",
    "JOB_TIMEOUT_KEY",
    "MAXIMUM_JOB_TIMEOUT_MINUTES",
    "REUSABLE_WORKFLOW_CALL_KEY",
    "FAIL_FAST_PREAMBLE",
    "GATE_JOB_NAME",
    "GATE_PULL_REQUEST_EVENT",
    "GATE_PUSH_BRANCH",
    "GATE_PUSH_EVENT",
    "GATE_RECIPE_COMMAND",
    "JUST_BINARY",
    "PINNED_VERSION_ENVIRONMENT_SUFFIX",
    "PYTHON_SETUP_STEP_NAME",
    "SOFT_PASS_SHELL_SNIPPETS",
    "TRAP_COMMAND_PREFIX",
    "WORKFLOW_FILE_GLOBS",
    "CiStepEnvironmentRequirement",
    "CiToolRequirement",
]
