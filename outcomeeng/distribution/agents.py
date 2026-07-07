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
        "effort",
        "permissionMode",
        "skills",
        "tools",
        "disallowedTools",
    }
)
GENERATED_MANIFEST_FILENAME: Final = ".outcomeeng-generated-agents.json"
DEFAULT_SOURCE_ROOT: Final = Path("dist") / "codex"
DEFAULT_TARGET_ROOT: Final = Path.home() / ".codex" / "agents"
MODEL_MAPPINGS: Final = (
    ("claude-opus", "gpt-5.4"),
    ("opus", "gpt-5.4"),
    ("claude-sonnet", "gpt-5.4"),
    ("sonnet", "gpt-5.4"),
    ("claude-haiku", "gpt-5.4-mini"),
    ("haiku", "gpt-5.4-mini"),
)
EFFORT_MAPPINGS: Final = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "max": "xhigh",
}
PERMISSION_MODE_MAPPINGS: Final = {
    "acceptEdits": "workspace-write",
    "readOnly": "read-only",
}
INHERIT_MODEL_VALUE: Final = "inherit"
MODEL_PREFIX_EXAMPLE_SUFFIX: Final = "-example"
UNMAPPED_PERMISSION_MODE_EXAMPLE: Final = "bypassPermissions"
ALL_TOOLS_SENTINEL: Final = "all"
CODEX_AGENT_ENV_VAR: Final = "OUTCOMEENG_CODEX_AGENT_NAME"
CODEX_AGENT_ENV_SEPARATOR: Final = "/"
READ_ONLY_SANDBOX_MODE: Final = "read-only"
WEB_SEARCH_DISABLED: Final = "disabled"
READ_ONLY_TOOLS: Final = frozenset({"Glob", "Grep", "Read"})
SCRIPT_CAPABLE_TOOLS: Final = frozenset({"Bash", "Skill"})
WEB_CAPABLE_TOOLS: Final = frozenset({"WebFetch", "WebSearch"})
WRITE_CAPABLE_TOOLS: Final = frozenset({"Edit", "NotebookEdit", "Write"})


class AgentConversionError(Exception):
    """Agent conversion or installation failed."""


@dataclass(frozen=True)
class ClaudeAgent:
    """Parsed Claude agent markdown."""

    source_path: Path
    name: str
    description: str
    body: str
    model: str | None = None
    effort: str | None = None
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


def iter_agent_files(source_root: Path) -> tuple[Path, ...]:
    """Return rendered agent markdown files under ``source_root``."""
    if not source_root.is_dir():
        return ()
    return tuple(sorted(source_root.glob("*/agents/*.md")))


def parse_agent_markdown(path: Path) -> ClaudeAgent:
    """Parse one Claude agent markdown file."""
    frontmatter, body = _split_frontmatter(path.read_text(encoding="utf-8"))
    name = _optional_string(frontmatter, "name") or path.stem
    description = _optional_string(frontmatter, "description") or (
        f"Converted Claude agent from {path.name}."
    )
    unsupported_fields = tuple(
        sorted(key for key in frontmatter if key not in SUPPORTED_FRONTMATTER_FIELDS)
    )
    return ClaudeAgent(
        source_path=path,
        name=name,
        description=description,
        body=body,
        model=_optional_string(frontmatter, "model"),
        effort=_optional_string(frontmatter, "effort"),
        permission_mode=_optional_string(frontmatter, "permissionMode"),
        skills=_string_tuple(frontmatter, "skills"),
        tools=_string_tuple(frontmatter, "tools"),
        tools_declared="tools" in frontmatter,
        disallowed_tools=_string_tuple(frontmatter, "disallowedTools"),
        unsupported_fields=unsupported_fields,
    )


def convert_agent(agent: ClaudeAgent) -> CodexAgent:
    """Convert one Claude agent into a Codex custom-agent representation."""
    values: dict[str, object] = {
        "name": agent.name,
        "description": agent.description,
    }
    model = map_model(agent.model)
    if model is not None:
        values["model"] = model
    effort = map_effort(agent.effort)
    if effort is not None:
        values["model_reasoning_effort"] = effort
    sandbox_mode = map_permission_mode(agent.permission_mode)
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
    values["shell_environment_policy"] = {
        "set": {
            CODEX_AGENT_ENV_VAR: agent_environment_marker(agent),
        },
    }
    values["developer_instructions"] = TomlMultilineString(
        render_developer_instructions(agent)
    )
    return CodexAgent(filename=f"{_slugify(agent.name)}.toml", values=values)


def map_model(model: str | None) -> str | None:
    """Map Claude model names to Codex model slugs."""
    if model is None or model == INHERIT_MODEL_VALUE:
        return None
    for source_prefix, target_model in MODEL_MAPPINGS:
        if model == source_prefix or model.startswith(source_prefix):
            return target_model
    return model


