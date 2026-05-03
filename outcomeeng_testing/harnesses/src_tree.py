"""Harness for materializing sample src/ plugin trees in tests.

SrcTreeBuilder writes plugins and shared topics to a given root, validating
inputs against the canonical kebab-case naming rules. Layout constants come
from outcomeeng.scripts.build_plugins so the harness stays aligned with the
production module's contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from outcomeeng.scripts.build_plugins import (
    AGENTS_SUBDIR_NAME,
    AGENT_FILE_SUFFIX,
    COMMANDS_SUBDIR_NAME,
    COMMAND_FILE_SUFFIX,
    PLUGINS_DIR_NAME,
    REFERENCES_SUBDIR_NAME,
    SHARED_DIR_NAME,
    SHARED_FRAGMENT_FILENAME,
    SKILLS_SUBDIR_NAME,
    SKILL_FILENAME,
)

SRC_DIR_NAME = "src"

# Kebab-case: starts with letter, contains lowercase letters/digits/hyphens,
# does not start or end with hyphen, no consecutive hyphens.
_KEBAB_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


def _validate_name(name: str, *, kind: str) -> None:
    if not _KEBAB_PATTERN.match(name):
        msg = (
            f"invalid {kind} name {name!r}: must be kebab-case "
            "(lowercase letters and digits separated by single hyphens, "
            "starting with a letter)"
        )
        raise ValueError(msg)


def _validate_reference_filename(filename: str) -> None:
    if "/" in filename or "\\" in filename:
        msg = f"reference filename {filename!r} must not contain path separators"
        raise ValueError(msg)
    if not filename.endswith(".md"):
        msg = f"reference filename {filename!r} must end in .md"
        raise ValueError(msg)


@dataclass(frozen=True)
class SrcTreeBuilder:
    """Construct a sample src/ tree at a given root for build tests.

    Each method writes files immediately and returns self for chaining.
    The dataclass is frozen because the only mutable state is the
    filesystem itself, not the builder instance.
    """

    root: Path

    @property
    def src_root(self) -> Path:
        return self.root / SRC_DIR_NAME

    def add_plugin(
        self,
        name: str,
        *,
        skills: Mapping[str, str] | None = None,
        commands: Mapping[str, str] | None = None,
        agents: Mapping[str, str] | None = None,
    ) -> SrcTreeBuilder:
        """Materialize a plugin at src/plugins/<name>/ with the given components.

        skills: skill-directory-name -> SKILL.md body content.
                Each entry creates src/plugins/<name>/skills/<skill>/SKILL.md.
        commands: command-name -> markdown body.
                  Each entry creates src/plugins/<name>/commands/<command>.md.
        agents: agent-name -> markdown body.
                Each entry creates src/plugins/<name>/agents/<agent>.md.

        Names are validated as kebab-case before any file is written.
        """
        _validate_name(name, kind="plugin")

        plugin_root = self.src_root / PLUGINS_DIR_NAME / name
        plugin_root.mkdir(parents=True, exist_ok=True)

        if skills:
            for skill_name in skills:
                _validate_name(skill_name, kind="skill")
            skills_root = plugin_root / SKILLS_SUBDIR_NAME
            skills_root.mkdir(exist_ok=True)
            for skill_name, content in skills.items():
                skill_dir = skills_root / skill_name
                skill_dir.mkdir(exist_ok=True)
                (skill_dir / SKILL_FILENAME).write_text(content)

        if commands:
            for command_name in commands:
                _validate_name(command_name, kind="command")
            commands_root = plugin_root / COMMANDS_SUBDIR_NAME
            commands_root.mkdir(exist_ok=True)
            for command_name, content in commands.items():
                (commands_root / f"{command_name}{COMMAND_FILE_SUFFIX}").write_text(
                    content
                )

        if agents:
            for agent_name in agents:
                _validate_name(agent_name, kind="agent")
            agents_root = plugin_root / AGENTS_SUBDIR_NAME
            agents_root.mkdir(exist_ok=True)
            for agent_name, content in agents.items():
                (agents_root / f"{agent_name}{AGENT_FILE_SUFFIX}").write_text(content)

        return self

    def add_shared_topic(
        self,
        scope: str,
        topic: str,
        fragment_body: str,
        *,
        references: Mapping[str, str] | None = None,
    ) -> SrcTreeBuilder:
        """Materialize a shared topic at src/_shared/<scope>/<topic>/.

        scope and topic are validated as kebab-case. Reference filenames
        must end in .md and contain no path separators.
        """
        _validate_name(scope, kind="shared scope")
        _validate_name(topic, kind="shared topic")

        topic_root = self.src_root / SHARED_DIR_NAME / scope / topic
        topic_root.mkdir(parents=True, exist_ok=True)

        (topic_root / SHARED_FRAGMENT_FILENAME).write_text(fragment_body)

        if references:
            for ref_name in references:
                _validate_reference_filename(ref_name)
            references_root = topic_root / REFERENCES_SUBDIR_NAME
            references_root.mkdir(exist_ok=True)
            for ref_name, content in references.items():
                (references_root / ref_name).write_text(content)

        return self
