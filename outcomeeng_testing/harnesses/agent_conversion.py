"""Harness contracts for agent-conversion spec evidence."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

import yaml

from outcomeeng.distribution.agents import (
    AGENT_SOURCE_DIRECTORY_NAME,
    TomlArrayTable,
    TomlMultilineString,
    CodexAgent,
    SourceAgent,
    convert_agent,
    convert_agents,
    parse_agent_markdown,
    render_agent_toml,
)
from outcomeeng.distribution.contracts import (
    DIST_CODEX_PLUGINS_DIR,
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
)
from outcomeeng_testing.harnesses.src_tree import write_agent_source, write_agent_tree

PLUGIN_NAME: Final = "sample"
CHANGES_REVIEWER_NAME: Final = "changes-reviewer"
GUARDED_WRITER_NAME: Final = "guarded-writer"
READ_ONLY_REVIEWER_NAME: Final = "read-only-reviewer"
REVIEWER_BODY: Final = "Review."
WRITER_BODY: Final = "Write."
REVIEWER_DESCRIPTION: Final = "Review."
WRITER_DESCRIPTION: Final = "Write."
REVIEWER_SOURCE_PATH: Final = (
    Path(PLUGIN_NAME) / AGENT_SOURCE_DIRECTORY_NAME / "reviewer.md"
)
WRITER_SOURCE_PATH: Final = (
    Path(PLUGIN_NAME) / AGENT_SOURCE_DIRECTORY_NAME / "writer.md"
)
CODEX_AGENTS_DIRNAME: Final = "codex-agents"
AGENT_CONVERSION_FIXTURES_DIR: Final = (
    Path(__file__).resolve().parents[1] / "fixtures" / "agent_conversion"
)
SPEC_TREE_AGENT_SOURCE_DIR: Final = (
    Path(__file__).resolve().parents[2]
    / SOURCE_ROOT_NAME
    / PLUGINS_DIR_NAME
    / "spec-tree"
    / AGENT_SOURCE_DIRECTORY_NAME
)
SOURCE_AGENT_FIXTURE: Final = "source-agent.md"
CODEX_RENDERED_AGENT_FIXTURE: Final = "codex-rendered-agent.md"
CODEX_BLOCK_MCP_AGENT_FIXTURE: Final = "codex-block-mcp-agent.md"
CODEX_FLOW_MCP_AGENT_FIXTURE: Final = "codex-flow-mcp-agent.txt"
DUPLICATE_REVIEWER_FIXTURE: Final = "duplicate-reviewer.md"
DUPLICATE_REVIEWER_BANG_FIXTURE: Final = "duplicate-reviewer-bang.md"
EMPTY_TOOLS_AGENT_FIXTURE: Final = "empty-tools-agent.md"
FOLDED_DESCRIPTION_AGENT_FIXTURE: Final = "folded-description-agent.md"
GUARDED_WRITER_AGENT_FIXTURE: Final = "guarded-writer-agent.md"
READ_ONLY_REVIEWER_AGENT_FIXTURE: Final = "read-only-reviewer-agent.md"
# Every correspondence below is written out here rather than derived from the
# production tables the converter reads. Deriving them would make the expected
# value and the case domain the same object, so repointing a mapping target
# would move both and no test could fail for a wrong value. These literals are
# the oracle; the linked mapping tests separately compare their key sets to the
# production tables, so a new production entry cannot slip through untested.
EXPECTED_MODEL_CORRESPONDENCE: Final = (
    ("claude-opus", "gpt-5.5"),
    ("opus", "gpt-5.5"),
    ("claude-sonnet", "gpt-5.4"),
    ("sonnet", "gpt-5.4"),
    ("claude-haiku", "gpt-5.4-mini"),
    ("haiku", "gpt-5.4-mini"),
)
EXPECTED_EFFORT_CORRESPONDENCE: Final = (
    ("low", "low"),
    ("medium", "medium"),
    ("high", "high"),
    ("max", "xhigh"),
)
EXPECTED_PERMISSION_MODE_CORRESPONDENCE: Final = (
    ("default", None),
    ("acceptEdits", "workspace-write"),
    ("auto", None),
    ("dontAsk", None),
    ("bypassPermissions", None),
    ("plan", "read-only"),
)
# The tool names below are the authoring platform's own tool vocabulary; each
# pairing to a capability class is the conversion decision under test, so the
# pairs are the hand-authored oracle exactly like the correspondences above.
EXPECTED_TOOL_CLASSIFICATION: Final = (
    ("Bash", "script-capable"),
    ("Edit", "write-capable"),
    ("Glob", "read-only"),
    ("Grep", "read-only"),
    ("NotebookEdit", "write-capable"),
    ("Read", "read-only"),
    ("Skill", "script-capable"),
    ("WebFetch", "web-capable"),
    ("WebSearch", "web-capable"),
    ("Write", "write-capable"),
)


@dataclass(frozen=True)
class AgentDocumentOracle:
    """Independent YAML-frontmatter and Markdown-body observation."""

    frontmatter: Mapping[str, object]
    body: str


def agent_document_oracle(path: Path) -> AgentDocumentOracle:
    """Read an agent document through PyYAML instead of the production parser."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: expected YAML frontmatter opener")
    frontmatter_text, separator, body = text.removeprefix("---\n").partition("\n---\n")
    if not separator:
        raise ValueError(f"{path}: expected YAML frontmatter closer")
    loaded = yaml.safe_load(frontmatter_text)
    if not isinstance(loaded, Mapping) or not all(
        isinstance(key, str) for key in loaded
    ):
        raise ValueError(f"{path}: expected string-keyed YAML mapping")
    return AgentDocumentOracle(
        frontmatter=cast("Mapping[str, object]", loaded),
        body=body.strip(),
    )


