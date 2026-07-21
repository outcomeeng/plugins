"""Harness contracts for agent-conversion spec evidence."""

from __future__ import annotations

import os
import tomllib
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

import yaml

from outcomeeng.distribution.agents import (
    AGENT_SOURCE_DIRECTORY_NAME,
    ALL_TOOLS_SENTINEL,
    CODEX_AGENT_ENV_VAR,
    CODEX_AGENT_ENV_SEPARATOR,
    CODEX_DISALLOWED_TOOLS_GUIDANCE_TEMPLATE,
    CODEX_PERMISSION_MODE_GUIDANCE_TEMPLATE,
    CODEX_SKILLS_GUIDANCE_TEMPLATE,
    CODEX_STANDARD_MODEL,
    CODEX_STRONG_MODEL,
    CODEX_TOOLS_GUIDANCE_TEMPLATE,
    CODEX_UNSUPPORTED_FIELDS_GUIDANCE_TEMPLATE,
    DEFAULT_SOURCE_ROOT,
    EFFORT_MAPPINGS,
    GENERATED_MANIFEST_FILENAME,
    INHERIT_MODEL_VALUE,
    MANUAL_REVIEW_GUIDANCE_CLOSE,
    MANUAL_REVIEW_GUIDANCE_OPEN,
    MODEL_MAPPINGS,
    MODEL_PREFIX_EXAMPLE_SUFFIX,
    PERMISSION_MODE_MAPPINGS,
    READ_ONLY_SANDBOX_MODE,
    READ_ONLY_TOOLS,
    SCRIPT_CAPABLE_TOOLS,
    SUPPORTED_FRONTMATTER_FIELDS,
    TomlArrayTable,
    TomlMultilineString,
    WEB_CAPABLE_TOOLS,
    WEB_SEARCH_DISABLED,
    WRITE_CAPABLE_TOOLS,
    CodexAgent,
    SourceAgent,
    AgentConversionError,
    agent_environment_marker,
    convert_agent,
    convert_agents,
    infer_sandbox_mode,
    install_agents,
    map_effort,
    map_model,
    map_permission_mode,
    map_web_search,
    parse_agent_markdown,
    render_agent_toml,
)
from outcomeeng.distribution.contracts import (
    CODEX_PLUGIN_SUBDIR_NAME,
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
)
from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST,
    DIST_CODEX_PLUGINS_DIR,
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
GENERATED_CODEX_AGENTS_DIRNAME: Final = "generated-codex-agents"
CODEX_PLUGIN_MANIFEST_PARTS: Final = (
    *DIST_CODEX_PLUGINS_DIR.parts,
    PLUGIN_NAME,
    CODEX_PLUGIN_SUBDIR_NAME,
)
CODEX_PLUGIN_MANIFEST_BODY: Final = '{"name": "sample", "version": "0.0.1"}\n'
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
INVALID_MANIFEST_BODY: Final = "{"
STALE_GENERATED_CONTENT: Final = "user-visible stale generated content\n"
FOLDED_DESCRIPTION_TEXT: Final = (
    "Review working changes against a base ref. "
    "Accept optional PR, branch, or range inputs."
)
# Every correspondence below is written out here rather than derived from the
# production tables the converter reads. Deriving them would make the expected
# value and the case domain the same object, so repointing a mapping target
# would move both and no test could fail for a wrong value. These literals are
# the oracle; `assert_mapping_oracles_cover_production_tables` separately proves
# they still span the production key sets, so a new production entry cannot slip
# through untested.
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
# The DUPLICATE_REVIEWER_BANG_FIXTURE source names the agent `reviewer!`. Its
# generated agent type is written out here for the same reason as the mapping
# correspondences above: deriving it from the converted agent's own filename
# would route the expectation back through the slugify path under test, and the
# comparison would hold for any slug the implementation produced.
EXPECTED_TOP_TIER_MODEL: Final = "gpt-5.5"
EXPECTED_SLUGGED_AGENT_TYPE: Final = "reviewer"
EXPECTED_SLUGGED_AGENT_FILENAME: Final = f"{EXPECTED_SLUGGED_AGENT_TYPE}.toml"
EXPECTED_READ_ONLY_TOOLS: Final = ("Glob", "Grep", "Read")
EXPECTED_SCRIPT_CAPABLE_TOOLS: Final = ("Bash", "Skill")
EXPECTED_WEB_CAPABLE_TOOLS: Final = ("WebFetch", "WebSearch")
EXPECTED_WRITE_CAPABLE_TOOLS: Final = ("Edit", "NotebookEdit", "Write")