def agent_environment_marker(agent: ClaudeAgent) -> str:
    """Return the stable Codex policy marker for a converted agent."""
    plugin_name = _source_plugin_name(agent.source_path)
    if plugin_name is None:
        return agent.name
    return f"{plugin_name}{CODEX_AGENT_ENV_SEPARATOR}{agent.name}"


def map_effort(effort: str | None) -> str | None:
    """Map Claude effort values to Codex reasoning effort values."""
    if effort is None:
        return None
    return EFFORT_MAPPINGS.get(effort, effort)


def map_permission_mode(permission_mode: str | None) -> str | None:
    """Map supported Claude permission modes to Codex sandbox modes."""
    if permission_mode is None:
        return None
    return PERMISSION_MODE_MAPPINGS.get(permission_mode)


def map_web_search(
    tools: Sequence[str],
    *,
    tools_declared: bool = True,
) -> str | None:
    """Return the Codex web-search mode implied by an explicit Claude tool allowlist."""
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
    """Infer a Codex sandbox from an explicit Claude tool allowlist."""
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


def render_developer_instructions(agent: ClaudeAgent) -> str:
    """Render the Codex developer-instruction body."""
    sections = [agent.body.strip()]
    guidance: list[str] = []

    if agent.skills:
        guidance.append(
            "Claude `skills` preload semantics were preserved as prompt guidance. "
            "Invoke these skills before relying on this agent's specialized "
            f"behavior: {', '.join(f'`{skill}`' for skill in agent.skills)}."
        )

    if agent.tools:
        guidance.append(
            "Claude `tools` allowlists can map only to Codex configuration "
            "boundaries with matching semantics. Treat command-level meanings "
            "inside allowed shell tools as manual-review guidance: "
            f"{', '.join(f'`{tool}`' for tool in agent.tools)}."
        )

    if agent.disallowed_tools:
        guidance.append(
            "Claude `disallowedTools` deny lists do not enforce Codex permissions. "
            "Treat these tools as manual-review guidance unless runtime policy "
            "enforces them: "
            f"{', '.join(f'`{tool}`' for tool in agent.disallowed_tools)}."
        )

    if agent.permission_mode and map_permission_mode(agent.permission_mode) is None:
        guidance.append(
            f"Claude `permissionMode: {agent.permission_mode}` has no direct "
            "Codex mapping. Choose the appropriate sandbox, permissions, MCP "
            "tool filters, or app tool filters before relying on this agent for "
            "write or network behavior."
        )

    if agent.unsupported_fields:
        guidance.append(
            "Review unsupported Claude agent fields manually: "
            f"{', '.join(f'`{field}`' for field in agent.unsupported_fields)}."
        )

    if guidance:
        sections.append("## Manual Review Guidance\n\n" + "\n\n".join(guidance))
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
                f"multiple Claude agents convert to {converted_agent.filename}"
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
        description="Convert rendered Claude agents into Codex custom-agent TOML.",
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
            existing = values.setdefault(current_key, [])
            if not isinstance(existing, list):
                existing = [existing]
                values[current_key] = existing
            existing.append(_parse_yaml_scalar(raw_line[4:].strip()))
            index += 1
            continue
        key, separator, value = raw_line.partition(":")
        if not separator:
            index += 1
            continue
        current_key = key.strip()
        value = value.strip()
        if _is_yaml_block_scalar(value):
            block_lines, index = _collect_yaml_block(lines, index + 1)
            values[current_key] = _parse_yaml_block_scalar(value, block_lines)
            continue
        values[current_key] = _parse_yaml_scalar(value) if value else []
        index += 1
    return values


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
    if value.startswith("[") and value.endswith("]"):
        return [
            _parse_yaml_scalar(part)
            for part in _split_delimited(value[1:-1])
            if part.strip()
        ]
    if value.startswith(("'", '"')) and value.endswith(value[0]):
        return value[1:-1]
    return value


def _split_delimited(text: str) -> tuple[str, ...]:
    values: list[str] = []
    token: list[str] = []
    quote: str | None = None
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
        if char == ",":
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


def _slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-").lower() or "agent"


def _source_plugin_name(path: Path) -> str | None:
    if path.parent.name != "agents":
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
        if lines:
            lines.append("")
        lines.append(f"[{_format_toml_key(key)}]")
        for table_key, table_value in table.items():
            lines.append(
                f"{_format_toml_key(str(table_key))} = {_format_toml_value(table_value)}"
            )
    return "\n".join(lines) + "\n"


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
    "UNMAPPED_PERMISSION_MODE_EXAMPLE",
    "WEB_CAPABLE_TOOLS",
    "WEB_SEARCH_DISABLED",
    "WRITE_CAPABLE_TOOLS",
    "AgentConversionError",
    "ClaudeAgent",
    "CodexAgent",
    "agent_environment_marker",
    "convert_agent",
    "convert_agents",
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
