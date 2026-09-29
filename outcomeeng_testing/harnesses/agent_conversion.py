"""Harness contracts for agent-conversion spec evidence."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, cast

import yaml

from outcomeeng.distribution.agents import (
    AGENT_SKILL_CONFIG_FIELD,
    AGENT_SKILLS_FIELD,
    AGENT_SOURCE_DIRECTORY_NAME,
    AGENT_TARGETS_FIELD,
    DEVELOPER_INSTRUCTIONS_FIELD,
    TomlArrayTable,
    TomlMultilineString,
    CodexAgent,
    SourceAgent,
    convert_agent,
    convert_agents,
    parse_agent_markdown,
    render_agent_toml,
    iter_agent_files,
)
from outcomeeng.distribution.build import build
from outcomeeng.distribution.contracts import (
    DIST_CODEX_PLUGINS_DIR,
    DIST_DIR_NAME,
    FRONTMATTER_DELIMITER,
    MARKDOWN_FILE_SUFFIX,
    Target,
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
)
from outcomeeng.validation.audit_artifacts import SPEC_TREE_PLUGIN_NAME
from outcomeeng_testing.harnesses.src_tree import write_agent_source
from outcomeeng_testing.harnesses.distribution import REPOSITORY_ROOT

PLUGIN_NAME: Final = "sample"
CODEX_AGENTS_DIRNAME: Final = "codex-agents"
AGENT_CONVERSION_FIXTURES_DIR: Final = (
    Path(__file__).resolve().parents[1] / "fixtures" / "agent_conversion"
)
LIFECYCLE_COLLISION_SOURCE: Final = (
    AGENT_CONVERSION_FIXTURES_DIR / "lifecycle-collision" / SOURCE_ROOT_NAME
)
REPOSITORY_SOURCE_ROOT: Final = REPOSITORY_ROOT / SOURCE_ROOT_NAME
SPEC_TREE_AGENT_SOURCE_DIR: Final = (
    REPOSITORY_SOURCE_ROOT
    / PLUGINS_DIR_NAME
    / SPEC_TREE_PLUGIN_NAME
    / AGENT_SOURCE_DIRECTORY_NAME
)
FRONTMATTER_FENCE: Final = f"{FRONTMATTER_DELIMITER}\n"
FRONTMATTER_CLOSER: Final = f"\n{FRONTMATTER_DELIMITER}\n"
SOURCE_AGENT_FIXTURE: Final = "source-agent.md"
CODEX_RENDERED_AGENT_FIXTURE: Final = "codex-rendered-agent.md"
CODEX_BLOCK_MCP_AGENT_FIXTURE: Final = "codex-block-mcp-agent.md"
CODEX_FLOW_MCP_AGENT_FIXTURE: Final = "codex-flow-mcp-agent.txt"
DUPLICATE_REVIEWER_FIXTURE: Final = "duplicate-reviewer.md"
DUPLICATE_REVIEWER_BANG_FIXTURE: Final = "duplicate-reviewer-bang.md"
EMPTY_TOOLS_AGENT_FIXTURE: Final = "empty-tools-agent.md"
FOLDED_DESCRIPTION_AGENT_FIXTURE: Final = "folded-description-agent.md"
GUARDED_WRITER_AGENT_FIXTURE: Final = "guarded-writer-agent.md"
# The inert whole-agent payload that direct conversion calls vary one field of.
BASELINE_AGENT_FIXTURE: Final = DUPLICATE_REVIEWER_FIXTURE
FILENAME_COLLISION_FIXTURES: Final = (
    DUPLICATE_REVIEWER_FIXTURE,
    DUPLICATE_REVIEWER_BANG_FIXTURE,
)
YAML_MCP_SERVER_FIXTURES: Final = (
    CODEX_BLOCK_MCP_AGENT_FIXTURE,
    CODEX_FLOW_MCP_AGENT_FIXTURE,
)


@dataclass(frozen=True)
class AgentDocumentOracle:
    """Independent YAML-frontmatter and Markdown-body observation."""

    path: Path
    frontmatter: Mapping[str, object]
    body: str


@dataclass(frozen=True)
class RepositoryAgentBuild:
    """Repository agent sources beside one generated distribution tree."""

    source_root: Path
    sources: tuple[Path, ...]
    dist_root: Path
    admitted_targets: Mapping[Path, frozenset[Target]]

    def sources_for(self, target: Target) -> tuple[Path, ...]:
        """Return the sources the build emits into ``target``'s tree."""
        return tuple(
            source for source in self.sources if target in self.admitted_targets[source]
        )


