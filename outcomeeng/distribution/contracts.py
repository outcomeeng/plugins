"""Import-safe distribution contracts shared by validation and build code."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

TEXT_FILE_SUFFIXES: Final = frozenset(
    {".md", ".py", ".sh", ".json", ".toml", ".yml", ".yaml"}
)
DIST_DIR_NAME: Final = "dist"


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
GUIDE_DIFF_MODULE_NAME: Final = "outcomeeng.distribution.guide_diff"
GUIDE_DIFF_ARGV: Final = ("uv", "run", "python", "-m", GUIDE_DIFF_MODULE_NAME)
ORCHESTRATION_VALIDATION_ARGV: Final = (
    "uv",
    "run",
    "python",
    "-m",
    "outcomeeng.validation.build_orchestration",
    ".",
)