MODEL_PREFIX_CASES: Final = EXPECTED_MODEL_CORRESPONDENCE + tuple(
    (f"{source_prefix}{MODEL_PREFIX_EXAMPLE_SUFFIX}", target_model)
    for source_prefix, target_model in EXPECTED_MODEL_CORRESPONDENCE
    if source_prefix.startswith("claude-")
)
MODEL_CASES: Final = (*MODEL_PREFIX_CASES, (INHERIT_MODEL_VALUE, None))
EFFORT_CASES: Final = EXPECTED_EFFORT_CORRESPONDENCE
PERMISSION_MODE_CASES: Final = EXPECTED_PERMISSION_MODE_CORRESPONDENCE
SUPPORTED_PERMISSION_MODE_CASES: Final = tuple(
    (source, target)
    for source, target in EXPECTED_PERMISSION_MODE_CORRESPONDENCE
    if target is not None
)
UNMAPPED_PERMISSION_MODE_CASES: Final = tuple(
    source
    for source, target in EXPECTED_PERMISSION_MODE_CORRESPONDENCE
    if target is None
)
READ_ONLY_TOOL_ALLOWLIST: Final = EXPECTED_READ_ONLY_TOOLS
READ_ONLY_WEB_TOOL_ALLOWLIST: Final = (
    EXPECTED_READ_ONLY_TOOLS + EXPECTED_WEB_CAPABLE_TOOLS
)
WEB_CAPABLE_TOOL_ALLOWLIST: Final = EXPECTED_WEB_CAPABLE_TOOLS
ALL_TOOLS_ALLOWLIST: Final = (ALL_TOOLS_SENTINEL,)
WRITE_CAPABLE_TOOL_ALLOWLIST: Final = EXPECTED_WRITE_CAPABLE_TOOLS
SCRIPT_CAPABLE_TOOL_ALLOWLIST: Final = EXPECTED_SCRIPT_CAPABLE_TOOLS
SORTED_WRITE_CAPABLE_TOOL_ALLOWLIST: Final = tuple(sorted(EXPECTED_WRITE_CAPABLE_TOOLS))
EMPTY_TOOL_ALLOWLIST: Final = ()


@dataclass(frozen=True)
class AgentDocumentOracle:
    """Independent YAML-frontmatter and Markdown-body observation."""

    frontmatter: Mapping[str, object]
    body: str


