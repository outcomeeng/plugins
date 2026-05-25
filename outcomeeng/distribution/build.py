"""Plugin build pipeline.

Transforms src/ plugin source into committed runtime trees at dist/claude/
and dist/codex/. The pipeline is decomposed into stages so each stage is
independently testable. See spec at:

  spx/18-plugin-build.enabler/plugin-build.md
  spx/18-plugin-build.enabler/15-build-architecture.adr.md

This module owns every constant, type, and error class the build emits or
recognizes. Tests import from here directly — there are no test-owned
duplicates of build contracts.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError

# Implementation status flag. Tests gate on this via:
#
#     from outcomeeng.distribution.build import IMPLEMENTED
#     import pytest
#     if not IMPLEMENTED:
#         pytest.skip(
#             "outcomeeng.distribution.build is a stub",
#             allow_module_level=True,
#         )
#
# Flip to True only when every stage function below is implemented and the
# build's end-to-end tests pass.
IMPLEMENTED: Final = True


# ---------------------------------------------------------------------------
# Source tree layout
# ---------------------------------------------------------------------------

PLUGINS_DIR_NAME: Final = "plugins"
SHARED_DIR_NAME: Final = "_shared"
SHARED_FRAGMENT_FILENAME: Final = "fragment.md"
SKILLS_SUBDIR_NAME: Final = "skills"
COMMANDS_SUBDIR_NAME: Final = "commands"
AGENTS_SUBDIR_NAME: Final = "agents"
BIN_SUBDIR_NAME: Final = "bin"
HOOKS_SUBDIR_NAME: Final = "hooks"
CLAUDE_PLUGIN_SUBDIR_NAME: Final = ".claude-plugin"
CODEX_PLUGIN_SUBDIR_NAME: Final = ".codex-plugin"
REFERENCES_SUBDIR_NAME: Final = "references"
PLUGIN_SUBDIRS: Final = frozenset(
    {
        SKILLS_SUBDIR_NAME,
        COMMANDS_SUBDIR_NAME,
        AGENTS_SUBDIR_NAME,
        BIN_SUBDIR_NAME,
        HOOKS_SUBDIR_NAME,
        CLAUDE_PLUGIN_SUBDIR_NAME,
        CODEX_PLUGIN_SUBDIR_NAME,
    }
)

SKILL_FILENAME: Final = "SKILL.md"
COMMAND_FILE_SUFFIX: Final = ".md"
AGENT_FILE_SUFFIX: Final = ".md"
TEXT_FILE_SUFFIXES: Final = frozenset(
    {".md", ".py", ".sh", ".json", ".toml", ".yml", ".yaml"}
)


# ---------------------------------------------------------------------------
# Output tree layout
# ---------------------------------------------------------------------------

DIST_DIR_NAME: Final = "dist"


# ---------------------------------------------------------------------------
# Template delimiters (custom Jinja2)
# ---------------------------------------------------------------------------

BLOCK_DELIMITER_START: Final = "{!%"
BLOCK_DELIMITER_END: Final = "%!}"
VARIABLE_DELIMITER_START: Final = "{{!"
VARIABLE_DELIMITER_END: Final = "!}}"
COMMENT_DELIMITER_START: Final = "{!#"
COMMENT_DELIMITER_END: Final = "#!}"


# ---------------------------------------------------------------------------
# Per-target translation contract
# ---------------------------------------------------------------------------

# Frontmatter fields that appear in dist/claude/ and are stripped from dist/codex/.
# See ADR section "Per-target translation".
CLAUDE_ONLY_FRONTMATTER_FIELDS: Final = (
    "allowed-tools",
    "disable-model-invocation",
    "argument-hint",
)

# The literal token Claude Code expands at runtime. Source files contain this
# token verbatim; the build preserves it in dist/claude/ outputs and rewrites
# any occurrence to a relative path in dist/codex/ outputs.
CLAUDE_SKILL_DIR_TOKEN: Final = "${CLAUDE_SKILL_DIR}"

REQUIRE_SKILL_TEXT_TEMPLATE: Final = (
    "Invoke the `{skill_ref}` skill before proceeding. If that skill is "
    "unavailable, report the missing skill and continue with the closest "
    "available workflow."
)

_DIRECTIVE_RE: Final = re.compile(
    re.escape(BLOCK_DELIMITER_START) + r"\s*(.*?)\s*" + re.escape(BLOCK_DELIMITER_END),
    re.DOTALL,
)
_DIRECTIVE_BODY_RE: Final = re.compile(
    r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+"
    r"(?P<quote>['\"])(?P<argument>.*?)(?P=quote)$",
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class Target(StrEnum):
    """Output runtime target."""

    CLAUDE = "claude"
    CODEX = "codex"


@dataclass(frozen=True)
class IncludeDirective:
    """Source representation: ``{!% include 'path/to/file.md' %!}``.

    The path is interpreted relative to the build's shared_root.
    """

    path: str


@dataclass(frozen=True)
class RequireSkillDirective:
    """Source representation: ``{!% require_skill 'plugin:skill-name' %!}``.

    Expands to identical agent-runtime-neutral invocation text in both
    targets. Replaces the runtime ``!` `cat`` injection that has no Codex
    equivalent.
    """

    skill_ref: str


Directive = IncludeDirective | RequireSkillDirective


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class BuildError(Exception):
    """Base error for build failures."""


class DirectiveSyntaxError(BuildError):
    """A template directive could not be parsed."""


class IncludeResolutionError(BuildError):
    """An include directive references a file that does not exist."""


class CyclicIncludeError(BuildError):
    """An include directive forms a cycle of include references."""


class SourceFormatError(BuildError):
    """The src/ tree does not conform to the documented layout."""


class FrontmatterError(BuildError):
    """A source file's frontmatter is malformed."""


