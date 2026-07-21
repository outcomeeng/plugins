"""Convert rendered plugin agent definitions into local Codex custom agents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

SUPPORTED_FRONTMATTER_FIELDS: Final = frozenset(
    {
        "name",
        "description",
        "model",
        "model_reasoning_effort",
        "effort",
        "sandbox_mode",
        "nickname_candidates",
        "mcp_servers",
        "permissionMode",
        "skills",
        "tools",
        "disallowedTools",
    }
)
GENERATED_MANIFEST_FILENAME: Final = ".outcomeeng-generated-agents.json"
DEFAULT_SOURCE_ROOT: Final = Path("dist") / "codex"
DEFAULT_TARGET_ROOT: Final = Path.home() / ".codex" / "agents"
AGENT_SOURCE_DIRECTORY_NAME: Final = "agents"
CODEX_STRONG_MODEL: Final = "gpt-5.5"
CODEX_STANDARD_MODEL: Final = "gpt-5.4"
CODEX_FAST_MODEL: Final = "gpt-5.4-mini"
MODEL_MAPPINGS: Final = (
    ("claude-opus", CODEX_STRONG_MODEL),
    ("opus", CODEX_STRONG_MODEL),
    ("claude-sonnet", CODEX_STANDARD_MODEL),
    ("sonnet", CODEX_STANDARD_MODEL),
    ("claude-haiku", CODEX_FAST_MODEL),
    ("haiku", CODEX_FAST_MODEL),
)
EFFORT_MAPPINGS: Final = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "max": "xhigh",
}
PERMISSION_MODE_MAPPINGS: Final[Mapping[str, str | None]] = {
    "default": None,
    "acceptEdits": "workspace-write",
    "auto": None,
    "dontAsk": None,
    "bypassPermissions": None,
    "plan": "read-only",
}
INHERIT_MODEL_VALUE: Final = "inherit"
MODEL_PREFIX_EXAMPLE_SUFFIX: Final = "-example"
ALL_TOOLS_SENTINEL: Final = "all"
CODEX_AGENT_ENV_VAR: Final = "OUTCOMEENG_CODEX_AGENT_NAME"
CODEX_AGENT_ENV_SEPARATOR: Final = "/"
CODEX_SKILLS_GUIDANCE_TEMPLATE: Final = (
    "Source `skills` entries were preserved as prompt guidance. "
    "The generated Codex `skills.config` entries enable these skills; "
    "they are not a spawn-time preload guarantee. Invoke or load these "
    "skills before relying on this agent's specialized behavior: {skills}."
)
CODEX_TOOLS_GUIDANCE_TEMPLATE: Final = (
    "Source `tools` allowlists can map only to Codex configuration "
    "boundaries with matching semantics. Treat command-level meanings "
    "inside allowed shell tools as manual-review guidance: {tools}."
)
CODEX_DISALLOWED_TOOLS_GUIDANCE_TEMPLATE: Final = (
    "Source `disallowedTools` deny lists do not enforce Codex permissions. "
    "Treat these tools as manual-review guidance unless runtime policy "
    "enforces them: {tools}."
)
CODEX_PERMISSION_MODE_GUIDANCE_TEMPLATE: Final = (
    "Source `permissionMode: {permission_mode}` has no direct Codex mapping. "
    "Choose the appropriate sandbox, permissions, MCP tool filters, or app "
    "tool filters before relying on this agent for write or network behavior."
)
CODEX_UNSUPPORTED_FIELDS_GUIDANCE_TEMPLATE: Final = (
    "Review unsupported source agent fields manually: {fields}."
)
MANUAL_REVIEW_GUIDANCE_TAG: Final = "manual_review_guidance"
MANUAL_REVIEW_GUIDANCE_OPEN: Final = f"<{MANUAL_REVIEW_GUIDANCE_TAG}>"
MANUAL_REVIEW_GUIDANCE_CLOSE: Final = f"</{MANUAL_REVIEW_GUIDANCE_TAG}>"
READ_ONLY_SANDBOX_MODE: Final = "read-only"
WEB_SEARCH_DISABLED: Final = "disabled"
READ_ONLY_TOOLS: Final = frozenset({"Glob", "Grep", "Read"})
SCRIPT_CAPABLE_TOOLS: Final = frozenset({"Bash", "Skill"})
WEB_CAPABLE_TOOLS: Final = frozenset({"WebFetch", "WebSearch"})
WRITE_CAPABLE_TOOLS: Final = frozenset({"Edit", "NotebookEdit", "Write"})


class AgentConversionError(Exception):
    """Agent conversion or installation failed."""


@dataclass(frozen=True)
class SourceAgent:
    """Parsed rendered plugin agent markdown."""

    source_path: Path
    name: str
    description: str
    body: str
    model: str | None = None
    model_reasoning_effort: str | None = None
    effort: str | None = None
    sandbox_mode: str | None = None
    nickname_candidates: tuple[str, ...] = ()
    mcp_servers: Mapping[str, object] | None = None
    permission_mode: str | None = None
    skills: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    tools_declared: bool = False
    disallowed_tools: tuple[str, ...] = ()
    unsupported_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class CodexAgent:
    """Converted Codex custom-agent definition."""

    filename: str
    values: Mapping[str, object]


@dataclass(frozen=True)
class TomlMultilineString:
    """Marker for TOML multi-line strings."""

    value: str


@dataclass(frozen=True)
class TomlArrayTable:
    """Explicit TOML array-of-tables value."""

    rows: tuple[Mapping[str, object], ...]


def iter_agent_files(source_root: Path) -> tuple[Path, ...]:
    """Return rendered agent markdown files under ``source_root``."""
    if not source_root.is_dir():
        return ()
    return tuple(sorted(source_root.glob("*/agents/*.md")))


def parse_agent_markdown(path: Path) -> SourceAgent:
    """Parse one rendered plugin agent markdown file."""
    frontmatter, body = _split_frontmatter(path.read_text(encoding="utf-8"))
    name = _optional_string(frontmatter, "name") or path.stem
    description = _optional_string(frontmatter, "description") or (
        f"Converted source agent from {path.name}."
    )
    unsupported_fields = tuple(
        sorted(key for key in frontmatter if key not in SUPPORTED_FRONTMATTER_FIELDS)
    )
    return SourceAgent(
        source_path=path,
        name=name,
        description=description,
        body=body,
        model=_optional_string(frontmatter, "model"),
        model_reasoning_effort=_optional_string(frontmatter, "model_reasoning_effort"),
        effort=_optional_string(frontmatter, "effort"),
        sandbox_mode=_optional_string(frontmatter, "sandbox_mode"),
        nickname_candidates=_string_tuple(frontmatter, "nickname_candidates"),
        mcp_servers=_optional_mapping(frontmatter, "mcp_servers"),
        permission_mode=_optional_string(frontmatter, "permissionMode"),
        skills=_string_tuple(frontmatter, "skills"),
        tools=_string_tuple(frontmatter, "tools"),
        tools_declared="tools" in frontmatter,
        disallowed_tools=_string_tuple(frontmatter, "disallowedTools"),
        unsupported_fields=unsupported_fields,
    )


def parse_agent_text(text: str, *, source_path: Path, name: str) -> SourceAgent:
    """Parse rendered plugin agent markdown already held as text.

    The build renders an agent's source before converting it, so conversion
    reads the rendered text rather than re-reading the authored file. ``name``
    is the converted agent's identity, which the caller derives from the target
    namespace — a flat namespace carries the plugin slug as a prefix.
    """
    frontmatter, body = _split_frontmatter(text)
    description = _optional_string(frontmatter, "description") or (
        f"Converted source agent from {source_path.name}."
    )
    unsupported_fields = tuple(
        sorted(key for key in frontmatter if key not in SUPPORTED_FRONTMATTER_FIELDS)
    )
    return SourceAgent(
        source_path=source_path,
        name=name,
        description=description,
        body=body,
        model=_optional_string(frontmatter, "model"),
        model_reasoning_effort=_optional_string(frontmatter, "model_reasoning_effort"),
        effort=_optional_string(frontmatter, "effort"),
        sandbox_mode=_optional_string(frontmatter, "sandbox_mode"),
        nickname_candidates=_string_tuple(frontmatter, "nickname_candidates"),
        mcp_servers=_optional_mapping(frontmatter, "mcp_servers"),
        permission_mode=_optional_string(frontmatter, "permissionMode"),
        skills=_string_tuple(frontmatter, "skills"),
        tools=_string_tuple(frontmatter, "tools"),
        tools_declared="tools" in frontmatter,
        disallowed_tools=_string_tuple(frontmatter, "disallowedTools"),
        unsupported_fields=unsupported_fields,
    )


def convert_agent_markdown(text: str, *, source_path: Path, name: str) -> str:
    """Return the target-native agent artifact for rendered agent markdown."""
    return render_agent_toml(
        convert_agent(parse_agent_text(text, source_path=source_path, name=name))
    )


def convert_agent(agent: SourceAgent) -> CodexAgent:
    """Convert one rendered plugin agent into a Codex custom-agent representation."""
    values: dict[str, object] = {
        "name": agent.name,
        "description": agent.description,
    }
    model = map_model(agent.model)
    if model is not None:
        values["model"] = model
    effort = agent.model_reasoning_effort or map_effort(agent.effort)
    if effort is not None:
        values["model_reasoning_effort"] = effort
    sandbox_mode = agent.sandbox_mode or map_permission_mode(agent.permission_mode)
    if sandbox_mode is None:
        sandbox_mode = infer_sandbox_mode(
            agent.tools,
            agent.permission_mode,
            tools_declared=agent.tools_declared,
        )
    if sandbox_mode is not None:
        values["sandbox_mode"] = sandbox_mode
    web_search = map_web_search(agent.tools, tools_declared=agent.tools_declared)
    if web_search is not None:
        values["web_search"] = web_search
    if agent.nickname_candidates:
        values["nickname_candidates"] = agent.nickname_candidates
    if agent.mcp_servers:
        values["mcp_servers"] = agent.mcp_servers
    if agent.skills:
        values["skills"] = {
            "config": TomlArrayTable(
                tuple({"name": skill, "enabled": True} for skill in agent.skills)
            )
        }
    values["shell_environment_policy"] = {
        "set": {
            CODEX_AGENT_ENV_VAR: agent_environment_marker(agent),
        },
    }
    values["developer_instructions"] = TomlMultilineString(
        render_developer_instructions(agent)
    )
    return CodexAgent(filename=f"{generated_agent_type(agent)}.toml", values=values)


def map_model(model: str | None) -> str | None:
    """Map source model names to Codex model slugs."""
    if model is None or model == INHERIT_MODEL_VALUE:
        return None
    for source_prefix, target_model in MODEL_MAPPINGS:
        if model == source_prefix or model.startswith(source_prefix):
            return target_model
    return model


def agent_environment_marker(agent: SourceAgent) -> str:
    """Return the stable Codex policy marker for a converted agent."""
    plugin_name = _source_plugin_name(agent.source_path)
    if plugin_name is None:
        raise AgentConversionError(
            f"agent source path must be under <plugin>/agents: {agent.source_path}"
        )
    return f"{plugin_name}{CODEX_AGENT_ENV_SEPARATOR}{generated_agent_type(agent)}"


def generated_agent_type(agent: SourceAgent) -> str:
    """Return the generated Codex agent type for a source agent."""
    return _slugify(agent.name)


def map_effort(effort: str | None) -> str | None:
    """Map source effort values to Codex reasoning effort values."""
    if effort is None:
        return None
    return EFFORT_MAPPINGS.get(effort, effort)


def map_permission_mode(permission_mode: str | None) -> str | None:
    """Map supported source permission modes to Codex sandbox modes."""
    if permission_mode is None:
        return None
    return PERMISSION_MODE_MAPPINGS.get(permission_mode)


def map_web_search(
    tools: Sequence[str],
    *,
    tools_declared: bool = True,
) -> str | None:
    """Return the Codex web-search mode implied by an explicit source tool allowlist."""
    tool_set = set(tools)
    if not tools_declared or ALL_TOOLS_SENTINEL in tool_set:
        return None
    if tool_set & WEB_CAPABLE_TOOLS:
        return None
    return WEB_SEARCH_DISABLED


def infer_sandbox_mode(
    tools: Sequence[str],
    permission_mode: str | None,
    *,
    tools_declared: bool = True,
) -> str | None:
    """Infer a Codex sandbox from an explicit source tool allowlist."""
    tool_set = set(tools)
    if (
        permission_mode is not None
        or not tools_declared
        or ALL_TOOLS_SENTINEL in tool_set
    ):
        return None
    if tool_set & (SCRIPT_CAPABLE_TOOLS | WRITE_CAPABLE_TOOLS):
        return None
    if tool_set.issubset(READ_ONLY_TOOLS | WEB_CAPABLE_TOOLS):
        return READ_ONLY_SANDBOX_MODE
    return None


def render_developer_instructions(agent: SourceAgent) -> str:
    """Render the Codex developer-instruction body."""
    sections = [agent.body.strip()]
    guidance: list[str] = []

    if agent.skills:
        guidance.append(
            CODEX_SKILLS_GUIDANCE_TEMPLATE.format(
                skills=", ".join(f"`{skill}`" for skill in agent.skills)
            )
        )

    if agent.tools:
        guidance.append(
            CODEX_TOOLS_GUIDANCE_TEMPLATE.format(
                tools=", ".join(f"`{tool}`" for tool in agent.tools)
            )
        )

    if agent.disallowed_tools:
        guidance.append(
            CODEX_DISALLOWED_TOOLS_GUIDANCE_TEMPLATE.format(
                tools=", ".join(f"`{tool}`" for tool in agent.disallowed_tools)
            )
        )

    if agent.permission_mode and map_permission_mode(agent.permission_mode) is None:
        guidance.append(
            CODEX_PERMISSION_MODE_GUIDANCE_TEMPLATE.format(
                permission_mode=agent.permission_mode
            )
        )

    if agent.unsupported_fields:
        guidance.append(
            CODEX_UNSUPPORTED_FIELDS_GUIDANCE_TEMPLATE.format(
                fields=", ".join(f"`{field}`" for field in agent.unsupported_fields)
            )
        )

    if guidance:
        sections.append(
            f"{MANUAL_REVIEW_GUIDANCE_OPEN}\n"
            + "\n\n".join(guidance)
            + f"\n{MANUAL_REVIEW_GUIDANCE_CLOSE}"
        )
    return "\n\n".join(section for section in sections if section).strip() + "\n"


def render_agent_toml(agent: CodexAgent) -> str:
    """Render one converted agent as TOML."""
    return _render_toml_document(agent.values)


def convert_agents(source_root: Path = DEFAULT_SOURCE_ROOT) -> tuple[CodexAgent, ...]:
    """Convert all rendered plugin agents under ``source_root``."""
    converted: list[CodexAgent] = []
    seen: set[str] = set()
    for source_file in iter_agent_files(source_root):
        converted_agent = convert_agent(parse_agent_markdown(source_file))
        if converted_agent.filename in seen:
            raise AgentConversionError(
                f"multiple source agents convert to {converted_agent.filename}"
            )
        seen.add(converted_agent.filename)
        converted.append(converted_agent)
    return tuple(converted)


def install_agents(
    source_root: Path = DEFAULT_SOURCE_ROOT,
    target_root: Path = DEFAULT_TARGET_ROOT,
    *,
    manifest_name: str = GENERATED_MANIFEST_FILENAME,
) -> tuple[Path, ...]:
    """Install converted agents and remove stale generated files."""
    converted = convert_agents(source_root)
    target_root.mkdir(parents=True, exist_ok=True)
    manifest_path = target_root / manifest_name
    previous = _read_generated_manifest(manifest_path)
    current_files = frozenset(agent.filename for agent in converted)

    for filename in sorted(previous - current_files):
        stale_path = target_root / filename
        if stale_path.exists():
            stale_path.unlink()

    written: list[Path] = []
    generated_owned = set(previous)
    for agent in converted:
        target_path = target_root / agent.filename
        rendered = render_agent_toml(agent)
        if target_path.exists() and agent.filename not in generated_owned:
            raise AgentConversionError(
                f"refusing to overwrite user-owned Codex agent: {target_path}"
            )
        target_path.write_text(rendered, encoding="utf-8")
        written.append(target_path)

    manifest_path.write_text(
        json.dumps({"generated": sorted(current_files)}, indent=2) + "\n",
        encoding="utf-8",
    )
    return tuple(written)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            installed = install_agents(
                args.source_root,
                args.target_root,
                manifest_name=args.manifest_name,
            )
            print(f"installed {len(installed)} Codex agent(s) into {args.target_root}")
            return 0
        converted = convert_agents(args.source_root)
        for agent in converted:
            sys.stdout.write(f"# {agent.filename}\n")
            sys.stdout.write(render_agent_toml(agent))
        return 0
    except AgentConversionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outcomeeng.distribution.agents",
        description="Convert rendered plugin agents into Codex custom-agent TOML.",
    )
    subparsers = parser.add_subparsers(dest="command")
    install = subparsers.add_parser("install")
    install.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    install.add_argument("--target-root", type=Path, default=DEFAULT_TARGET_ROOT)
    install.add_argument(
        "--manifest-name",
        default=GENERATED_MANIFEST_FILENAME,
        help="Generated-file manifest stored under the target root.",
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    return parser


def _read_generated_manifest(path: Path) -> frozenset[str]:
    if not path.is_file():
        return frozenset()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AgentConversionError(f"invalid generated-agent manifest: {path}") from exc
    generated = data.get("generated", [])
    if not isinstance(generated, list) or not all(
        isinstance(item, str) for item in generated
    ):
        raise AgentConversionError(f"invalid generated-agent manifest: {path}")
    return frozenset(generated)


def _split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text
    closing_index = text.find("\n---", len("---\n"))
    if closing_index == -1:
        raise AgentConversionError("agent frontmatter has no closing fence")
    raw_frontmatter = text[len("---\n") : closing_index]
    fence_end = closing_index + len("\n---")
    body = text[fence_end:].lstrip("\r\n")
    return _parse_yaml_mapping(raw_frontmatter), body


def _parse_yaml_mapping(text: str) -> dict[str, object]:
    values: dict[str, object] = {}
    current_key: str | None = None
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        if not raw_line.strip():
            index += 1
            continue
        if raw_line.startswith("  - ") and current_key is not None:
            _append_yaml_sequence_item(values, current_key, raw_line[4:].strip())
            index += 1
            continue
        parsed_key, index = _parse_yaml_mapping_line(values, lines, index)
        current_key = parsed_key or current_key
    return values


def _append_yaml_sequence_item(
    values: dict[str, object],
    key: str,
    raw_value: str,
) -> None:
    existing = values.setdefault(key, [])
    if not isinstance(existing, list):
        existing = [existing]
        values[key] = existing
    existing.append(_parse_yaml_scalar(raw_value))


def _parse_yaml_mapping_line(
    values: dict[str, object],
    lines: Sequence[str],
    index: int,
) -> tuple[str | None, int]:
    key, separator, raw_value = lines[index].partition(":")
    if not separator:
        return None, index + 1
    current_key = key.strip()
    value = raw_value.strip()
    if _is_yaml_block_scalar(value):
        block_lines, next_index = _collect_yaml_block(lines, index + 1)
        values[current_key] = _parse_yaml_block_scalar(value, block_lines)
        return current_key, next_index
    if value:
        values[current_key] = _parse_yaml_scalar(value)
        return current_key, index + 1
    return current_key, _parse_yaml_empty_mapping_value(
        values, current_key, lines, index
    )


def _parse_yaml_empty_mapping_value(
    values: dict[str, object],
    key: str,
    lines: Sequence[str],
    index: int,
) -> int:
    block_lines, next_index = _collect_yaml_indented_block(lines, index + 1)
    values[key] = _parse_yaml_nested_block(block_lines) if block_lines else []
    return next_index if block_lines else index + 1


def _is_yaml_block_scalar(value: str) -> bool:
    return value in {"|", "|-", "|+", ">", ">-", ">+"}


def _collect_yaml_block(
    lines: Sequence[str], start: int
) -> tuple[tuple[str, ...], int]:
    block: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if line.startswith((" ", "\t")) or not line.strip():
            block.append(line)
            index += 1
            continue
        break
    return tuple(block), index


def _collect_yaml_indented_block(
    lines: Sequence[str],
    start: int,
) -> tuple[tuple[str, ...], int]:
    block: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if line.startswith((" ", "\t")) or not line.strip():
            block.append(line)
            index += 1
            continue
        break
    return tuple(block), index


def _parse_yaml_nested_block(raw_lines: Sequence[str]) -> object:
    lines = _dedent_yaml_block(raw_lines)
    first = next((line.strip() for line in lines if line.strip()), "")
    if first.startswith("- "):
        return _parse_yaml_sequence_block(lines)
    return _parse_yaml_mapping("\n".join(lines))


def _parse_yaml_sequence_block(lines: Sequence[str]) -> tuple[object, ...]:
    items: list[object] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if not stripped.startswith("- "):
            index += 1
            continue
        continuation, next_index = _collect_yaml_sequence_continuation(lines, index + 1)
        items.append(_parse_yaml_sequence_item(stripped[2:].strip(), continuation))
        index = next_index
    return tuple(items)


def _collect_yaml_sequence_continuation(
    lines: Sequence[str],
    start: int,
) -> tuple[tuple[str, ...], int]:
    block: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if line.strip().startswith("- "):
            break
        block.append(line)
        index += 1
    return tuple(block), index


def _parse_yaml_sequence_item(
    raw_value: str,
    raw_continuation: Sequence[str],
) -> object:
    continuation = _dedent_yaml_block(raw_continuation)
    if not continuation:
        return _parse_yaml_scalar(raw_value)
    if not raw_value:
        return _parse_yaml_nested_block(continuation)
    if ":" in raw_value:
        return _parse_yaml_mapping("\n".join((raw_value, *continuation)))
    return _parse_yaml_scalar(raw_value)


def _parse_yaml_block_scalar(style: str, raw_lines: Sequence[str]) -> str:
    lines = _dedent_yaml_block(raw_lines)
    if style.startswith("|"):
        text = "\n".join(lines)
    else:
        text = _fold_yaml_lines(lines)
    if style.endswith("+"):
        return text + "\n"
    return text.rstrip("\n")


def _dedent_yaml_block(raw_lines: Sequence[str]) -> tuple[str, ...]:
    nonblank_indents = [
        len(line) - len(line.lstrip(" ")) for line in raw_lines if line.strip()
    ]
    indent = min(nonblank_indents, default=0)
    return tuple(line[indent:] if len(line) >= indent else "" for line in raw_lines)


def _fold_yaml_lines(lines: Sequence[str]) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line.strip():
            if current:
                paragraphs.append(" ".join(current))
                current = []
            paragraphs.append("")
            continue
        current.append(line.strip())
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(paragraphs)


def _parse_yaml_scalar(value: str) -> object:
    for parser in (
        _parse_yaml_braced_scalar,
        _parse_yaml_sequence_scalar,
        _parse_yaml_quoted_scalar,
        _parse_yaml_keyword_scalar,
        _parse_yaml_numeric_scalar,
    ):
        parsed, handled = parser(value)
        if handled:
            return parsed
    return value


def _parse_yaml_braced_scalar(value: str) -> tuple[object, bool]:
    if not (value.startswith("{") and value.endswith("}")):
        return None, False
    try:
        return json.loads(value), True
    except json.JSONDecodeError:
        parsed = _parse_yaml_flow_mapping(value)
        return (parsed, True) if parsed is not None else (None, False)


def _parse_yaml_sequence_scalar(value: str) -> tuple[object, bool]:
    if not (value.startswith("[") and value.endswith("]")):
        return None, False
    return (
        [
            _parse_yaml_scalar(part)
            for part in _split_delimited(value[1:-1])
            if part.strip()
        ],
        True,
    )


def _parse_yaml_quoted_scalar(value: str) -> tuple[object, bool]:
    if value.startswith(("'", '"')) and value.endswith(value[0]):
        return value[1:-1], True
    return None, False


def _parse_yaml_keyword_scalar(value: str) -> tuple[object, bool]:
    lower_value = value.lower()
    if lower_value == "true":
        return True, True
    if lower_value == "false":
        return False, True
    if lower_value in {"null", "~"}:
        return None, True
    return None, False


def _parse_yaml_numeric_scalar(value: str) -> tuple[object, bool]:
    integer = _parse_yaml_integer(value)
    if integer is not None:
        return integer, True
    yaml_float = _parse_yaml_float(value)
    if yaml_float is not None:
        return yaml_float, True
    return None, False


def _parse_yaml_integer(value: str) -> int | None:
    digits = _strip_numeric_sign(value)
    if not digits.isdigit():
        return None
    if digits != "0" and digits.startswith("0"):
        return None
    return int(value)


def _parse_yaml_float(value: str) -> float | None:
    body, exponent = _split_numeric_exponent(_strip_numeric_sign(value))
    if exponent is not None and not _is_signed_digits(exponent):
        return None
    if "." not in body:
        return None
    whole, _, fractional = body.partition(".")
    if not whole and not fractional:
        return None
    if (whole and not whole.isdigit()) or (fractional and not fractional.isdigit()):
        return None
    return float(value)


def _strip_numeric_sign(value: str) -> str:
    return value[1:] if value.startswith(("+", "-")) else value


def _split_numeric_exponent(value: str) -> tuple[str, str | None]:
    for marker in ("e", "E"):
        if marker in value:
            body, _, exponent = value.partition(marker)
            return body, exponent
    return value, None


def _is_signed_digits(value: str) -> bool:
    return bool(value) and _strip_numeric_sign(value).isdigit()


def _parse_yaml_flow_mapping(value: str) -> dict[str, object] | None:
    body = value[1:-1].strip()
    if not body:
        return {}
    parsed: dict[str, object] = {}
    for part in _split_delimited(body):
        key, separator, raw_value = _partition_flow_pair(part)
        if not separator:
            return None
        parsed[_strip_yaml_quotes(key.strip())] = _parse_yaml_scalar(raw_value.strip())
    return parsed


def _partition_flow_pair(value: str) -> tuple[str, str, str]:
    quote: str | None = None
    depth = 0
    for index, char in enumerate(value):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char in "{[":
            depth += 1
            continue
        if char in "}]":
            depth -= 1
            continue
        if char == ":" and depth == 0:
            return value[:index], char, value[index + 1 :]
    return value, "", ""


def _strip_yaml_quotes(value: str) -> str:
    if value.startswith(("'", '"')) and value.endswith(value[0]):
        return value[1:-1]
    return value


def _split_delimited(text: str) -> tuple[str, ...]:
    values: list[str] = []
    token: list[str] = []
    quote: str | None = None
    depth = 0
    for char in text:
        if quote:
            token.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            token.append(char)
            continue
        if char in "{[":
            depth += 1
            token.append(char)
            continue
        if char in "}]":
            depth -= 1
            token.append(char)
            continue
        if char == "," and depth == 0:
            values.append("".join(token).strip())
            token = []
            continue
        token.append(char)
    values.append("".join(token).strip())
    return tuple(values)


def _optional_string(values: Mapping[str, object], key: str) -> str | None:
    value = values.get(key)
    if value is None:
        return None
    return str(value)


def _string_tuple(values: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = values.get(key)
    if value is None:
        return ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return tuple(
        part for part in (part.strip() for part in str(value).split(",")) if part
    )


def _optional_mapping(
    values: Mapping[str, object],
    key: str,
) -> Mapping[str, object] | None:
    value = values.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        return None
    return {str(map_key): map_value for map_key, map_value in value.items()}


def _slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-").lower() or "agent"


def _source_plugin_name(path: Path) -> str | None:
    if path.parent.name != AGENT_SOURCE_DIRECTORY_NAME:
        return None
    plugin_dir = path.parent.parent
    if plugin_dir == path.parent:
        return None
    return plugin_dir.name or None


def _render_toml_document(values: Mapping[str, object]) -> str:
    lines: list[str] = []
    table_values: list[tuple[str, Mapping[str, object]]] = []
    for key, value in values.items():
        if isinstance(value, Mapping):
            table_values.append((key, value))
            continue
        lines.append(f"{_format_toml_key(key)} = {_format_toml_value(value)}")
    for key, table in table_values:
        _append_toml_table(lines, key=key, table=table)
    return "\n".join(lines) + "\n"


def _append_toml_table(
    lines: list[str],
    *,
    key: str,
    table: Mapping[str, object],
) -> None:
    if lines:
        lines.append("")
    lines.append(f"[{_format_toml_key(key)}]")
    for table_key, table_value in table.items():
        if isinstance(table_value, TomlArrayTable):
            _append_toml_array_table(
                lines,
                key=key,
                table_key=str(table_key),
                value=table_value,
            )
            continue
        lines.append(
            f"{_format_toml_key(str(table_key))} = {_format_toml_value(table_value)}"
        )


def _append_toml_array_table(
    lines: list[str],
    *,
    key: str,
    table_key: str,
    value: TomlArrayTable,
) -> None:
    for item in value.rows:
        lines.append("")
        lines.append(f"[[{_format_toml_key(key)}.{_format_toml_key(table_key)}]]")
        lines.extend(
            f"{_format_toml_key(str(nested_key))} = {_format_toml_value(nested_value)}"
            for nested_key, nested_value in item.items()
        )


def _format_toml_key(key: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return json.dumps(key)


def _format_toml_value(value: object) -> str:
    if isinstance(value, TomlMultilineString):
        return _format_toml_multiline(value.value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return '""'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, Mapping):
        items = (
            f"{_format_toml_key(str(key))} = {_format_toml_value(item)}"
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        )
        return "{ " + ", ".join(items) + " }"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return "[" + ", ".join(_format_toml_value(item) for item in value) + "]"
    return json.dumps(str(value))


def _format_toml_multiline(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    return f'"""{escaped}"""'


__all__ = [
    "AGENT_SOURCE_DIRECTORY_NAME",
    "ALL_TOOLS_SENTINEL",
    "CODEX_AGENT_ENV_VAR",
    "CODEX_AGENT_ENV_SEPARATOR",
    "DEFAULT_SOURCE_ROOT",
    "DEFAULT_TARGET_ROOT",
    "EFFORT_MAPPINGS",
    "GENERATED_MANIFEST_FILENAME",
    "INHERIT_MODEL_VALUE",
    "MODEL_MAPPINGS",
    "MODEL_PREFIX_EXAMPLE_SUFFIX",
    "PERMISSION_MODE_MAPPINGS",
    "READ_ONLY_SANDBOX_MODE",
    "READ_ONLY_TOOLS",
    "SCRIPT_CAPABLE_TOOLS",
    "WEB_CAPABLE_TOOLS",
    "WEB_SEARCH_DISABLED",
    "WRITE_CAPABLE_TOOLS",
    "AgentConversionError",
    "CodexAgent",
    "SourceAgent",
    "TomlArrayTable",
    "agent_environment_marker",
    "convert_agent",
    "convert_agents",
    "generated_agent_type",
    "infer_sandbox_mode",
    "install_agents",
    "iter_agent_files",
    "main",
    "map_effort",
    "map_model",
    "map_permission_mode",
    "map_web_search",
    "parse_agent_markdown",
    "render_agent_toml",
]


if __name__ == "__main__":
    raise SystemExit(main())
