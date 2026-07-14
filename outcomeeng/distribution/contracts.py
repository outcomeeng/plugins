"""Import-safe distribution contracts shared by validation and build code."""

from __future__ import annotations

from enum import StrEnum
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
REFERENCES_SUBDIR_NAME: Final = "references"
SKILL_FILENAME: Final = "SKILL.md"
MARKDOWN_FILE_SUFFIX: Final = ".md"
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


SOURCE_ROOT_NAME: Final = "src"
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