def build_repository_agents(root: Path) -> RepositoryAgentBuild:
    """Build every repository agent into one disposable distribution tree."""
    sources = iter_agent_files(REPOSITORY_SOURCE_ROOT / PLUGINS_DIR_NAME)
    dist_root = root / DIST_DIR_NAME
    build(REPOSITORY_SOURCE_ROOT, dist_root)
    return RepositoryAgentBuild(
        source_root=REPOSITORY_SOURCE_ROOT,
        sources=sources,
        dist_root=dist_root,
        admitted_targets={source: authored_agent_targets(source) for source in sources},
    )


def authored_agent_targets(source: Path) -> frozenset[Target]:
    """Read the targets an authored source lists, independently of the build's parser.

    Only the block list under the targets key is read, so build tokens elsewhere
    in the front matter need no rendering. A source outside an agents directory,
    or an agent source without the key, lists every target.
    """
    if source.parent.name != AGENT_SOURCE_DIRECTORY_NAME:
        return frozenset(Target)
    lines = source.read_text(encoding="utf-8").split("\n")
    if lines[0] != FRONTMATTER_DELIMITER or FRONTMATTER_DELIMITER not in lines[1:]:
        raise ValueError(f"{source}: expected YAML frontmatter delimiters")
    frontmatter = lines[1 : lines.index(FRONTMATTER_DELIMITER, 1)]
    key = f"{AGENT_TARGETS_FIELD}:"
    if key not in frontmatter:
        return frozenset(Target)
    items: list[str] = []
    for line in frontmatter[frontmatter.index(key) + 1 :]:
        if not line.startswith("  - "):
            break
        items.append(line.removeprefix("  - ").strip())
    return frozenset(Target(item) for item in items)


def agent_document_oracle(path: Path) -> AgentDocumentOracle:
    """Read an agent document through PyYAML instead of the production parser."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith(FRONTMATTER_FENCE):
        raise ValueError(f"{path}: expected YAML frontmatter opener")
    frontmatter_text, separator, body = text.removeprefix(FRONTMATTER_FENCE).partition(
        FRONTMATTER_CLOSER
    )
    if not separator:
        raise ValueError(f"{path}: expected YAML frontmatter closer")
    loaded = yaml.safe_load(frontmatter_text)
    if not isinstance(loaded, Mapping) or not all(
        isinstance(key, str) for key in loaded
    ):
        raise ValueError(f"{path}: expected string-keyed YAML mapping")
    return AgentDocumentOracle(
        path=path,
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
    profile: str | None = None,
    permission_mode: str | None = None,
    tools: tuple[str, ...] | None = None,
) -> SourceAgent:
    """Parse the baseline whole-agent fixture with one caller-selected variation.

    The fixture is relocated beneath a plugin's agent directory, the namespace
    conversion requires; ``tools`` declares an explicit allowlist when given.
    """
    fixture = AGENT_CONVERSION_FIXTURES_DIR / BASELINE_AGENT_FIXTURE
    baseline = parse_agent_markdown(fixture)
    return replace(
        baseline,
        source_path=Path(PLUGIN_NAME) / AGENT_SOURCE_DIRECTORY_NAME / fixture.name,
        profile=profile,
        permission_mode=permission_mode,
        tools=baseline.tools if tools is None else tools,
        tools_declared=baseline.tools_declared or tools is not None,
    )


def spec_tree_wrapper_agents() -> tuple[SourceAgent, ...]:
    """Return every authored Spec Tree wrapper agent."""
    return tuple(
        parse_agent_markdown(path)
        for path in sorted(SPEC_TREE_AGENT_SOURCE_DIR.glob(f"*{MARKDOWN_FILE_SUFFIX}"))
    )


def repository_wrapper_agents() -> tuple[SourceAgent, ...]:
    """Return every authored marketplace wrapper agent."""
    return tuple(
        parse_agent_markdown(path)
        for path in iter_agent_files(REPOSITORY_SOURCE_ROOT / PLUGINS_DIR_NAME)
    )


def agent_conversion_fixture(name: str) -> str:
    """Read one inert whole-agent fixture."""
    return (AGENT_CONVERSION_FIXTURES_DIR / name).read_text(encoding="utf-8")


def write_fixture_agent(root: Path, fixture: str) -> Path:
    """Materialize one whole-agent fixture as a plugin agent source file."""
    return write_agent_source(
        root, PLUGIN_NAME, Path(fixture).stem, agent_conversion_fixture(fixture)
    )


def write_filename_collision_sources(root: Path) -> Path:
    """Materialize the agents whose names converge on one converted filename."""
    for fixture in FILENAME_COLLISION_FIXTURES:
        write_fixture_agent(root, fixture)
    return root / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME


def _converted_fixture_toml(
    root: Path, fixture: str
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    source_path = write_fixture_agent(root, fixture)
    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source_path)))
    return agent_document_oracle(source_path), tomllib.loads(rendered)


def converted_source_agent_toml(
    root: Path,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Render the baseline source-agent fixture through the converter."""
    return _converted_fixture_toml(root, SOURCE_AGENT_FIXTURE)