class TemplateRenderError(BuildError):
    """A template could not be rendered."""


# ---------------------------------------------------------------------------
# Stage 1: Directive parsing
# ---------------------------------------------------------------------------


def parse_directives(text: str) -> tuple[Directive, ...]:
    """Find all template directives in text, in source order.

    Standard Jinja2 delimiters (``{% %}`` and ``{{ }}``) are not recognized
    as directives — only the custom delimiter set defined above. Content
    that uses standard delimiters passes through render_text unchanged.

    Raises DirectiveSyntaxError if a directive uses recognized delimiters
    but cannot be parsed (e.g., unknown directive name, malformed argument).
    """
    directives: list[Directive] = []
    for match in _DIRECTIVE_RE.finditer(text):
        body = " ".join(match.group(1).split())
        body_match = _DIRECTIVE_BODY_RE.match(body)
        if body_match is None:
            raise DirectiveSyntaxError(f"invalid directive: {match.group(0)!r}")
        name = body_match.group("name")
        argument = body_match.group("argument")
        if name == "include":
            directives.append(IncludeDirective(path=argument))
        elif name == "require_skill":
            directives.append(RequireSkillDirective(skill_ref=argument))
        else:
            raise DirectiveSyntaxError(f"unknown directive {name!r}")
    return tuple(directives)


def format_directive(directive: Directive) -> str:
    """Format a directive back to its source text representation.

    Round-trip property: ``parse_directives(format_directive(d))[0] == d``
    for every Directive d.
    """
    if isinstance(directive, IncludeDirective):
        return (
            f"{BLOCK_DELIMITER_START} include '{directive.path}' {BLOCK_DELIMITER_END}"
        )
    if isinstance(directive, RequireSkillDirective):
        return (
            f"{BLOCK_DELIMITER_START} require_skill '{directive.skill_ref}' "
            f"{BLOCK_DELIMITER_END}"
        )
    raise DirectiveSyntaxError(f"unsupported directive: {directive!r}")


# ---------------------------------------------------------------------------
# Stage 2: Directive expansion
# ---------------------------------------------------------------------------


def expand_include(
    directive: IncludeDirective,
    *,
    shared_root: Path,
) -> str:
    """Read and return the body of the included file.

    The directive's path is resolved as ``shared_root / directive.path``.
    The returned string is the file's body verbatim — no rendering, no
    transformation.

    Raises IncludeResolutionError if the file does not exist.
    """
    include_path = _resolve_under_root(shared_root, directive.path)
    if not include_path.is_file():
        raise IncludeResolutionError(
            f"include {directive.path!r} does not resolve under {shared_root}"
        )
    return include_path.read_text(encoding="utf-8")


