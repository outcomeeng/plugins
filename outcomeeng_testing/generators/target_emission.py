"""Command inputs derived from the source-tree scenario domain."""

from outcomeeng.distribution.build import CLAUDE_SKILL_DIR_TOKEN, CODEX_SKILL_DIR_TOKEN
from outcomeeng.distribution.contracts import (
    MARKDOWN_FILE_SUFFIX,
    REFERENCES_SUBDIR_NAME,
    SKILL_FILENAME,
)
from outcomeeng_testing.generators.source_and_templating import source_scenarios


def execution_time_commands() -> tuple[str, ...]:
    """Vary direct and variable-qualified sibling references over source scenarios."""
    return tuple(
        command
        for case in source_scenarios()
        for path in (
            f"../{case.skill}/{SKILL_FILENAME}",
            f"../{case.skill}/*",
            f"../{case.skill}/{REFERENCES_SUBDIR_NAME}/{case.outer_topic}{MARKDOWN_FILE_SUFFIX}",
        )
        for command in (
            f"{case.inner_topic} {path}",
            f"{case.inner_topic} {CLAUDE_SKILL_DIR_TOKEN}/{path}",
            f"{case.inner_topic} {CODEX_SKILL_DIR_TOKEN}/{path}",
        )
    )
