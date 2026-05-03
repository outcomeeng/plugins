"""Harness for building sample src/ plugin trees in tests.

Materializes the directory shape declared by 21-source-and-templating's spec:

- src/plugins/<plugin>/{skills,commands,agents}/
- src/_shared/<scope>/<topic>/fragment.md plus optional reference subtrees

Tests use it via pytest's tmp_path fixture:

    builder = SrcTreeBuilder(tmp_path)
    builder.add_plugin("typescript", skills={"coding-typescript": "..."})
    builder.add_shared_topic("typescript", "code-standards", "fragment body")
    src_root = builder.src_root
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PLUGINS_SUBDIR = "plugins"
SHARED_SUBDIR = "_shared"
SKILLS_SUBDIR = "skills"
COMMANDS_SUBDIR = "commands"
AGENTS_SUBDIR = "agents"
REFERENCES_SUBDIR = "references"
SHARED_FRAGMENT_FILENAME = "fragment.md"
SKILL_FILENAME = "SKILL.md"
COMMAND_FILE_SUFFIX = ".md"
AGENT_FILE_SUFFIX = ".md"


@dataclass(frozen=True)
class SrcTreeBuilder:
    """Construct a sample src/ tree at a given root for build tests.

    The builder is stateless — each method writes files immediately and
    returns self for chaining. Frozen because the only mutable state is
    the filesystem itself, not the builder instance.
    """

    root: Path

    @property
    def src_root(self) -> Path:
        return self.root / "src"

    def add_plugin(
        self,
        name: str,
        *,
        skills: dict[str, str] | None = None,
        commands: dict[str, str] | None = None,
        agents: dict[str, str] | None = None,
    ) -> SrcTreeBuilder:
        """Materialize a plugin at src/plugins/<name>/.

        skills: mapping of skill-directory-name to SKILL.md body content.
                Each entry creates src/plugins/<name>/skills/<skill>/SKILL.md.
        commands: mapping of command-name to markdown body.
                  Each entry creates src/plugins/<name>/commands/<command>.md.
        agents: mapping of agent-name to markdown body.
                Each entry creates src/plugins/<name>/agents/<agent>.md.
        """
        plugin_root = self.src_root / PLUGINS_SUBDIR / name
        plugin_root.mkdir(parents=True, exist_ok=True)

        if skills:
            skills_root = plugin_root / SKILLS_SUBDIR
            skills_root.mkdir(exist_ok=True)
            for skill_name, content in skills.items():
                skill_dir = skills_root / skill_name
                skill_dir.mkdir(exist_ok=True)
                (skill_dir / SKILL_FILENAME).write_text(content)

        if commands:
            commands_root = plugin_root / COMMANDS_SUBDIR
            commands_root.mkdir(exist_ok=True)
            for command_name, content in commands.items():
                (commands_root / f"{command_name}{COMMAND_FILE_SUFFIX}").write_text(
                    content
                )

        if agents:
            agents_root = plugin_root / AGENTS_SUBDIR
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
        references: dict[str, str] | None = None,
    ) -> SrcTreeBuilder:
        """Materialize a shared topic at src/_shared/<scope>/<topic>/.

        scope: top-level grouping, e.g. "typescript", "develop".
        topic: subtopic within the scope, e.g. "code-standards", "test-standards".
        fragment_body: the body of fragment.md (the inlinable shared content).
        references: mapping of reference-filename to body. Each entry creates
                    src/_shared/<scope>/<topic>/references/<filename>.
        """
        topic_root = self.src_root / SHARED_SUBDIR / scope / topic
        topic_root.mkdir(parents=True, exist_ok=True)

        (topic_root / SHARED_FRAGMENT_FILENAME).write_text(fragment_body)

        if references:
            references_root = topic_root / REFERENCES_SUBDIR
            references_root.mkdir(exist_ok=True)
            for ref_name, content in references.items():
                (references_root / ref_name).write_text(content)

        return self