def agent_document_oracle(path: Path) -> AgentDocumentOracle:
    """Read an agent document through PyYAML instead of the production parser."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path}: expected YAML frontmatter opener")
    frontmatter_text, separator, body = text.removeprefix("---\n").partition("\n---\n")
    if not separator:
        raise AssertionError(f"{path}: expected YAML frontmatter closer")
    loaded = yaml.safe_load(frontmatter_text)
    if not isinstance(loaded, Mapping) or not all(
        isinstance(key, str) for key in loaded
    ):
        raise AssertionError(f"{path}: expected string-keyed YAML mapping")
    return AgentDocumentOracle(
        frontmatter=cast("Mapping[str, object]", loaded),
        body=body.strip(),
    )


def oracle_string(document: AgentDocumentOracle, key: str) -> str:
    """Return one required string from an independent document observation."""
    value = document.frontmatter[key]
    assert isinstance(value, str)
    return value


def oracle_optional_string(document: AgentDocumentOracle, key: str) -> str | None:
    """Return one optional string from an independent document observation."""
    value = document.frontmatter.get(key)
    assert value is None or isinstance(value, str)
    return value


def oracle_strings(document: AgentDocumentOracle, key: str) -> tuple[str, ...]:
    """Return one comma-delimited or YAML-sequence string field."""
    value = document.frontmatter.get(key)
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    assert isinstance(value, list) and all(isinstance(item, str) for item in value)
    return tuple(cast("list[str]", value))


def oracle_mapping(document: AgentDocumentOracle, key: str) -> Mapping[str, object]:
    """Return one required nested mapping from an independent observation."""
    value = document.frontmatter[key]
    assert isinstance(value, Mapping)
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


def assert_spec_tree_wrapper_agents_use_explicit_models() -> None:
    """Prove every skill-owning Spec Tree wrapper selects a concrete model."""
    wrappers = tuple(
        agent
        for path in sorted(SPEC_TREE_AGENT_SOURCE_DIR.glob("*.md"))
        if (agent := parse_agent_markdown(path)).skills
    )

    assert wrappers
    for agent in wrappers:
        assert agent.model is not None, f"{agent.source_path}: model is required"
        assert agent.model != INHERIT_MODEL_VALUE, (
            f"{agent.source_path}: model must not inherit"
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


def converted_folded_description_toml(root: Path) -> dict[str, object]:
    """Render the folded-description fixture through the converter."""
    source = write_agent_source(
        root,
        PLUGIN_NAME,
        CHANGES_REVIEWER_NAME,
        agent_conversion_fixture(FOLDED_DESCRIPTION_AGENT_FIXTURE),
    )
    rendered = render_agent_toml(convert_agent(parse_agent_markdown(source)))
    return tomllib.loads(rendered)


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


@contextmanager
def working_directory(path: Path) -> Iterator[None]:
    """Run a block with the current working directory set to ``path``."""
    previous = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(previous)


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
    target_root = root / CODEX_AGENTS_DIRNAME
    (installed_path,) = install_agents(source_root, target_root)
    return agent_document_oracle(source_path), tomllib.loads(
        installed_path.read_text(encoding="utf-8")
    )


def write_codex_plugin_manifest(root: Path) -> Path:
    """Write a sample Codex plugin manifest and return its path."""
    manifest_dir = root.joinpath(*CODEX_PLUGIN_MANIFEST_PARTS)
    manifest_path = manifest_dir / CODEX_PLUGIN_MANIFEST.name
    manifest_dir.mkdir(parents=True)
    manifest_path.write_text(CODEX_PLUGIN_MANIFEST_BODY, encoding="utf-8")
    return manifest_path


def source_root_with_guarded_writer(root: Path) -> Path:
    """Write the guarded-writer fixture and return the source root."""
    return write_agent_tree(
        root,
        PLUGIN_NAME,
        {GUARDED_WRITER_NAME: agent_conversion_fixture(GUARDED_WRITER_AGENT_FIXTURE)},
    )


def installed_environment_markers(root: Path) -> set[str]:
    """Install two plugin fixtures and return their environment markers."""
    source_root = write_agent_tree(
        root,
        "alpha",
        {GUARDED_WRITER_NAME: agent_conversion_fixture(GUARDED_WRITER_AGENT_FIXTURE)},
    )
    write_agent_tree(
        root,
        "beta",
        {
            READ_ONLY_REVIEWER_NAME: agent_conversion_fixture(
                READ_ONLY_REVIEWER_AGENT_FIXTURE
            )
        },
    )
    installed_paths = install_agents(source_root, root / CODEX_AGENTS_DIRNAME)
    return {
        toml_string(
            toml_table(
                toml_table(
                    tomllib.loads(path.read_text(encoding="utf-8")),
                    "shell_environment_policy",
                ),
                "set",
            ),
            CODEX_AGENT_ENV_VAR,
        )
        for path in installed_paths
    }


def toml_string(values: Mapping[str, object], key: str) -> str:
    """Return a TOML string value and assert the parsed shape."""
    value = values[key]
    assert isinstance(value, str)
    return value


def toml_compatible(value: object) -> object:
    """Normalize structured source values to their TOML-decoded container shape."""
    if isinstance(value, Mapping):
        return {key: toml_compatible(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [toml_compatible(item) for item in value]
    return value


def toml_table(values: Mapping[str, object], key: str) -> Mapping[str, object]:
    """Return a TOML table value and assert the parsed shape."""
    value = values[key]
    assert isinstance(value, dict)
    return cast("Mapping[str, object]", value)


def parsed_toml_skill_config(
    values: Mapping[str, object],
) -> list[Mapping[str, object]]:
    """Return ``skills.config`` entries from emitted TOML."""
    skills = toml_table(values, "skills")
    config = skills["config"]
    assert isinstance(config, list)
    parsed: list[Mapping[str, object]] = []
    for item in config:
        assert isinstance(item, dict)
        parsed.append(cast("Mapping[str, object]", item))
    return parsed


def converted_skill_config(agent: CodexAgent) -> tuple[Mapping[str, object], ...]:
    """Return the converter's structured ``skills.config`` rows."""
    skills = agent.values["skills"]
    assert isinstance(skills, Mapping)
    config = skills["config"]
    assert isinstance(config, TomlArrayTable)
    return config.rows


def converted_instruction_value(agent: CodexAgent) -> str:
    """Return converted developer instructions and assert the TOML marker."""
    value = agent.values["developer_instructions"]
    assert isinstance(value, TomlMultilineString)
    return value.value