def expand_require_skill(directive: RequireSkillDirective) -> str:
    """Return the agent-runtime-neutral invocation text for the named skill.

    Output is identical for both Claude Code and Codex targets — the text
    instructs the agent to invoke the named skill before proceeding.
    """
    return REQUIRE_SKILL_TEXT_TEMPLATE.format(skill_ref=directive.skill_ref)


# ---------------------------------------------------------------------------
# Stage 3: Template rendering
# ---------------------------------------------------------------------------


def render_text(
    template: str,
    *,
    shared_root: Path | None = None,
    variables: dict[str, object] | None = None,
) -> str:
    """Render a template by parsing and recursively expanding directives.

    Pass shared_root when the template contains include directives.
    Standard Jinja2 syntax in the template (``{% %}``, ``{{ }}``) is
    preserved verbatim — only the custom-delimiter directives are expanded.

    Raises CyclicIncludeError if include directives form a cycle.
    """
    rendered = _render_directives(
        template,
        shared_root=shared_root,
        include_stack=(),
    )
    if VARIABLE_DELIMITER_START not in rendered:
        return rendered
    try:
        environment = make_jinja_environment(shared_root)
        return environment.from_string(rendered).render(variables or {})
    except TemplateError as exc:
        raise TemplateRenderError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Stage 4: Per-target translation
# ---------------------------------------------------------------------------


def rewrite_paths_for_target(text: str, *, target: Target) -> str:
    """Apply target-specific path rewriting.

    For Target.CLAUDE: identity (CLAUDE_SKILL_DIR_TOKEN preserved verbatim).
    For Target.CODEX: every occurrence of CLAUDE_SKILL_DIR_TOKEN/<rest> is
    rewritten to a relative path under the consuming skill directory.

    Idempotence: ``rewrite_paths_for_target(rewrite_paths_for_target(t, target=T), target=T) == rewrite_paths_for_target(t, target=T)``.
    """
    if target is Target.CLAUDE:
        return text

    without_slash = text.replace(f"{CLAUDE_SKILL_DIR_TOKEN}/", "")
    return without_slash.replace(CLAUDE_SKILL_DIR_TOKEN, ".")


def strip_frontmatter_fields(
    text: str,
    *,
    fields: tuple[str, ...],
) -> str:
    """Remove named YAML frontmatter fields from text, preserving other frontmatter.

    Idempotence: ``strip_frontmatter_fields(strip_frontmatter_fields(t, fields=F), fields=F) == strip_frontmatter_fields(t, fields=F)``.

    Raises FrontmatterError if the text claims to have frontmatter but it
    does not parse as YAML.
    """
    if not text.startswith("---\n"):
        return text

    closing_index = text.find("\n---", len("---\n"))
    if closing_index == -1:
        raise FrontmatterError("frontmatter starts with --- but has no closing fence")

    fence_end = closing_index + len("\n---")
    if len(text) > fence_end and text[fence_end] not in {"\n", "\r"}:
        raise FrontmatterError("frontmatter closing fence is malformed")

    raw_frontmatter = text[len("---\n") : closing_index]
    suffix = text[fence_end:]
    field_set = frozenset(fields)
    kept_lines: list[str] = []
    lines = raw_frontmatter.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        key = _frontmatter_key(line)
        if key in field_set:
            index += 1
            while index < len(lines) and _is_continuation_line(lines[index]):
                index += 1
            continue
        kept_lines.append(line)
        index += 1

    if kept_lines:
        return "---\n" + "\n".join(kept_lines) + "\n---" + suffix
    return suffix.lstrip("\r\n")


# ---------------------------------------------------------------------------
# Stage 5: Build orchestration
# ---------------------------------------------------------------------------


def emit_skill(
    src_path: Path,
    *,
    target: Target,
    dist_root: Path,
    shared_root: Path,
) -> None:
    """Emit one skill's outputs for one target.

    Reads src_path (a SKILL.md), renders directives via shared_root, applies
    target-specific translation, and writes the result to the corresponding
    location under dist_root.
    """
    src_relative = _relative_plugin_path(src_path)
    destination = dist_root / target.value / src_relative
    rendered = render_text(
        src_path.read_text(encoding="utf-8"),
        shared_root=shared_root,
        variables={"target": target.value},
    )
    translated = rewrite_paths_for_target(rendered, target=target)
    if target is Target.CODEX:
        translated = strip_frontmatter_fields(
            translated,
            fields=CLAUDE_ONLY_FRONTMATTER_FIELDS,
        )
    _write_text(destination, translated)
    shutil.copymode(src_path, destination)
    _fan_out_shared_references(
        src_path,
        destination,
        shared_root=shared_root,
        rendered_source=src_path.read_text(encoding="utf-8"),
    )