def oracle_string(document: AgentDocumentOracle, key: str) -> str:
    """Return one required string from an independent document observation."""
    value = document.frontmatter[key]
    if not isinstance(value, str):
        raise TypeError(f"{key}: expected string, got {type(value).__name__}")
    return value


def oracle_optional_string(document: AgentDocumentOracle, key: str) -> str | None:
    """Return one optional string from an independent document observation."""
    value = document.frontmatter.get(key)
    if value is not None and not isinstance(value, str):
        raise TypeError(f"{key}: expected optional string, got {type(value).__name__}")
    return value


def oracle_strings(document: AgentDocumentOracle, key: str) -> tuple[str, ...]:
    """Return one comma-delimited or YAML-sequence string field."""
    value = document.frontmatter.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"{key}: expected string sequence")
    return tuple(cast("list[str]", value))


def oracle_mapping(document: AgentDocumentOracle, key: str) -> Mapping[str, object]:
    """Return one required nested mapping from an independent observation."""
    value = document.frontmatter[key]
    if not isinstance(value, Mapping):
        raise TypeError(f"{key}: expected mapping, got {type(value).__name__}")
    return cast("Mapping[str, object]", value)


def source_agent(
    *,
    source_path: Path = REVIEWER_SOURCE_PATH,
    name: str = "reviewer",
    description: str = REVIEWER_DESCRIPTION,
    body: str = REVIEWER_BODY,
    model: str | None = None,
    effort: str | None = None,
    permission_mode: str | None = None,
    skills: tuple[str, ...] = (),
    tools: tuple[str, ...] = (),
    tools_declared: bool = False,
) -> SourceAgent:
    """Build a parsed source agent with harness-owned defaults."""
    return SourceAgent(
        source_path=source_path,
        name=name,
        description=description,
        body=body,
        model=model,
        effort=effort,
        permission_mode=permission_mode,
        skills=skills,
        tools=tools,
        tools_declared=tools_declared,
    )


def spec_tree_wrapper_agents() -> tuple[SourceAgent, ...]:
    """Return every authored Spec Tree wrapper agent."""
    return tuple(
        parse_agent_markdown(path)
        for path in sorted(SPEC_TREE_AGENT_SOURCE_DIR.glob("*.md"))
    )


def agent_conversion_fixture(name: str) -> str:
    """Read one inert whole-agent fixture."""
    return (AGENT_CONVERSION_FIXTURES_DIR / name).read_text(encoding="utf-8")


def converted_source_agent_toml(
    root: Path,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Render the baseline source-agent fixture through the converter."""
    source_path = write_agent_source(
        root,
        PLUGIN_NAME,
        CHANGES_REVIEWER_NAME,
        agent_conversion_fixture(SOURCE_AGENT_FIXTURE),
    )
    source = parse_agent_markdown(source_path)
    rendered = render_agent_toml(convert_agent(source))
    return agent_document_oracle(source_path), tomllib.loads(rendered)


def converted_folded_description_toml(
    root: Path,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Render the folded-description fixture through the converter."""
    source = write_agent_source(
        root,
        PLUGIN_NAME,
        CHANGES_REVIEWER_NAME,
        agent_conversion_fixture(FOLDED_DESCRIPTION_AGENT_FIXTURE),
    )
    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source)))
    return agent_document_oracle(source), tomllib.loads(rendered)