def source_agent_marker_candidate() -> SourceAgent:
    """Return a source agent with no plugin-derived path."""
    return source_agent(
        source_path=Path(GUARDED_WRITER_AGENT_FIXTURE),
        name=GUARDED_WRITER_NAME,
    )


def invalid_generated_manifest_target(root: Path) -> tuple[Path, Path]:
    """Create an invalid generated manifest and return source and target roots."""
    source_root = root / DIST_CODEX_PLUGINS_DIR
    target_root = root / CODEX_AGENTS_DIRNAME
    target_root.mkdir()
    manifest_path = target_root / GENERATED_MANIFEST_FILENAME
    manifest_path.write_text(INVALID_MANIFEST_BODY, encoding="utf-8")
    return source_root, target_root


def untracked_identical_agent_install_roots(root: Path) -> tuple[Path, Path]:
    """Create a user-owned file matching generated content."""
    source_root = source_root_with_guarded_writer(root)
    generated_root = root / GENERATED_CODEX_AGENTS_DIRNAME
    target_root = root / CODEX_AGENTS_DIRNAME
    (generated_path,) = install_agents(source_root, generated_root)
    target_root.mkdir()
    target_path = target_root / generated_path.name
    target_path.write_text(generated_path.read_text(encoding="utf-8"), encoding="utf-8")
    return source_root, target_root


def rewritten_generated_owned_agent(root: Path) -> Path:
    """Rewrite a manifest-owned generated file and return the rewritten path."""
    source_root = source_root_with_guarded_writer(root)
    target_root = root / CODEX_AGENTS_DIRNAME
    (installed_path,) = install_agents(source_root, target_root)
    installed_path.write_text(STALE_GENERATED_CONTENT, encoding="utf-8")
    (rewritten_path,) = install_agents(source_root, target_root)
    return rewritten_path


def duplicate_filename_roots(root: Path) -> tuple[Path, Path]:
    """Create duplicate-slug source agents and return install roots."""
    source_root = write_agent_tree(
        root,
        PLUGIN_NAME,
        {
            "reviewer": agent_conversion_fixture(DUPLICATE_REVIEWER_FIXTURE),
            "reviewer-bang": agent_conversion_fixture(DUPLICATE_REVIEWER_BANG_FIXTURE),
        },
    )
    return source_root, root / CODEX_AGENTS_DIRNAME


def assert_agent_frontmatter_and_body_convert_to_codex_toml() -> None:
    """Assert baseline frontmatter and body conversion."""
    with TemporaryDirectory() as tmp:
        expected, parsed = converted_source_agent_toml(Path(tmp))
    expected_name = oracle_string(expected, "name")
    expected_skills = oracle_strings(expected, "skills")
    expected_tools = oracle_strings(expected, "tools")

    assert parsed["name"] == expected_name
    assert parsed["description"] == oracle_string(expected, "description")
    assert parsed["model"] == map_model(oracle_optional_string(expected, "model"))
    assert parsed["web_search"] == WEB_SEARCH_DISABLED
    assert "sandbox_mode" not in parsed
    assert toml_table(toml_table(parsed, "shell_environment_policy"), "set") == {
        CODEX_AGENT_ENV_VAR: (
            f"{PLUGIN_NAME}{CODEX_AGENT_ENV_SEPARATOR}{expected_name}"
        )
    }
    instructions = toml_string(parsed, "developer_instructions")
    assert expected.body in instructions
    assert all(skill in instructions for skill in expected_skills)
    assert parsed_toml_skill_config(parsed) == [
        {"name": skill, "enabled": True} for skill in expected_skills
    ]
    assert all(tool in instructions for tool in expected_tools)


def assert_folded_yaml_description_converts_to_text() -> None:
    """Assert folded YAML descriptions become plain text."""
    with TemporaryDirectory() as tmp:
        parsed = converted_folded_description_toml(Path(tmp))

    assert parsed["description"] == FOLDED_DESCRIPTION_TEXT


# The skills domain is synthesized here rather than scanned out of the live
# generated tree. Scanning it made this node's mapping evidence depend on which
# agents other plugins happen to ship: an unrelated plugin changing its skill
# counts could fail this test, and a missing generated tree could let it pass
# with an empty domain. The three cardinalities the mapping spans - none, one,
# and several - are enumerated instead.
SKILLS_DOMAIN: Final = (
    (source_agent(skills=()), ()),
    (source_agent(skills=("alpha:one",)), ("alpha:one",)),
    (
        source_agent(skills=("alpha:one", "beta:two", "gamma:three")),
        ("alpha:one", "beta:two", "gamma:three"),
    ),
)


