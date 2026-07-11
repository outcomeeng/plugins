"""Import-safe distribution contracts shared by validation and build code."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

TEXT_FILE_SUFFIXES: Final = frozenset(
    {".md", ".py", ".sh", ".json", ".toml", ".yml", ".yaml"}
)
DIST_DIR_NAME: Final = "dist"
REQUIRE_SKILL_GUIDANCE_TEMPLATE: Final = (
    "Invoke the `{skill_ref}` skill before proceeding. If that skill is "
    "unavailable, report the missing skill and continue with the closest "
    "available workflow."
)


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
