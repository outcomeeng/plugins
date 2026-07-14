"""Harness for materializing sample src/ plugin trees in tests.

SrcTreeBuilder writes plugins and shared topics to a given root, validating
inputs against the canonical kebab-case naming rules. Layout constants come
from outcomeeng.distribution.build so the harness stays aligned with the
production module's contract.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator, Mapping

from outcomeeng.distribution.build import (
    AGENTS_SUBDIR_NAME,
    AGENT_FILE_SUFFIX,
    PLUGIN_SUBDIRS,
    REFERENCES_SUBDIR_NAME,
    SHARED_DIR_NAME,
    SHARED_FRAGMENT_FILENAME,
    SKILL_FILENAME,
)
from outcomeeng.distribution.contracts import PLUGINS_DIR_NAME, SKILLS_SUBDIR_NAME

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


def write_agent_tree(
    root: Path,
    plugin_name: str,
    agents: Mapping[str, str],
) -> Path:
    """Materialize a plugin agent tree and return the src/plugins root."""
    builder = SrcTreeBuilder(root)
    builder.add_plugin(plugin_name, agents=agents)
    return builder.src_root / PLUGINS_DIR_NAME


def write_agent_source(
    root: Path,
    plugin_name: str,
    agent_name: str,
    content: str,
) -> Path:
    """Materialize one agent file and return its source path."""
    write_agent_tree(root, plugin_name, {agent_name: content})
    return (
        root
        / SRC_DIR_NAME
        / PLUGINS_DIR_NAME
        / plugin_name
        / AGENTS_SUBDIR_NAME
        / f"{agent_name}{AGENT_FILE_SUFFIX}"
    )


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

    @property
    def shared_root(self) -> Path:
        """Path passed to expand_include / render_text as the shared_root argument."""
        return self.src_root / SHARED_DIR_NAME

    def add_plugin(
        self,
        name: str,
        *,
        skills: Mapping[str, str] | None = None,
        agents: Mapping[str, str] | None = None,
        artifacts: Mapping[Path, bytes] | None = None,
    ) -> SrcTreeBuilder:
        """Materialize a plugin at src/plugins/<name>/ with the given components.

        skills: skill-directory-name -> SKILL.md body content.
                Each entry creates src/plugins/<name>/skills/<skill>/SKILL.md.
        agents: agent-name -> markdown body.
                Each entry creates src/plugins/<name>/agents/<agent>.md.
        artifacts: plugin-relative path -> opaque bytes. A nested path must begin
                   with one of the build's source subdirectories; a one-part path
                   materializes an ordinary file at the plugin root.

        Names are validated as kebab-case before any file is written.
        """
        _validate_name(name, kind="plugin")

        plugin_root = self.src_root / PLUGINS_DIR_NAME / name
        plugin_root.mkdir(parents=True, exist_ok=True)

        _write_skills(plugin_root, skills)
        _write_agents(plugin_root, agents)
        _write_artifacts(plugin_root, artifacts)

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

        (topic_root / SHARED_FRAGMENT_FILENAME).write_text(
            fragment_body, encoding="utf-8"
        )

        if references:
            for ref_name in references:
                _validate_reference_filename(ref_name)
            references_root = topic_root / REFERENCES_SUBDIR_NAME
            references_root.mkdir(exist_ok=True)
            for ref_name, content in references.items():
                (references_root / ref_name).write_text(content, encoding="utf-8")

        return self


def _write_skills(plugin_root: Path, skills: Mapping[str, str] | None) -> None:
    if not skills:
        return
    for skill_name in skills:
        _validate_name(skill_name, kind="skill")
    skills_root = plugin_root / SKILLS_SUBDIR_NAME
    skills_root.mkdir(exist_ok=True)
    for skill_name, content in skills.items():
        skill_dir = skills_root / skill_name
        skill_dir.mkdir(exist_ok=True)
        (skill_dir / SKILL_FILENAME).write_text(content, encoding="utf-8")


def _write_agents(plugin_root: Path, agents: Mapping[str, str] | None) -> None:
    if not agents:
        return
    for agent_name in agents:
        _validate_name(agent_name, kind="agent")
    agents_root = plugin_root / AGENTS_SUBDIR_NAME
    agents_root.mkdir(exist_ok=True)
    for agent_name, content in agents.items():
        (agents_root / f"{agent_name}{AGENT_FILE_SUFFIX}").write_text(
            content, encoding="utf-8"
        )


def _write_artifacts(
    plugin_root: Path,
    artifacts: Mapping[Path, bytes] | None,
) -> None:
    if not artifacts:
        return
    for relative_path, artifact_content in artifacts.items():
        _validate_artifact_path(relative_path)
        artifact_path = plugin_root / relative_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(artifact_content)


def _validate_artifact_path(relative_path: Path) -> None:
    nested_outside_plugin_subdirs = (
        len(relative_path.parts) > 1 and relative_path.parts[0] not in PLUGIN_SUBDIRS
    )
    if (
        relative_path.is_absolute()
        or not relative_path.parts
        or nested_outside_plugin_subdirs
        or ".." in relative_path.parts
    ):
        msg = f"invalid plugin artifact path {relative_path}"
        raise ValueError(msg)


@contextmanager
def src_tree() -> Iterator[SrcTreeBuilder]:
    """Yield a SrcTreeBuilder rooted in a fresh temporary directory.

    Owns the temporary-directory lifecycle so a property test can materialize a
    new src/ tree per generated example and have it removed on every exit path.
    The builder writes files; this manages the resource the builder writes into.
    """
    with TemporaryDirectory() as tmp:
        yield SrcTreeBuilder(Path(tmp))