def assert_skills_are_preserved_as_codex_config_and_guidance() -> None:
    """Assert skill entries become Codex config and developer guidance."""
    for source, expected_skills in SKILLS_DOMAIN:
        converted = convert_agent(source)
        instructions = converted_instruction_value(converted)
        guidance = CODEX_SKILLS_GUIDANCE_TEMPLATE.format(
            skills=", ".join(f"`{skill}`" for skill in expected_skills)
        )
        if not expected_skills:
            assert "skills" not in converted.values
            guidance_prefix = CODEX_SKILLS_GUIDANCE_TEMPLATE.partition("{skills}")[0]
            assert guidance_prefix not in instructions
            continue
        assert guidance in instructions
        assert converted_skill_config(converted) == tuple(
            {"name": skill, "enabled": True} for skill in expected_skills
        )


def assert_rendered_codex_agent_tree_converts_to_codex_toml() -> None:
    """Assert rendered Codex target agents preserve Codex runtime overrides."""
    with TemporaryDirectory() as tmp:
        expected, parsed = converted_default_codex_source_root_toml(Path(tmp))
    expected_skills = oracle_strings(expected, "skills")

    assert parsed["name"] == oracle_string(expected, "name")
    assert parsed["description"] == oracle_string(expected, "description")
    assert parsed["model"] == oracle_string(expected, "model")
    assert parsed["model_reasoning_effort"] == oracle_string(
        expected, "model_reasoning_effort"
    )
    assert parsed["sandbox_mode"] == oracle_string(expected, "sandbox_mode")
    assert parsed["nickname_candidates"] == list(
        oracle_strings(expected, "nickname_candidates")
    )
    source_docs_server = oracle_mapping(expected, "mcp_servers")["docs"]
    assert isinstance(source_docs_server, Mapping)
    parsed_docs_server = toml_table(toml_table(parsed, "mcp_servers"), "docs")
    assert parsed_docs_server["command"] == source_docs_server["command"]
    source_args = source_docs_server["args"]
    assert isinstance(source_args, list)
    assert parsed_docs_server["args"] == source_args
    instructions = toml_string(parsed, "developer_instructions")
    assert expected.body in instructions
    assert all(skill in instructions for skill in expected_skills)
    assert parsed_toml_skill_config(parsed) == [
        {"name": skill, "enabled": True} for skill in expected_skills
    ]


def assert_yaml_mcp_server_mappings_convert_to_codex_toml() -> None:
    """Assert YAML mapping syntax for MCP servers preserves nested config."""
    with TemporaryDirectory() as tmp:
        block_expected, block_parsed = converted_codex_agent_with_yaml_mcp_toml(
            Path(tmp),
            agent_conversion_fixture(CODEX_BLOCK_MCP_AGENT_FIXTURE),
        )
        flow_expected, flow_parsed = converted_codex_agent_with_yaml_mcp_toml(
            Path(tmp),
            agent_conversion_fixture(CODEX_FLOW_MCP_AGENT_FIXTURE),
        )

    for expected, parsed in (
        (block_expected, block_parsed),
        (flow_expected, flow_parsed),
    ):
        expected_mcp_servers = oracle_mapping(expected, "mcp_servers")
        assert toml_table(parsed, "mcp_servers") == toml_compatible(
            expected_mcp_servers
        )


def assert_explicit_empty_tools_frontmatter_converts_to_restrictive_codex_config() -> (
    None
):
    """Assert explicit empty tools maps to restrictive Codex config."""
    with TemporaryDirectory() as tmp:
        parsed = converted_empty_tools_toml(Path(tmp))

    assert parsed["web_search"] == WEB_SEARCH_DISABLED
    assert parsed["sandbox_mode"] == READ_ONLY_SANDBOX_MODE


def assert_mapping_oracles_cover_production_tables() -> None:
    """Assert the independent oracles span every production mapping key."""
    assert {source for source, _ in EXPECTED_MODEL_CORRESPONDENCE} == {
        source for source, _ in MODEL_MAPPINGS
    }
    assert {source for source, _ in EXPECTED_EFFORT_CORRESPONDENCE} == set(
        EFFORT_MAPPINGS
    )
    assert {source for source, _ in EXPECTED_PERMISSION_MODE_CORRESPONDENCE} == set(
        PERMISSION_MODE_MAPPINGS
    )
    assert set(EXPECTED_READ_ONLY_TOOLS) == READ_ONLY_TOOLS
    assert set(EXPECTED_SCRIPT_CAPABLE_TOOLS) == SCRIPT_CAPABLE_TOOLS
    assert set(EXPECTED_WEB_CAPABLE_TOOLS) == WEB_CAPABLE_TOOLS
    assert set(EXPECTED_WRITE_CAPABLE_TOOLS) == WRITE_CAPABLE_TOOLS


