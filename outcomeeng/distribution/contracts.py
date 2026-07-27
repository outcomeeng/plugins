"""Import-safe distribution contracts shared by validation and build code."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Final

TEXT_FILE_SUFFIXES: Final = frozenset(
    {".md", ".py", ".sh", ".json", ".toml", ".yml", ".yaml"}
)
BUILD_BLOCK_DELIMITER_START: Final = "{!%"
BUILD_BLOCK_DELIMITER_END: Final = "%!}"
BUILD_VARIABLE_DELIMITER_START: Final = "{{!"
BUILD_VARIABLE_DELIMITER_END: Final = "!}}"
BUILD_COMMENT_DELIMITER_START: Final = "{!#"
BUILD_COMMENT_DELIMITER_END: Final = "#!}"
STANDARD_JINJA_BLOCK_DELIMITER_START: Final = "{%"
STANDARD_JINJA_BLOCK_DELIMITER_END: Final = "%}"
STANDARD_JINJA_VARIABLE_DELIMITER_START: Final = "{{"
STANDARD_JINJA_VARIABLE_DELIMITER_END: Final = "}}"
BUILD_TARGET_VARIABLE: Final = "target"
SPX_FLOOR_VARIABLE: Final = "spx_floor"
PLUGIN_NAME_VARIABLE: Final = "plugin_name"
DIST_DIR_NAME: Final = "dist"
PLUGINS_DIR_NAME: Final = "plugins"
SKILLS_SUBDIR_NAME: Final = "skills"
AGENTS_SUBDIR_NAME: Final = "agents"
SCRIPTS_SUBDIR_NAME: Final = "scripts"
HOOKS_SUBDIR_NAME: Final = "hooks"
CLAUDE_PLUGIN_SUBDIR_NAME: Final = ".claude-plugin"
CODEX_PLUGIN_SUBDIR_NAME: Final = ".codex-plugin"
CODEX_PLUGIN_MANIFEST: Final = Path(CODEX_PLUGIN_SUBDIR_NAME) / "plugin.json"
DIST_CODEX_PLUGINS_DIR: Final = Path(DIST_DIR_NAME) / "codex"
REFERENCES_SUBDIR_NAME: Final = "references"
SKILL_FILENAME: Final = "SKILL.md"
MARKDOWN_FILE_SUFFIX: Final = ".md"
GIT_METADATA_DIR_NAME: Final = ".git"
SKILL_NAME_FIELD: Final = "name"
SKILL_DESCRIPTION_FIELD: Final = "description"
COLLECTED_SKILL_SOURCE_FIELD: Final = "source"
COLLECTED_SKILL_DIR_NAME_FIELD: Final = "dir_name"
FRONTMATTER_DELIMITER: Final = "---"
DIRECTIVE_DESCRIPTION_PREFIX: Final = "ALWAYS invoke this skill when "
DIRECTIVE_DESCRIPTION_BOUNDARY: Final = ". NEVER"
SENTENCE_TERMINATOR: Final = "."
RECURSIVE_GLOB: Final = "**"
PLUGIN_SUBDIRS: Final = frozenset(
    {
        SKILLS_SUBDIR_NAME,
        AGENTS_SUBDIR_NAME,
        SCRIPTS_SUBDIR_NAME,
        HOOKS_SUBDIR_NAME,
        CLAUDE_PLUGIN_SUBDIR_NAME,
        CODEX_PLUGIN_SUBDIR_NAME,
    }
)
REQUIRE_SKILL_GUIDANCE_TEMPLATE: Final = (
    "Invoke the `{skill_ref}` skill before proceeding. If that skill is "
    "unavailable, report the missing skill and continue with the closest "
    "available workflow."
)


def build_variable_token(variable: str) -> str:
    """Return the authored-source token for one build render variable."""
    return f"{BUILD_VARIABLE_DELIMITER_START} {variable} {BUILD_VARIABLE_DELIMITER_END}"


def format_runtime_token(kind: str, capability: str, runtime: str | None = None) -> str:
    """Return the authored template token for one runtime registry capability.

    Mirrors the template global's own signature: the default form renders the
    build target's name, while a runtime-explicit second argument renders the
    named runtime's name regardless of target.
    """
    arguments = f"{capability!r}" if runtime is None else f"{capability!r}, {runtime!r}"
    return (
        f"{BUILD_VARIABLE_DELIMITER_START} {kind}({arguments}) "
        f"{BUILD_VARIABLE_DELIMITER_END}"
    )


class Target(StrEnum):
    """Generated output target."""

    CLAUDE = "claude"
    CODEX = "codex"


RUNTIME_TOKEN_TOOL_KIND: Final = "tool"
RUNTIME_TOKEN_FIELD_KIND: Final = "field"
RUNTIME_TOKEN_TERM_KIND: Final = "term"
RUNTIME_TOKEN_FILE_KIND: Final = "file"
RUNTIME_TOKEN_KIND_GUARD_ENFORCEMENT: Final[dict[str, bool]] = {
    RUNTIME_TOKEN_TOOL_KIND: True,
    RUNTIME_TOKEN_FIELD_KIND: True,
    RUNTIME_TOKEN_TERM_KIND: False,
    RUNTIME_TOKEN_FILE_KIND: True,
}

RUNTIME_TOKEN_ASK_USER_CAPABILITY: Final = "ask_user"
RUNTIME_TOKEN_SPAWN_AGENT_CAPABILITY: Final = "spawn_agent"
RUNTIME_TOKEN_WAIT_AGENT_CAPABILITY: Final = "wait_agent"
RUNTIME_TOKEN_CLOSE_AGENT_CAPABILITY: Final = "close_agent"
RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY: Final = "schedule_wakeup"
RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY: Final = "configured_agent_prompt"
RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY: Final = "configured_agent"
RUNTIME_TOKEN_CONFIGURED_AGENT_STANDARD_MODEL_CAPABILITY: Final = (
    "configured_agent_standard_model"
)
RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_MODEL_CAPABILITY: Final = (
    "configured_agent_fast_model"
)
RUNTIME_TOKEN_CONFIGURED_AGENT_AUDITOR_MODEL_CAPABILITY: Final = (
    "configured_agent_auditor_model"
)
RUNTIME_TOKEN_CONFIGURED_AGENT_STRONG_MODELS_CAPABILITY: Final = (
    "configured_agent_strong_models"
)
RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_OR_STANDARD_MODELS_CAPABILITY: Final = (
    "configured_agent_fast_or_standard_models"
)
RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY: Final = "root_guide"

RUNTIME_TOKEN_ASK_USER_NAMES: Final[dict[str, str]] = {
    Target.CLAUDE.value: "AskUserQuestion",
    Target.CODEX.value: "request_user_input",
}
RUNTIME_TOKEN_SPAWN_AGENT_NAMES: Final[dict[str, str]] = {
    Target.CODEX.value: "multi_agent_v1.spawn_agent",
}
RUNTIME_TOKEN_WAIT_AGENT_NAMES: Final[dict[str, str]] = {
    Target.CODEX.value: "multi_agent_v1.wait_agent",
}
RUNTIME_TOKEN_CLOSE_AGENT_NAMES: Final[dict[str, str]] = {
    Target.CODEX.value: "multi_agent_v1.close_agent",
}
RUNTIME_TOKEN_SCHEDULE_WAKEUP_NAMES: Final[dict[str, str]] = {
    Target.CLAUDE.value: "ScheduleWakeup",
}
RUNTIME_TOKEN_ROOT_GUIDE_NAMES: Final[dict[str, str]] = {
    Target.CLAUDE.value: "CLAUDE.md",
    Target.CODEX.value: "AGENTS.md",
}
RUNTIME_TOKEN_REQUIRED_NAMES: Final[dict[tuple[str, str], dict[str, str]]] = {
    (RUNTIME_TOKEN_TOOL_KIND, RUNTIME_TOKEN_ASK_USER_CAPABILITY): (
        RUNTIME_TOKEN_ASK_USER_NAMES
    ),
    (RUNTIME_TOKEN_TOOL_KIND, RUNTIME_TOKEN_SPAWN_AGENT_CAPABILITY): (
        RUNTIME_TOKEN_SPAWN_AGENT_NAMES
    ),
    (RUNTIME_TOKEN_TOOL_KIND, RUNTIME_TOKEN_WAIT_AGENT_CAPABILITY): (
        RUNTIME_TOKEN_WAIT_AGENT_NAMES
    ),
    (RUNTIME_TOKEN_TOOL_KIND, RUNTIME_TOKEN_CLOSE_AGENT_CAPABILITY): (
        RUNTIME_TOKEN_CLOSE_AGENT_NAMES
    ),
    (RUNTIME_TOKEN_TOOL_KIND, RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY): (
        RUNTIME_TOKEN_SCHEDULE_WAKEUP_NAMES
    ),
    (RUNTIME_TOKEN_FILE_KIND, RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY): (
        RUNTIME_TOKEN_ROOT_GUIDE_NAMES
    ),
}


def format_target_branches(
    branches: tuple[tuple[Target, str], ...],
    *,
    fallback: str | None = None,
) -> str:
    """Return one authored per-target conditional over ``branches``."""
    if not branches:
        msg = "at least one target branch is required"
        raise ValueError(msg)

    lines: list[str] = []
    for index, (target, body) in enumerate(branches):
        keyword = "if" if index == 0 else "elif"
        lines.extend(
            (
                f"{BUILD_BLOCK_DELIMITER_START} {keyword} "
                f"{BUILD_TARGET_VARIABLE} == {target.value!r} "
                f"{BUILD_BLOCK_DELIMITER_END}",
                body,
            )
        )
    if fallback is not None:
        lines.extend(
            (
                f"{BUILD_BLOCK_DELIMITER_START} else {BUILD_BLOCK_DELIMITER_END}",
                fallback,
            )
        )
    lines.append(f"{BUILD_BLOCK_DELIMITER_START} endif {BUILD_BLOCK_DELIMITER_END}")
    return "\n".join(lines)


def format_target_conditional(target: Target, body: str) -> str:
    """Return an authored conditional whose body belongs to one target."""
    return format_target_branches(((target, body),))


SOURCE_ROOT_NAME: Final = "src"
CLAUDE_DIST_RELATIVE: Final = Path(DIST_DIR_NAME) / Target.CLAUDE.value
DISTRIBUTION_WORKFLOW_RELATIVE: Final = (
    Path(".github") / "workflows" / "distribute-skills.yml"
)
PROJECT_METADATA_RELATIVE: Final = Path("pyproject.toml")
WORKFLOW_ON_FIELD: Final = "on"
WORKFLOW_PUSH_FIELD: Final = "push"
WORKFLOW_PATHS_FIELD: Final = "paths"
WORKFLOW_JOBS_FIELD: Final = "jobs"
WORKFLOW_DISTRIBUTION_JOB: Final = "distribute"
WORKFLOW_STEPS_FIELD: Final = "steps"
WORKFLOW_STEP_NAME_FIELD: Final = "name"
WORKFLOW_SETUP_PYTHON_STEP: Final = "Set up Python"
WORKFLOW_WITH_FIELD: Final = "with"
WORKFLOW_PYTHON_VERSION_FIELD: Final = "python-version"
PROJECT_FIELD: Final = "project"
PROJECT_REQUIRES_PYTHON_FIELD: Final = "requires-python"
MINIMUM_VERSION_PREFIX: Final = ">="
BUILD_MODULE_NAME: Final = "outcomeeng.distribution.build"
BUILD_COMMAND_ARGV: Final = (
    "uv",
    "run",
    "--no-cache",
    "python",
    "-m",
    BUILD_MODULE_NAME,
    SOURCE_ROOT_NAME,
    DIST_DIR_NAME,
)
DIST_DIFF_MODULE_NAME: Final = "outcomeeng.distribution.dist_diff"
DIST_DIFF_ARGV: Final = ("uv", "run", "python", "-m", DIST_DIFF_MODULE_NAME)
INSTRUCTION_BLOCK_MODULE_NAME: Final = "outcomeeng.distribution.instruction_block"
INSTRUCTION_BLOCK_ARGV: Final = (
    "uv",
    "run",
    "python",
    "-m",
    INSTRUCTION_BLOCK_MODULE_NAME,
)
ORCHESTRATION_VALIDATION_ARGV: Final = (
    "uv",
    "run",
    "python",
    "-m",
    "outcomeeng.validation.build_orchestration",
    ".",
)
