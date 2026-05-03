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

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

# Implementation status flag. Tests gate on this via:
#
#     from outcomeeng.scripts.build_plugins import IMPLEMENTED
#     import pytest
#     if not IMPLEMENTED:
#         pytest.skip(
#             "outcomeeng.scripts.build_plugins is a stub",
#             allow_module_level=True,
#         )
#
# Flip to True only when every stage function below is implemented and the
# build's end-to-end tests pass.
IMPLEMENTED: Final = False


# ---------------------------------------------------------------------------
# Source tree layout
# ---------------------------------------------------------------------------

PLUGINS_DIR_NAME: Final = "plugins"
SHARED_DIR_NAME: Final = "_shared"
SHARED_FRAGMENT_FILENAME: Final = "fragment.md"
SKILLS_SUBDIR_NAME: Final = "skills"
COMMANDS_SUBDIR_NAME: Final = "commands"
AGENTS_SUBDIR_NAME: Final = "agents"
REFERENCES_SUBDIR_NAME: Final = "references"
PLUGIN_SUBDIRS: Final = frozenset(
    {SKILLS_SUBDIR_NAME, COMMANDS_SUBDIR_NAME, AGENTS_SUBDIR_NAME}
)

SKILL_FILENAME: Final = "SKILL.md"
COMMAND_FILE_SUFFIX: Final = ".md"
AGENT_FILE_SUFFIX: Final = ".md"


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
    raise NotImplementedError


def format_directive(directive: Directive) -> str:
    """Format a directive back to its source text representation.

    Round-trip property: ``parse_directives(format_directive(d))[0] == d``
    for every Directive d.
    """
    raise NotImplementedError


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
    raise NotImplementedError


def expand_require_skill(directive: RequireSkillDirective) -> str:
    """Return the agent-runtime-neutral invocation text for the named skill.

    Output is identical for both Claude Code and Codex targets — the text
    instructs the agent to invoke the named skill before proceeding.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Stage 3: Template rendering
# ---------------------------------------------------------------------------


def render_text(
    template: str,
    *,
    shared_root: Path | None = None,
) -> str:
    """Render a template by parsing and recursively expanding directives.

    Pass shared_root when the template contains include directives.
    Standard Jinja2 syntax in the template (``{% %}``, ``{{ }}``) is
    preserved verbatim — only the custom-delimiter directives are expanded.

    Raises CyclicIncludeError if include directives form a cycle.
    """
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


def build(src_root: Path, dist_root: Path) -> None:
    """End-to-end build: src/ -> dist/claude/ and dist/codex/.

    Validates src_root's tree shape, then iterates every plugin source file
    and emits both target outputs. The build is deterministic and
    idempotent — the same src_root always produces byte-identical outputs,
    and re-running the build over a previously-emitted dist_root produces
    no changes.

    Raises SourceFormatError if src_root's tree shape is invalid.
    """
    raise NotImplementedError