def assert_source_model_maps_to_codex_model() -> None:
    """Assert every source model case maps to the expected Codex model."""
    for source, expected in MODEL_CASES:
        assert map_model(source) == expected


def assert_opus_model_maps_to_distinct_top_tier_codex_model() -> None:
    """Assert opus maps to the configured top-tier Codex model."""
    converted = convert_agent(source_agent(model="opus"))

    assert converted.values["model"] == EXPECTED_TOP_TIER_MODEL
    assert str(CODEX_STRONG_MODEL) != str(CODEX_STANDARD_MODEL)


def assert_source_effort_maps_to_codex_reasoning_effort() -> None:
    """Assert every source effort case maps to the expected Codex effort."""
    for source, expected in EFFORT_CASES:
        assert map_effort(source) == expected


def assert_source_effort_reaches_converted_codex_reasoning_effort() -> None:
    """Assert mapped effort reaches converted TOML values."""
    for source, expected in EFFORT_CASES:
        converted = convert_agent(source_agent(effort=source))
        assert converted.values["model_reasoning_effort"] == expected


def assert_permission_modes_map_to_codex_sandbox_or_manual_review() -> None:
    """Assert every source permission mode maps to its Codex representation."""
    for source, expected in PERMISSION_MODE_CASES:
        assert map_permission_mode(source) == expected


def assert_supported_permission_mode_reaches_converted_codex_sandbox_mode() -> None:
    """Assert supported permission modes reach converted TOML values."""
    for source, expected in SUPPORTED_PERMISSION_MODE_CASES:
        converted = convert_agent(source_agent(permission_mode=source))
        assert converted.values["sandbox_mode"] == expected


def assert_tool_allowlist_without_web_tool_disables_web_search() -> None:
    """Assert read-only tool allowlists disable web search."""
    assert map_web_search(READ_ONLY_TOOL_ALLOWLIST) == WEB_SEARCH_DISABLED


def assert_explicit_empty_tool_allowlist_disables_web_search() -> None:
    """Assert explicit empty tool allowlists disable web search."""
    assert map_web_search(EMPTY_TOOL_ALLOWLIST) == WEB_SEARCH_DISABLED


def assert_missing_tool_allowlist_leaves_web_search_to_runtime_default() -> None:
    """Assert absent tool allowlists do not emit web-search config."""
    assert map_web_search(EMPTY_TOOL_ALLOWLIST, tools_declared=False) is None


def assert_tool_allowlist_with_web_tool_leaves_web_search_to_runtime_default() -> None:
    """Assert web-capable tools leave web search to runtime defaults."""
    assert map_web_search(WEB_CAPABLE_TOOL_ALLOWLIST) is None


def assert_all_tools_sentinel_leaves_web_search_to_runtime_default() -> None:
    """Assert the all-tools sentinel leaves web search to runtime defaults."""
    assert map_web_search(ALL_TOOLS_ALLOWLIST) is None


def assert_read_only_tool_allowlist_infers_read_only_sandbox() -> None:
    """Assert read-only tools infer read-only sandboxing."""
    assert infer_sandbox_mode(READ_ONLY_TOOL_ALLOWLIST, None) == READ_ONLY_SANDBOX_MODE


def assert_read_only_web_tool_allowlist_infers_read_only_sandbox() -> None:
    """Assert read-only plus web tools infer read-only sandboxing."""
    assert (
        infer_sandbox_mode(READ_ONLY_WEB_TOOL_ALLOWLIST, None) == READ_ONLY_SANDBOX_MODE
    )


def assert_web_capable_only_tool_allowlist_infers_read_only_sandbox() -> None:
    """Assert web-capable-only tools infer read-only sandboxing."""
    assert (
        infer_sandbox_mode(WEB_CAPABLE_TOOL_ALLOWLIST, None) == READ_ONLY_SANDBOX_MODE
    )


def assert_all_tools_sentinel_leaves_sandbox_to_runtime_default() -> None:
    """Assert the all-tools sentinel leaves sandboxing to runtime defaults."""
    assert infer_sandbox_mode(ALL_TOOLS_ALLOWLIST, None) is None