def converted_default_codex_source_root_toml(
    root: Path,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Convert a rendered Codex-target agent fixture from its own tree."""
    source_root = write_dist_codex_agent_tree(
        root,
        PLUGIN_NAME,
        {CHANGES_REVIEWER_NAME: agent_conversion_fixture(CODEX_RENDERED_AGENT_FIXTURE)},
    )
    source_path = (
        source_root
        / PLUGIN_NAME
        / AGENT_SOURCE_DIRECTORY_NAME
        / f"{CHANGES_REVIEWER_NAME}.md"
    )
    (converted,) = convert_agents(source_root)
    return agent_document_oracle(source_path), tomllib.loads(
        render_agent_toml(converted)
    )


def converted_codex_agent_with_yaml_mcp_toml(
    root: Path,
    source: str,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Convert a Codex target fixture with YAML MCP mapping syntax."""
    source_root = write_agent_tree(
        root,
        PLUGIN_NAME,
        {CHANGES_REVIEWER_NAME: source},
    )
    source_agent_path = (
        source_root
        / PLUGIN_NAME
        / AGENT_SOURCE_DIRECTORY_NAME
        / f"{CHANGES_REVIEWER_NAME}.md"
    )
    (converted,) = convert_agent_tree(source_root)
    return agent_document_oracle(source_agent_path), tomllib.loads(
        render_agent_toml(converted)
    )


def converted_empty_tools_toml(root: Path) -> dict[str, object]:
    """Render the explicit-empty-tools fixture through the converter."""
    source = write_agent_source(
        root,
        PLUGIN_NAME,
        CHANGES_REVIEWER_NAME,
        agent_conversion_fixture(EMPTY_TOOLS_AGENT_FIXTURE),
    )
    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source)))
    return tomllib.loads(rendered)


def convert_agent_tree(source_root: Path) -> tuple[CodexAgent, ...]:
    """Convert a harness-created agent tree."""
    return convert_agents(source_root)


def write_dist_codex_agent_tree(
    root: Path,
    plugin_name: str,
    agents: Mapping[str, str],
) -> Path:
    """Materialize a generated dist/codex plugin agent tree."""
    source_root = root / DIST_CODEX_PLUGINS_DIR
    for agent_name, content in agents.items():
        agent_path = (
            source_root / plugin_name / AGENT_SOURCE_DIRECTORY_NAME / f"{agent_name}.md"
        )
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        agent_path.write_text(content, encoding="utf-8")
    return source_root


def installed_guarded_writer_toml(
    root: Path,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Install the guarded-writer fixture and return source plus parsed TOML."""
    source_root = write_agent_tree(
        root,
        PLUGIN_NAME,
        {GUARDED_WRITER_NAME: agent_conversion_fixture(GUARDED_WRITER_AGENT_FIXTURE)},
    )
    source_path = (
        source_root
        / PLUGIN_NAME
        / AGENT_SOURCE_DIRECTORY_NAME
        / f"{GUARDED_WRITER_NAME}.md"
    )
    (installed_path,) = _write_converted_agents(
        source_root, root / CODEX_AGENTS_DIRNAME
    )
    return agent_document_oracle(source_path), tomllib.loads(
        installed_path.read_text(encoding="utf-8")
    )


def _write_converted_agents(source_root: Path, target_root: Path) -> tuple[Path, ...]:
    """Convert every agent under ``source_root`` and write the TOML to disk.

    Mirrors what the build writes into a generated tree, so a harness can read
    a converted agent back through the filesystem without the retired
    install-time model.
    """
    target_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for agent in convert_agents(source_root):
        path = target_root / agent.filename
        path.write_text(render_agent_toml(agent), encoding="utf-8")
        written.append(path)
    return tuple(written)


def toml_string(values: Mapping[str, object], key: str) -> str:
    """Return one string from parsed TOML."""
    value = values[key]
    if not isinstance(value, str):
        raise TypeError(f"{key}: expected string, got {type(value).__name__}")
    return value


def toml_compatible(value: object) -> object:
    """Normalize structured source values to their TOML-decoded container shape."""
    if isinstance(value, Mapping):
        return {key: toml_compatible(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [toml_compatible(item) for item in value]
    return value


def toml_table(values: Mapping[str, object], key: str) -> Mapping[str, object]:
    """Return one table from parsed TOML."""
    value = values[key]
    if not isinstance(value, dict):
        raise TypeError(f"{key}: expected table, got {type(value).__name__}")
    return cast("Mapping[str, object]", value)


def parsed_toml_skill_config(
    values: Mapping[str, object],
) -> list[Mapping[str, object]]:
    """Return ``skills.config`` entries from emitted TOML."""
    skills = toml_table(values, "skills")
    config = skills["config"]
    if not isinstance(config, list):
        raise TypeError("skills.config: expected array")
    parsed: list[Mapping[str, object]] = []
    for item in config:
        if not isinstance(item, dict):
            raise TypeError("skills.config: expected table entries")
        parsed.append(cast("Mapping[str, object]", item))
    return parsed


def converted_skill_config(agent: CodexAgent) -> tuple[Mapping[str, object], ...]:
    """Return the converter's structured ``skills.config`` rows."""
    skills = agent.values["skills"]
    if not isinstance(skills, Mapping):
        raise TypeError("skills: expected table")
    config = skills["config"]
    if not isinstance(config, TomlArrayTable):
        raise TypeError("skills.config: expected TOML array table")
    return config.rows


def converted_instruction_value(agent: CodexAgent) -> str:
    """Return converted developer instructions."""
    value = agent.values["developer_instructions"]
    if not isinstance(value, TomlMultilineString):
        raise TypeError("developer_instructions: expected TOML multiline string")
    return value.value