def build(src_root: Path, dist_root: Path) -> None:
    """End-to-end build: src/ -> dist/claude/ and dist/codex/.

    Validates src_root's tree shape, then iterates every plugin source file
    and emits both target outputs. The build is deterministic and
    idempotent — the same src_root always produces byte-identical outputs,
    and re-running the build over a previously-emitted dist_root produces
    no changes.

    Raises SourceFormatError if src_root's tree shape is invalid.
    """
    _validate_source_tree(src_root)
    shared_root = src_root / SHARED_DIR_NAME
    plugins_root = src_root / PLUGINS_DIR_NAME

    for target in Target:
        runtime_root = dist_root / target.value
        if runtime_root.exists():
            shutil.rmtree(runtime_root)
        runtime_root.mkdir(parents=True, exist_ok=True)

    for source_file in _iter_plugin_files(plugins_root):
        for target in Target:
            if _is_rendered_text(source_file):
                if (
                    SKILLS_SUBDIR_NAME in source_file.parts
                    and source_file.name == SKILL_FILENAME
                ):
                    emit_skill(
                        source_file,
                        target=target,
                        dist_root=dist_root,
                        shared_root=shared_root,
                    )
                    continue
                _emit_rendered_file(
                    source_file,
                    target=target,
                    dist_root=dist_root,
                    shared_root=shared_root,
                )
                continue
            _copy_unrendered_file(source_file, target=target, dist_root=dist_root)

    _format_dist(dist_root)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the build recipe."""
    parser = argparse.ArgumentParser(
        prog="outcomeeng.distribution.build",
        description="Build src/ plugin sources into dist/claude and dist/codex.",
    )
    parser.add_argument("src_root", type=Path, nargs="?", default=Path("src"))
    parser.add_argument("dist_root", type=Path, nargs="?", default=Path("dist"))
    args = parser.parse_args(argv)
    try:
        build(args.src_root, args.dist_root)
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def make_jinja_environment(shared_root: Path | None = None) -> Environment:
    """Return the build's configured Jinja2 environment."""
    loader = FileSystemLoader(str(shared_root)) if shared_root is not None else None
    return Environment(
        loader=loader,
        block_start_string=BLOCK_DELIMITER_START,
        block_end_string=BLOCK_DELIMITER_END,
        variable_start_string=VARIABLE_DELIMITER_START,
        variable_end_string=VARIABLE_DELIMITER_END,
        comment_start_string=COMMENT_DELIMITER_START,
        comment_end_string=COMMENT_DELIMITER_END,
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )


def _render_directives(
    template: str,
    *,
    shared_root: Path | None,
    include_stack: tuple[Path, ...],
) -> str:
    parse_directives(template)

    def replace(match: re.Match[str]) -> str:
        body = " ".join(match.group(1).split())
        body_match = _DIRECTIVE_BODY_RE.match(body)
        if body_match is None:
            raise DirectiveSyntaxError(f"invalid directive: {match.group(0)!r}")
        name = body_match.group("name")
        argument = body_match.group("argument")
        if name == "require_skill":
            return expand_require_skill(RequireSkillDirective(skill_ref=argument))
        if name != "include":
            raise DirectiveSyntaxError(f"unknown directive {name!r}")
        if shared_root is None:
            raise IncludeResolutionError("include directive requires shared_root")
        include_path = _resolve_under_root(shared_root, argument)
        if include_path in include_stack:
            cycle = " -> ".join(str(path) for path in (*include_stack, include_path))
            raise CyclicIncludeError(f"cyclic include detected: {cycle}")
        included = expand_include(
            IncludeDirective(path=argument), shared_root=shared_root
        )
        return _render_directives(
            included,
            shared_root=shared_root,
            include_stack=(*include_stack, include_path),
        )

    return _DIRECTIVE_RE.sub(replace, template)