def assert_explicit_empty_tool_allowlist_infers_read_only_sandbox() -> None:
    """Assert an explicit empty tool allowlist infers read-only sandboxing."""
    assert infer_sandbox_mode(EMPTY_TOOL_ALLOWLIST, None) == READ_ONLY_SANDBOX_MODE


def assert_missing_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    """Assert absent tool allowlists leave sandboxing to runtime defaults."""
    assert infer_sandbox_mode(EMPTY_TOOL_ALLOWLIST, None, tools_declared=False) is None


def assert_write_capable_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    """Assert write-capable tools leave sandboxing to runtime defaults."""
    assert infer_sandbox_mode(WRITE_CAPABLE_TOOL_ALLOWLIST, None) is None


def assert_script_capable_tool_allowlist_leaves_sandbox_to_runtime_default() -> None:
    """Assert script-capable tools leave sandboxing to runtime defaults."""
    assert infer_sandbox_mode(SCRIPT_CAPABLE_TOOL_ALLOWLIST, None) is None


def assert_explicit_unmapped_permission_mode_blocks_read_only_inference() -> None:
    """Assert every unmapped permission mode blocks sandbox inference."""
    for source in UNMAPPED_PERMISSION_MODE_CASES:
        assert infer_sandbox_mode(READ_ONLY_TOOL_ALLOWLIST, source) is None


def assert_unmapped_permission_mode_converts_to_manual_review_guidance() -> None:
    """Assert every unmapped permission mode becomes manual-review guidance."""
    for source in UNMAPPED_PERMISSION_MODE_CASES:
        converted = convert_agent(
            source_agent(
                permission_mode=source,
                tools=READ_ONLY_TOOL_ALLOWLIST,
                tools_declared=True,
            )
        )
        instructions = converted_instruction_value(converted)

        assert "sandbox_mode" not in converted.values
        assert f"permissionMode: {source}" in instructions
        assert "manual-review guidance" in instructions


def assert_write_capable_tool_allowlist_converts_to_manual_review_guidance() -> None:
    """Assert write-capable tools become manual-review guidance."""
    converted = convert_agent(
        source_agent(
            source_path=WRITER_SOURCE_PATH,
            name="writer",
            description=WRITER_DESCRIPTION,
            body=WRITER_BODY,
            tools=SORTED_WRITE_CAPABLE_TOOL_ALLOWLIST,
            tools_declared=True,
        )
    )
    instructions = converted_instruction_value(converted)
    guidance = CODEX_TOOLS_GUIDANCE_TEMPLATE.format(
        tools=", ".join(f"`{tool}`" for tool in SORTED_WRITE_CAPABLE_TOOL_ALLOWLIST)
    )

    assert "sandbox_mode" not in converted.values
    assert guidance in instructions


def assert_manual_guidance_preserves_source_only_fields() -> None:
    """Assert source-only fields remain as manual-review guidance."""
    with TemporaryDirectory() as tmp:
        expected, parsed = installed_guarded_writer_toml(Path(tmp))
    expected_skills = oracle_strings(expected, "skills")
    expected_tools = oracle_strings(expected, "tools")
    expected_disallowed_tools = oracle_strings(expected, "disallowedTools")
    expected_unsupported_fields = tuple(
        sorted(
            field
            for field in expected.frontmatter
            if field not in SUPPORTED_FRONTMATTER_FIELDS
        )
    )

    instructions = toml_string(parsed, "developer_instructions")
    expected_guidance = (
        CODEX_SKILLS_GUIDANCE_TEMPLATE.format(
            skills=", ".join(f"`{skill}`" for skill in expected_skills)
        ),
        CODEX_TOOLS_GUIDANCE_TEMPLATE.format(
            tools=", ".join(f"`{tool}`" for tool in expected_tools)
        ),
        CODEX_DISALLOWED_TOOLS_GUIDANCE_TEMPLATE.format(
            tools=", ".join(f"`{tool}`" for tool in expected_disallowed_tools)
        ),
        CODEX_PERMISSION_MODE_GUIDANCE_TEMPLATE.format(
            permission_mode=oracle_string(expected, "permissionMode")
        ),
        CODEX_UNSUPPORTED_FIELDS_GUIDANCE_TEMPLATE.format(
            fields=", ".join(f"`{field}`" for field in expected_unsupported_fields)
        ),
    )
    assert parsed["model"] == CODEX_STRONG_MODEL
    assert all(guidance in instructions for guidance in expected_guidance)
    assert MANUAL_REVIEW_GUIDANCE_OPEN in instructions
    assert MANUAL_REVIEW_GUIDANCE_CLOSE in instructions
    assert "##" not in instructions
    assert "sandbox_mode" not in parsed


