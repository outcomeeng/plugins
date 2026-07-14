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