def _resolve_under_root(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise IncludeResolutionError(
            f"path {relative_path!r} escapes shared root {root}"
        ) from exc
    return candidate


def _frontmatter_key(line: str) -> str | None:
    if not line or line[0].isspace() or ":" not in line:
        return None
    key, _, _ = line.partition(":")
    return key.strip()


def _is_continuation_line(line: str) -> bool:
    return bool(line.startswith((" ", "\t")) or not line.strip())


def _relative_plugin_path(path: Path) -> Path:
    parts = path.parts
    try:
        plugins_index = parts.index(PLUGINS_DIR_NAME)
    except ValueError as exc:
        raise SourceFormatError(
            f"{path} is not under a {PLUGINS_DIR_NAME}/ directory"
        ) from exc
    return Path(*parts[plugins_index + 1 :])


def _is_rendered_text(path: Path) -> bool:
    return path.suffix in TEXT_FILE_SUFFIXES


def _emit_rendered_file(
    source_file: Path,
    *,
    target: Target,
    dist_root: Path,
    shared_root: Path,
) -> None:
    destination = dist_root / target.value / _relative_plugin_path(source_file)
    rendered = render_text(
        source_file.read_text(encoding="utf-8"),
        shared_root=shared_root,
        variables={"target": target.value},
    )
    translated = rewrite_paths_for_target(rendered, target=target)
    _write_text(destination, translated)
    shutil.copymode(source_file, destination)
    _fan_out_shared_references(
        source_file,
        destination,
        shared_root=shared_root,
        rendered_source=source_file.read_text(encoding="utf-8"),
    )


def _copy_unrendered_file(
    source_file: Path, *, target: Target, dist_root: Path
) -> None:
    destination = dist_root / target.value / _relative_plugin_path(source_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, destination)


def _format_dist(dist_root: Path) -> None:
    formatter = shutil.which("dprint")
    if formatter is None:
        raise BuildError("dprint is required to format generated dist output")
    file_pattern = str(dist_root / "**" / "*.{md,json,toml,py,yaml,yml,js,html}")
    result = subprocess.run(
        (formatter, "fmt", "--allow-no-files", file_pattern),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise BuildError(f"dprint failed while formatting dist: {details}")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _iter_plugin_files(plugins_root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in plugins_root.rglob("*") if path.is_file()))


def _validate_source_tree(src_root: Path) -> None:
    plugins_root = src_root / PLUGINS_DIR_NAME
    if not plugins_root.is_dir():
        raise SourceFormatError(f"missing source plugins directory: {plugins_root}")

    shared_root = src_root / SHARED_DIR_NAME
    if shared_root.exists():
        for topic_root in sorted(
            path for path in shared_root.glob("*/*") if path.is_dir()
        ):
            fragment = topic_root / SHARED_FRAGMENT_FILENAME
            if not fragment.is_file():
                raise SourceFormatError(
                    f"shared topic missing fragment.md: {topic_root}"
                )

    for plugin_root in sorted(path for path in plugins_root.iterdir() if path.is_dir()):
        for child in sorted(plugin_root.iterdir()):
            if child.name not in PLUGIN_SUBDIRS:
                raise SourceFormatError(
                    f"unexpected plugin subdirectory {child.relative_to(src_root)}"
                )
        skills_root = plugin_root / SKILLS_SUBDIR_NAME
        if skills_root.exists():
            for skill_root in sorted(
                path for path in skills_root.iterdir() if path.is_dir()
            ):
                if not (skill_root / SKILL_FILENAME).is_file():
                    raise SourceFormatError(
                        f"skill directory missing {SKILL_FILENAME}: "
                        f"{skill_root.relative_to(src_root)}"
                    )


def _fan_out_shared_references(
    source_file: Path,
    destination: Path,
    *,
    shared_root: Path,
    rendered_source: str,
) -> None:
    if SKILLS_SUBDIR_NAME not in source_file.parts:
        return
    for directive in parse_directives(rendered_source):
        if not isinstance(directive, IncludeDirective):
            continue
        include_path = _resolve_under_root(shared_root, directive.path)
        topic_root = include_path.parent
        for child in sorted(topic_root.iterdir()):
            if child.name == SHARED_FRAGMENT_FILENAME:
                continue
            if child.is_dir():
                target_child = destination.parent / child.name
                if target_child.exists():
                    shutil.rmtree(target_child)
                shutil.copytree(child, target_child)
            elif child.is_file():
                shutil.copy2(child, destination.parent / child.name)


if __name__ == "__main__":
    raise SystemExit(main())