def assert_default_source_root_uses_rendered_codex_agents() -> None:
    """Assert the default converter source root is generated Codex output."""
    assert DEFAULT_SOURCE_ROOT == Path("dist") / "codex"


def assert_generated_toml_stays_outside_codex_plugin_manifest_content() -> None:
    """Assert local generated TOML does not mutate plugin manifest content."""
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_root = source_root_with_guarded_writer(root)
        manifest_path = write_codex_plugin_manifest(root)
        install_agents(source_root, root / CODEX_AGENTS_DIRNAME)
        assert not tuple(manifest_path.parent.parent.rglob("*.toml"))
        assert manifest_path.read_text(encoding="utf-8") == CODEX_PLUGIN_MANIFEST_BODY


def assert_environment_marker_is_namespaced_by_source_plugin() -> None:
    """Assert markers contain the source plugin and exact generated agent type."""
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        markers = installed_environment_markers(root)
        slugged_source_path = write_agent_source(
            root,
            PLUGIN_NAME,
            Path(DUPLICATE_REVIEWER_BANG_FIXTURE).stem,
            agent_conversion_fixture(DUPLICATE_REVIEWER_BANG_FIXTURE),
        )
        slugged_source = parse_agent_markdown(slugged_source_path)
        slugged_agent = convert_agent(slugged_source)

    assert markers == {
        f"alpha{CODEX_AGENT_ENV_SEPARATOR}{GUARDED_WRITER_NAME}",
        f"beta{CODEX_AGENT_ENV_SEPARATOR}{READ_ONLY_REVIEWER_NAME}",
    }
    assert slugged_agent.filename == EXPECTED_SLUGGED_AGENT_FILENAME
    assert agent_environment_marker(slugged_source) == (
        f"{PLUGIN_NAME}{CODEX_AGENT_ENV_SEPARATOR}{EXPECTED_SLUGGED_AGENT_TYPE}"
    )


def assert_environment_marker_without_source_plugin_is_rejected() -> None:
    """Assert a source path without a plugin namespace is rejected."""
    try:
        agent_environment_marker(source_agent_marker_candidate())
    except AgentConversionError as exc:
        assert "agent source path must be under <plugin>/agents" in str(exc)
    else:
        msg = (
            "source path without a plugin namespace did not raise AgentConversionError"
        )
        raise AssertionError(msg)


def assert_invalid_generated_manifest_uses_converter_error() -> None:
    """Assert invalid generated-agent manifests raise converter errors."""
    with TemporaryDirectory() as tmp:
        source_root, target_root = invalid_generated_manifest_target(Path(tmp))
        try:
            install_agents(source_root, target_root)
        except AgentConversionError as exc:
            assert "invalid generated-agent manifest" in str(exc)
        else:
            msg = "invalid generated-agent manifest did not raise AgentConversionError"
            raise AssertionError(msg)


def assert_install_refuses_to_claim_untracked_identical_agent() -> None:
    """Assert untracked matching files remain user-owned."""
    with TemporaryDirectory() as tmp:
        source_root, target_root = untracked_identical_agent_install_roots(Path(tmp))
        try:
            install_agents(source_root, target_root)
        except AgentConversionError as exc:
            assert "refusing to overwrite user-owned Codex agent" in str(exc)
        else:
            msg = "untracked identical agent did not raise AgentConversionError"
            raise AssertionError(msg)
        assert not (target_root / GENERATED_MANIFEST_FILENAME).exists()


def assert_install_overwrites_generated_owned_agent_from_manifest() -> None:
    """Assert manifest-owned generated files can be updated."""
    with TemporaryDirectory() as tmp:
        rewritten_path = rewritten_generated_owned_agent(Path(tmp))
        assert STALE_GENERATED_CONTENT not in rewritten_path.read_text(encoding="utf-8")


def assert_duplicate_generated_agent_filename_fails_before_install_writes() -> None:
    """Assert duplicate generated filenames fail before target writes."""
    with TemporaryDirectory() as tmp:
        source_root, target_root = duplicate_filename_roots(Path(tmp))
        try:
            install_agents(source_root, target_root)
        except AgentConversionError as exc:
            assert "multiple source agents convert" in str(exc)
        else:
            msg = "duplicate generated filename did not raise AgentConversionError"
            raise AssertionError(msg)
        assert not target_root.exists()
