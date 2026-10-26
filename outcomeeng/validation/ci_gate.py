"""Source-owned CI quality-gate toolchain contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from outcomeeng.validation._steps import RECIPE_TEST_L3
from outcomeeng.validation.selected_gate import RECIPE_CHECK_FULL

GATE_JOB_NAME: Final = "check"
PYTHON_SETUP_STEP_NAME: Final = "Set up Python"
PINNED_VERSION_ENVIRONMENT_SUFFIX: Final = "_VERSION"
GATE_PULL_REQUEST_EVENT: Final = "pull_request"
GATE_PUSH_EVENT: Final = "push"
GATE_PUSH_BRANCH: Final = "main"
JUST_BINARY: Final = "just"
GATE_RECIPE_COMMAND: Final = f"{JUST_BINARY} {RECIPE_CHECK_FULL}"
# The gate job runs every L3 test after the full gate, in the same job, so a
# red full gate stops the job before an L3 test spends a credential.
L3_RECIPE_COMMAND: Final = f"{JUST_BINARY} {RECIPE_TEST_L3}"
GATE_RECIPE_COMMANDS: Final = (GATE_RECIPE_COMMAND, L3_RECIPE_COMMAND)
GITHUB_TOKEN_ENVIRONMENT: Final = "GH_TOKEN"
CODEX_API_KEY_ENVIRONMENT: Final = "OPENAI_API_KEY"
DISCOVERY_AUTH_MODE_ENVIRONMENT: Final = "SUBAGENT_DISCOVERY_AUTH_MODE"
SPX_REPOSITORY: Final = "outcomeeng/spx"
SPX_COMMIT_ENVIRONMENT: Final = "SPX_COMMIT"
SPX_CHECKOUT_REFERENCE: Final = f"${{{{ env.{SPX_COMMIT_ENVIRONMENT} }}}}"
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
    """One environment variable the step running a command requires."""

    run_command: str
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
    CiToolRequirement(None, "pnpm run build", "spx --version"),
    CiToolRequirement(None, "actions/checkout@", None),
    CiToolRequirement(None, "actions/setup-python@", None),
    CiToolRequirement(None, "actions/setup-node@", None),
)
# Only the L3 tests read these credentials, so only the step whose command
# runs them receives them.
CI_STEP_ENVIRONMENT_REQUIREMENTS: Final = (
    CiStepEnvironmentRequirement(L3_RECIPE_COMMAND, GITHUB_TOKEN_ENVIRONMENT),
    CiStepEnvironmentRequirement(L3_RECIPE_COMMAND, CODEX_API_KEY_ENVIRONMENT),
    CiStepEnvironmentRequirement(L3_RECIPE_COMMAND, DISCOVERY_AUTH_MODE_ENVIRONMENT),
)
RETIRED_SPX_VERSION_ENVIRONMENT: Final = "SPX_VERSION"
FULL_COMMIT_SHA_PATTERN: Final = r"[0-9a-f]{40}"
MAXIMUM_JOB_TIMEOUT_MINUTES: Final = 30
REUSABLE_WORKFLOW_CALL_KEY: Final = "uses"
JOB_TIMEOUT_KEY: Final = "timeout-minutes"
WORKFLOW_FILE_GLOBS: Final = ("*.yml", "*.yaml")


__all__ = [
    "CI_STEP_ENVIRONMENT_REQUIREMENTS",
    "CODEX_API_KEY_ENVIRONMENT",
    "DISCOVERY_AUTH_MODE_ENVIRONMENT",
    "GITHUB_TOKEN_ENVIRONMENT",
    "CI_TOOL_REQUIREMENTS",
    "FULL_COMMIT_SHA_PATTERN",
    "RETIRED_SPX_VERSION_ENVIRONMENT",
    "SPX_CHECKOUT_REFERENCE",
    "SPX_COMMIT_ENVIRONMENT",
    "SPX_REPOSITORY",
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
    "GATE_RECIPE_COMMANDS",
    "JUST_BINARY",
    "L3_RECIPE_COMMAND",
    "PINNED_VERSION_ENVIRONMENT_SUFFIX",
    "PYTHON_SETUP_STEP_NAME",
    "SOFT_PASS_SHELL_SNIPPETS",
    "TRAP_COMMAND_PREFIX",
    "WORKFLOW_FILE_GLOBS",
    "CiStepEnvironmentRequirement",
    "CiToolRequirement",
]