def converted_folded_description_toml(
    root: Path,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Render the folded-description fixture through the converter."""
    return _converted_fixture_toml(root, FOLDED_DESCRIPTION_AGENT_FIXTURE)


def converted_empty_tools_toml(root: Path) -> dict[str, object]:
    """Render the explicit-empty-tools fixture through the converter."""
    _document, parsed = _converted_fixture_toml(root, EMPTY_TOOLS_AGENT_FIXTURE)
    return parsed


def converted_default_codex_source_root_toml(
    root: Path,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Convert a rendered Codex-target agent fixture from its own tree."""
    source_root = root / DIST_CODEX_PLUGINS_DIR
    source_path = (
        source_root
        / PLUGIN_NAME
        / AGENT_SOURCE_DIRECTORY_NAME
        / Path(CODEX_RENDERED_AGENT_FIXTURE).with_suffix(MARKDOWN_FILE_SUFFIX).name
    )
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        agent_conversion_fixture(CODEX_RENDERED_AGENT_FIXTURE), encoding="utf-8"
    )
    (converted,) = convert_agents(source_root)
    return agent_document_oracle(source_path), tomllib.loads(
        render_agent_toml(converted)
    )


def converted_codex_agent_with_yaml_mcp_toml(
    root: Path,
    fixture: str,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Convert a Codex target fixture with YAML MCP mapping syntax."""
    source_path = write_fixture_agent(root, fixture)
    (converted,) = convert_agents(root / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME)
    return agent_document_oracle(source_path), tomllib.loads(
        render_agent_toml(converted)
    )


def installed_guarded_writer_toml(
    root: Path,
) -> tuple[AgentDocumentOracle, dict[str, object]]:
    """Install the guarded-writer fixture and return source plus parsed TOML."""
    source_path = write_fixture_agent(root, GUARDED_WRITER_AGENT_FIXTURE)
    (installed_path,) = _write_converted_agents(
        root / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME, root / CODEX_AGENTS_DIRNAME
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
    skills = toml_table(values, AGENT_SKILLS_FIELD)
    config = skills[AGENT_SKILL_CONFIG_FIELD]
    if not isinstance(config, list):
        raise TypeError(f"{AGENT_SKILL_CONFIG_FIELD}: expected array")
    parsed: list[Mapping[str, object]] = []
    for item in config:
        if not isinstance(item, dict):
            raise TypeError(f"{AGENT_SKILL_CONFIG_FIELD}: expected table entries")
        parsed.append(cast("Mapping[str, object]", item))
    return parsed


def converted_skill_config(agent: CodexAgent) -> tuple[Mapping[str, object], ...]:
    """Return the converter's structured ``skills.config`` rows."""
    skills = agent.values[AGENT_SKILLS_FIELD]
    if not isinstance(skills, Mapping):
        raise TypeError(f"{AGENT_SKILLS_FIELD}: expected table")
    config = skills[AGENT_SKILL_CONFIG_FIELD]
    if not isinstance(config, TomlArrayTable):
        raise TypeError(f"{AGENT_SKILL_CONFIG_FIELD}: expected TOML array table")
    return config.rows


def converted_instruction_value(agent: CodexAgent) -> str:
    """Return converted developer instructions."""
    value = agent.values[DEVELOPER_INSTRUCTIONS_FIELD]
    if not isinstance(value, TomlMultilineString):
        raise TypeError(
            f"{DEVELOPER_INSTRUCTIONS_FIELD}: expected TOML multiline string"
        )
    return value.value
