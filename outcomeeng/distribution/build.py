"""Plugin build pipeline.

Transforms src/ plugin source into committed target trees at dist/claude/
and dist/codex/. The pipeline is decomposed into stages so each stage is
independently testable.

This module owns build behavior and consumes distribution contracts from
``outcomeeng.distribution.contracts``. Tests import source-owned contracts
directly instead of keeping test-owned duplicates.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from ast import literal_eval
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    pass_context,
)
from jinja2.runtime import Context

from outcomeeng.distribution.agents import (
    CODEX_FAST_MODEL,
    convert_agent_markdown,
    CODEX_STANDARD_MODEL,
    CODEX_STRONG_MODEL,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    BUILD_BLOCK_DELIMITER_END,
    BUILD_BLOCK_DELIMITER_START,
    BUILD_COMMENT_DELIMITER_END,
    BUILD_COMMENT_DELIMITER_START,
    BUILD_TARGET_VARIABLE,
    BUILD_VARIABLE_DELIMITER_END,
    BUILD_VARIABLE_DELIMITER_START,
    PLUGIN_NAME_VARIABLE,
    PLUGINS_DIR_NAME,
    PLUGIN_SUBDIRS,
    REFERENCES_SUBDIR_NAME,
    REQUIRE_SKILL_GUIDANCE_TEMPLATE,
    RUNTIME_TOKEN_ASK_USER_CAPABILITY,
    RUNTIME_TOKEN_ASK_USER_NAMES,
    RUNTIME_TOKEN_CLOSE_AGENT_CAPABILITY,
    RUNTIME_TOKEN_CLOSE_AGENT_NAMES,
    RUNTIME_TOKEN_CONFIGURED_AGENT_AUDITOR_MODEL_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_MODEL_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_OR_STANDARD_MODELS_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_STANDARD_MODEL_CAPABILITY,
    RUNTIME_TOKEN_CONFIGURED_AGENT_STRONG_MODELS_CAPABILITY,
    RUNTIME_TOKEN_FIELD_KIND,
    RUNTIME_TOKEN_FILE_KIND,
    RUNTIME_TOKEN_KIND_GUARD_ENFORCEMENT,
    RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY,
    RUNTIME_TOKEN_ROOT_GUIDE_NAMES,
    RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY,
    RUNTIME_TOKEN_SCHEDULE_WAKEUP_NAMES,
    RUNTIME_TOKEN_SPAWN_AGENT_CAPABILITY,
    RUNTIME_TOKEN_SPAWN_AGENT_NAMES,
    RUNTIME_TOKEN_TERM_KIND,
    RUNTIME_TOKEN_TOOL_KIND,
    RUNTIME_TOKEN_WAIT_AGENT_CAPABILITY,
    RUNTIME_TOKEN_WAIT_AGENT_NAMES,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    SPX_FLOOR_VARIABLE,
    TEXT_FILE_SUFFIXES as _TEXT_FILE_SUFFIXES,
    Target as _Target,
)
from outcomeeng.distribution.diagnose_manifest import (
    diagnose_manifest_render_variables,
)
from outcomeeng.validation.spx_version import REQUIRED_SPX_VERSION

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

SHARED_DIR_NAME: Final = "_shared"
# Per-plugin skill templates. One authored body under `src/templates/<template>/`
# renders once per plugin with that plugin's slug bound, emitting the skill
# directory `<plugin>-<template>` into every plugin's generated tree. Distinct
# from `_shared`, whose fragments are included INTO a skill rather than being a
# whole skill generated from one source.
TEMPLATES_DIR_NAME: Final = "templates"
# The template whose generated skill carries each plugin's own lifecycle surface,
# including the agent definitions a target reads from the checkout rather than
# from a plugin manifest.
LIFECYCLE_TEMPLATE_NAME: Final = "plugin"
PLACEMENT_MANIFEST_FILENAME: Final = "placement.json"
SHARED_FRAGMENT_FILENAME: Final = "fragment.md"


# ---------------------------------------------------------------------------
# Template delimiters (custom Jinja2)
# ---------------------------------------------------------------------------

BLOCK_DELIMITER_START: Final = BUILD_BLOCK_DELIMITER_START
BLOCK_DELIMITER_END: Final = BUILD_BLOCK_DELIMITER_END
VARIABLE_DELIMITER_START: Final = BUILD_VARIABLE_DELIMITER_START
VARIABLE_DELIMITER_END: Final = BUILD_VARIABLE_DELIMITER_END
COMMENT_DELIMITER_START: Final = BUILD_COMMENT_DELIMITER_START
COMMENT_DELIMITER_END: Final = BUILD_COMMENT_DELIMITER_END


# ---------------------------------------------------------------------------
# Per-target translation contract
# ---------------------------------------------------------------------------

# Frontmatter fields that appear in dist/claude/ and are stripped from dist/codex/.
DISABLE_MODEL_INVOCATION_FIELD: Final = "disable-model-invocation"
CLAUDE_ONLY_FRONTMATTER_FIELDS: Final = (DISABLE_MODEL_INVOCATION_FIELD,)

# The literal token Claude Code expands during skill execution. Source files
# contain this token verbatim; the build preserves it in dist/claude/ outputs
# and rewrites any occurrence to Codex's skill-directory token in dist/codex/
# outputs.
CLAUDE_SKILL_DIR_TOKEN: Final = "${CLAUDE_SKILL_DIR}"
CODEX_SKILL_DIR_TOKEN: Final = "${SKILL_DIR}"
SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE: Final = "{!# no-codex-skill-dir-rewrite #!}"
EXECUTION_TIME_INJECTION_START: Final = "!`"
EXECUTION_TIME_INJECTION_END: Final = "`"
EXECUTION_TIME_INJECTION_PATTERN: Final = re.compile(
    rf"(?<!`){re.escape(EXECUTION_TIME_INJECTION_START)}"
    rf"(?P<command>[^`\r\n]*)"
    rf"{re.escape(EXECUTION_TIME_INJECTION_END)}"
)
SKILL_DIR_REFERENCE_SUFFIX_PATTERN: Final = r"/[^\s`\"']+"
SKILL_DIR_REWRITE_PLACEHOLDER: Final = "__OUTCOMEENG_CLAUDE_SKILL_DIR_LITERAL__"
# Protects the escape directive (which shares Jinja's {!# #!} comment syntax) across
# the Jinja render pass so it reaches rewrite_paths_for_target unstripped.
SKILL_DIR_REWRITE_ESCAPE_PLACEHOLDER: Final = "__OUTCOMEENG_SKILL_DIR_REWRITE_ESCAPE__"

FORMATTER_COMMAND_NAME: Final = "dprint"
FORMATTER_VERSION: Final = "0.54.0"  # renovate: datasource=npm depName=dprint
FORMATTER_VERSION_OUTPUT: Final = f"{FORMATTER_COMMAND_NAME} {FORMATTER_VERSION}"
FORMATTER_FILE_GLOB: Final = "**/*.{md,json,toml,py,yaml,yml,js,html}"
FORMATTER_CONFIG_PATH: Final = Path(__file__).resolve().parents[2] / "dprint.jsonc"
IGNORED_SOURCE_DIRECTORY_NAMES: Final = frozenset({"__pycache__"})
IGNORED_SOURCE_FILE_SUFFIXES: Final = (".pyc",)
FormatterProbe = Callable[[str], str | None]
FormatterRunner = Callable[[tuple[str, ...], Path], subprocess.CompletedProcess[str]]


class EmissionAction(StrEnum):
    """How one source file reaches a generated target tree."""

    RENDER = "render"
    COPY = "copy"
    FAN_OUT = "fan-out"
    CONVERT_AGENT = "convert-agent"
    PLACEMENT_MANIFEST = "placement-manifest"


@dataclass(frozen=True)
class PlannedEmission:
    """One source-owned output in one generated target tree."""

    source: Path
    target: _Target
    relative_path: Path
    action: EmissionAction


@dataclass(frozen=True)
class BuildPlan:
    """Complete source and output inventory for one build."""

    plugin_sources: tuple[Path, ...]
    emissions: tuple[PlannedEmission, ...]

    def for_target(self, target: _Target) -> tuple[PlannedEmission, ...]:
        """Return the planned outputs for ``target``."""
        return tuple(
            emission for emission in self.emissions if emission.target is target
        )

    def collisions(self) -> dict[tuple[_Target, Path], tuple[Path, ...]]:
        """Return output coordinates with more than one producing source."""
        producers: dict[tuple[_Target, Path], set[Path]] = {}
        for emission in self.emissions:
            coordinate = (emission.target, emission.relative_path)
            producers.setdefault(coordinate, set()).add(emission.source)
        return {
            coordinate: tuple(sorted(paths))
            for coordinate, paths in producers.items()
            if len(paths) > 1
        }


@dataclass(frozen=True)
class RuntimeTokenKind:
    """One category of runtime-divergent name the build renders via a template global.

    ``names`` maps a capability to its per-runtime names (capability -> runtime ->
    name). ``lint_enforced`` marks whether the runtime-token validation gate forbids
    a raw appearance of these names in authored source: the unique-token kinds
    (``tool``, ``field``, ``file``) are enforced, while the common-word concept-term
    kind (``term``) is not — a whole-token match on a word like "agent" would flag
    every prose mention, so terms are covered by review instead. A new kind opts into
    or out of guard enforcement explicitly through this flag.
    """

    lint_enforced: bool
    names: dict[str, dict[str, str]]


@dataclass(frozen=True)
class RuntimeTokenResolverCase:
    """A source-owned registry coordinate the resolver must render."""

    kind: str
    capability: str
    runtime: str


CONFIGURED_AGENT_PROMPT_FIELD_NAMES: Final[dict[str, str]] = {
    "claude": "system prompt",
    "codex": "developer_instructions",
}
CONFIGURED_AGENT_TERM_NAMES: Final[dict[str, dict[str, str]]] = {
    RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY: {
        "claude": "subagent",
        "codex": "custom agent",
    },
    "configured_agents": {"claude": "subagents", "codex": "custom agents"},
    "configured_agent_file": {
        "claude": "subagent file",
        "codex": "custom agent file",
    },
    "configured_agent_files": {
        "claude": "subagent files",
        "codex": "custom agent files",
    },
    RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY: {
        "claude": "system prompt",
        "codex": "developer instructions",
    },
    "configured_agent_prompts": {
        "claude": "system prompts",
        "codex": "developer instructions",
    },
    RUNTIME_TOKEN_CONFIGURED_AGENT_STANDARD_MODEL_CAPABILITY: {
        "claude": "sonnet",
        "codex": CODEX_STANDARD_MODEL,
    },
    RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_MODEL_CAPABILITY: {
        "claude": "haiku",
        "codex": CODEX_FAST_MODEL,
    },
    RUNTIME_TOKEN_CONFIGURED_AGENT_AUDITOR_MODEL_CAPABILITY: {
        "claude": "sonnet",
        "codex": CODEX_STANDARD_MODEL,
    },
    RUNTIME_TOKEN_CONFIGURED_AGENT_STRONG_MODELS_CAPABILITY: {
        "claude": "Sonnet",
        "codex": f"{CODEX_STRONG_MODEL} or {CODEX_STANDARD_MODEL}",
    },
    RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_OR_STANDARD_MODELS_CAPABILITY: {
        "claude": "Haiku or Sonnet",
        "codex": f"{CODEX_FAST_MODEL} or {CODEX_STANDARD_MODEL}",
    },
}


# Source-owned registry of runtime-divergent names, keyed by token kind, then by
# capability, then by runtime. Authored source names a capability via a per-kind
# template token (`tool('<capability>')`, `field(...)`, `term(...)`); the build
# renders the current target's name from that kind's sub-registry. A capability
# with no entry for a runtime (e.g. schedule_wakeup on codex) must be wrapped in a
# per-runtime conditional so the token is never evaluated for the missing runtime.
# The `tool` kind is seeded from the Agent Harness Guidance table in AGENTS.md; the
# `file` kind holds per-runtime filenames — the root agent guide a consumer reads
# is `CLAUDE.md` under Claude Code and `AGENTS.md` under Codex. `field` and `term`
# carry the rendering mechanism ahead of their first authored consumers. Enforcement
# that a raw name never appears in authored source is the runtime-token validation
# lint (outcomeeng.validation.runtime_tokens), which derives its forbidden set from
# the lint-enforced kinds only — not this module.
RUNTIME_TOKEN_REGISTRY: Final[dict[str, RuntimeTokenKind]] = {
    RUNTIME_TOKEN_TOOL_KIND: RuntimeTokenKind(
        lint_enforced=RUNTIME_TOKEN_KIND_GUARD_ENFORCEMENT[RUNTIME_TOKEN_TOOL_KIND],
        names={
            RUNTIME_TOKEN_ASK_USER_CAPABILITY: RUNTIME_TOKEN_ASK_USER_NAMES,
            RUNTIME_TOKEN_SPAWN_AGENT_CAPABILITY: RUNTIME_TOKEN_SPAWN_AGENT_NAMES,
            RUNTIME_TOKEN_WAIT_AGENT_CAPABILITY: RUNTIME_TOKEN_WAIT_AGENT_NAMES,
            RUNTIME_TOKEN_CLOSE_AGENT_CAPABILITY: RUNTIME_TOKEN_CLOSE_AGENT_NAMES,
            RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY: (
                RUNTIME_TOKEN_SCHEDULE_WAKEUP_NAMES
            ),
        },
    ),
    RUNTIME_TOKEN_FIELD_KIND: RuntimeTokenKind(
        lint_enforced=RUNTIME_TOKEN_KIND_GUARD_ENFORCEMENT[RUNTIME_TOKEN_FIELD_KIND],
        names={
            RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY: (
                CONFIGURED_AGENT_PROMPT_FIELD_NAMES
            ),
        },
    ),
    RUNTIME_TOKEN_TERM_KIND: RuntimeTokenKind(
        lint_enforced=RUNTIME_TOKEN_KIND_GUARD_ENFORCEMENT[RUNTIME_TOKEN_TERM_KIND],
        names=CONFIGURED_AGENT_TERM_NAMES,
    ),
    RUNTIME_TOKEN_FILE_KIND: RuntimeTokenKind(
        lint_enforced=RUNTIME_TOKEN_KIND_GUARD_ENFORCEMENT[RUNTIME_TOKEN_FILE_KIND],
        names={
            RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY: RUNTIME_TOKEN_ROOT_GUIDE_NAMES,
        },
    ),
}


def runtime_token_resolver_cases(
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> tuple[RuntimeTokenResolverCase, ...]:
    """Return every registry coordinate the runtime-token resolver must cover."""
    return tuple(
        RuntimeTokenResolverCase(
            kind=kind,
            capability=capability,
            runtime=runtime,
        )
        for kind, kind_entry in registry.items()
        for capability, runtime_names in kind_entry.names.items()
        for runtime in runtime_names
    )


def resolve_runtime_token(
    kind: str,
    capability: str,
    runtime: str,
    *,
    registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> str:
    """Return the runtime-divergent name for ``(kind, capability, runtime)``.

    The kind selects the sub-registry; capability and runtime select the name. The
    ``registry`` seam defaults to the module registry and is injectable so the
    kind-generic resolution is exercised with a controlled registry. Raises
    ``RuntimeTokenError`` when the kind is absent, the capability has no entry in
    that kind, or the kind has no name for the runtime — the caller wraps the
    absent-runtime case in a per-runtime conditional.
    """
    kind_entry = registry.get(kind)
    if kind_entry is None:
        raise RuntimeTokenError(f"unknown runtime-token kind {kind!r}")
    entry = kind_entry.names.get(capability)
    if entry is None:
        raise RuntimeTokenError(f"unknown {kind} capability {capability!r}")
    name = entry.get(runtime)
    if name is None:
        raise RuntimeTokenError(
            f"{kind} capability {capability!r} has no name for runtime {runtime!r}; "
            "wrap the token in a per-runtime conditional"
        )
    return name


_DIRECTIVE_RE: Final = re.compile(
    re.escape(BLOCK_DELIMITER_START) + r"\s*(.*?)\s*" + re.escape(BLOCK_DELIMITER_END),
    re.DOTALL,
)
_DIRECTIVE_BODY_RE: Final = re.compile(
    r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s+"
    r"(?P<argument>.+)$",
    re.DOTALL,
)
_PLANNING_DIRECTIVE_PLACEHOLDER_START: Final = "\ue000outcomeeng-directive:"
_PLANNING_DIRECTIVE_PLACEHOLDER_END: Final = "\ue001"

# Jinja control statements share the `{!% %!}` block delimiter with the build's
# directives. The build owns this vocabulary; validators and evidence import it
# rather than maintaining parallel keyword tables.
JINJA_RAW_BLOCK_NAME: Final = "raw"
JINJA_RAW_BLOCK_END_NAME: Final = "endraw"
JINJA_NEUTRAL_BLOCK_ENDINGS: Final = {
    "block": "endblock",
    "call": "endcall",
    "filter": "endfilter",
    "for": "endfor",
    "macro": "endmacro",
    JINJA_RAW_BLOCK_NAME: JINJA_RAW_BLOCK_END_NAME,
    "set": "endset",
    "with": "endwith",
}
JINJA_CONTROL_KEYWORDS: Final = frozenset(
    {
        "if",
        "elif",
        "else",
        "endif",
        *JINJA_NEUTRAL_BLOCK_ENDINGS,
        *JINJA_NEUTRAL_BLOCK_ENDINGS.values(),
    }
)
_JINJA_RAW_BLOCK_RE: Final = re.compile(
    rf"(?P<start>{re.escape(BLOCK_DELIMITER_START)}\s*"
    rf"{re.escape(JINJA_RAW_BLOCK_NAME)}\s*{re.escape(BLOCK_DELIMITER_END)})"
    rf"(?P<body>.*?)"
    rf"(?P<end>{re.escape(BLOCK_DELIMITER_START)}\s*"
    rf"{re.escape(JINJA_RAW_BLOCK_END_NAME)}\s*{re.escape(BLOCK_DELIMITER_END)})",
    re.DOTALL,
)


def _is_jinja_control_block(body: str) -> bool:
    return bool(body) and body.split()[0] in JINJA_CONTROL_KEYWORDS


@dataclass(frozen=True)
class IncludeDirective:
    """Source representation: ``{!% include 'path/to/file.md' %!}``.

    The path is interpreted relative to the build's shared_root.
    """

    path: str


@dataclass(frozen=True)
class RequireSkillDirective:
    """Source representation: ``{!% require_skill 'plugin:skill-name' %!}``.

    Expands to identical coding-agent-neutral invocation text in both
    targets. Replaces the execution-time ``!` `cat`` injection that has no Codex
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


class RuntimeTokenError(BuildError):
    """A runtime-divergent token is unresolved or leaked into guarded source.

    Raised when a `tool(...)` token names an unknown capability or a runtime the
    capability has no name for, and when a raw runtime-divergent name appears in a
    guarded plugin's authored source instead of a token or a per-runtime conditional.
    """


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
        body = match.group(1).strip()
        if _is_jinja_control_block(body):
            continue
        body_match = _DIRECTIVE_BODY_RE.fullmatch(body)
        if body_match is None:
            raise DirectiveSyntaxError(f"invalid directive: {match.group(0)!r}")
        name = body_match.group("name")
        argument = _directive_argument(body_match.group("argument"), match.group(0))
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
            f"{BLOCK_DELIMITER_START} include "
            f"{_directive_literal(directive.path)} {BLOCK_DELIMITER_END}"
        )
    if isinstance(directive, RequireSkillDirective):
        return (
            f"{BLOCK_DELIMITER_START} require_skill "
            f"{_directive_literal(directive.skill_ref)} "
            f"{BLOCK_DELIMITER_END}"
        )
    raise DirectiveSyntaxError(f"unsupported directive: {directive!r}")


def format_jinja_raw_block(body: str) -> str:
    """Return an authored Jinja raw block containing ``body``."""
    return (
        f"{BLOCK_DELIMITER_START} {JINJA_RAW_BLOCK_NAME} {BLOCK_DELIMITER_END}"
        f"{body}"
        f"{BLOCK_DELIMITER_START} {JINJA_RAW_BLOCK_END_NAME} {BLOCK_DELIMITER_END}"
    )


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
    """Return the coding-agent-neutral invocation text for the named skill.

    Output is identical for both Claude Code and Codex targets — the text
    instructs the agent to invoke the named skill before proceeding.
    """
    return REQUIRE_SKILL_GUIDANCE_TEMPLATE.format(skill_ref=directive.skill_ref)


# ---------------------------------------------------------------------------
# Stage 3: Template rendering
# ---------------------------------------------------------------------------


def _render_variables(
    target: _Target,
    *,
    plugin_name: str | None = None,
) -> dict[str, object]:
    """Return the Jinja render variables for a build target.

    Carries the build target name and the spx version floor. The floor is
    sourced from the single source of truth in
    ``outcomeeng.validation.spx_version`` so the value the build renders into
    shipped content cannot drift from the floor the product enforces.
    """
    variables = {
        BUILD_TARGET_VARIABLE: target.value,
        SPX_FLOOR_VARIABLE: REQUIRED_SPX_VERSION,
        **diagnose_manifest_render_variables(),
    }
    if plugin_name is not None:
        variables[PLUGIN_NAME_VARIABLE] = plugin_name
    return variables


def render_text(
    template: str,
    *,
    shared_root: Path | None = None,
    variables: dict[str, object] | None = None,
    runtime_token_registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> str:
    """Render a template by parsing and recursively expanding directives.

    Pass shared_root when the template contains include directives.
    Standard Jinja2 syntax in the template (``{% %}``, ``{{ }}``) is
    preserved verbatim — only the custom-delimiter directives are expanded.

    Raises CyclicIncludeError if include directives form a cycle.
    """
    raw_literals: list[tuple[str, str]] = []
    rendered = _render_directives(
        template,
        shared_root=shared_root,
        include_stack=(),
        variables=variables,
        runtime_token_registry=runtime_token_registry,
        raw_literals=raw_literals,
    )
    return _restore_literals(
        _render_jinja(
            rendered,
            shared_root=shared_root,
            variables=variables,
            runtime_token_registry=runtime_token_registry,
        ),
        tuple(raw_literals),
    )


def _render_jinja(
    template: str,
    *,
    shared_root: Path | None,
    variables: dict[str, object] | None,
    runtime_token_registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> str:
    """Evaluate custom-delimiter Jinja variables and control blocks."""
    # Run the Jinja pass when a variable token ({{! !}}) or a Jinja control block
    # ({!% if %!}) survives directive expansion — bare conditionals carry no
    # variable token but still need evaluation.
    if (
        VARIABLE_DELIMITER_START not in template
        and BLOCK_DELIMITER_START not in template
    ):
        return template
    # The skill-directory rewrite escape shares the {!# #!} syntax Jinja treats as
    # a comment, but it is processed later by rewrite_paths_for_target, not here.
    # Protect it across the Jinja render so the escape survives intact.
    protected = template.replace(
        SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE, SKILL_DIR_REWRITE_ESCAPE_PLACEHOLDER
    )
    try:
        environment = make_jinja_environment(
            shared_root,
            runtime_token_registry=runtime_token_registry,
        )
        result = environment.from_string(protected).render(variables or {})
    except TemplateError as exc:
        raise TemplateRenderError(str(exc)) from exc
    return result.replace(
        SKILL_DIR_REWRITE_ESCAPE_PLACEHOLDER, SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
    )


def _render_target_scope(
    template: str,
    *,
    target: _Target,
    plugin_name: str,
    shared_root: Path,
) -> str:
    """Evaluate one target's Jinja control flow while preserving directives."""
    raw_literals: list[tuple[str, str]] = []
    return _render_jinja_preserving_directives(
        template,
        shared_root=shared_root,
        variables=_render_variables(target, plugin_name=plugin_name),
        raw_literals=raw_literals,
    )


def _render_jinja_preserving_directives(
    template: str,
    *,
    shared_root: Path | None,
    variables: dict[str, object] | None,
    runtime_token_registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
    raw_literals: list[tuple[str, str]],
) -> str:
    """Evaluate Jinja control flow while collecting protected raw literals."""
    protected_template = _protect_jinja_raw_bodies(template, raw_literals=raw_literals)
    preserved: list[tuple[str, str]] = []

    def mask_directive(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        if _is_jinja_control_block(body):
            return match.group(0)
        placeholder = _directive_placeholder(protected_template, len(preserved))
        preserved.append((placeholder, match.group(0)))
        return placeholder

    scoped = _render_jinja(
        _DIRECTIVE_RE.sub(mask_directive, protected_template),
        shared_root=shared_root,
        variables=variables,
        runtime_token_registry=runtime_token_registry,
    )
    for placeholder, directive in preserved:
        scoped = scoped.replace(placeholder, directive)
    return scoped


def _protect_jinja_raw_bodies(
    template: str,
    *,
    raw_literals: list[tuple[str, str]],
) -> str:
    def replace(match: re.Match[str]) -> str:
        placeholder = _directive_placeholder(template, len(raw_literals))
        while any(existing == placeholder for existing, _ in raw_literals):
            placeholder += _PLANNING_DIRECTIVE_PLACEHOLDER_END
        raw_literals.append((placeholder, match.group("body")))
        return f"{match.group('start')}{placeholder}{match.group('end')}"

    return _JINJA_RAW_BLOCK_RE.sub(replace, template)


def _restore_literals(text: str, literals: tuple[tuple[str, str], ...]) -> str:
    for placeholder, literal in literals:
        text = text.replace(placeholder, literal)
    return text


def _directive_placeholder(template: str, index: int) -> str:
    placeholder = (
        f"{_PLANNING_DIRECTIVE_PLACEHOLDER_START}{index}"
        f"{_PLANNING_DIRECTIVE_PLACEHOLDER_END}"
    )
    while placeholder in template:
        placeholder += _PLANNING_DIRECTIVE_PLACEHOLDER_END
    return placeholder


# ---------------------------------------------------------------------------
# Stage 4: Per-target translation
# ---------------------------------------------------------------------------


def rewrite_paths_for_target(text: str, *, target: _Target) -> str:
    """Apply target-specific path rewriting.

    For Target.CLAUDE: identity (CLAUDE_SKILL_DIR_TOKEN preserved verbatim).
    For Target.CODEX: every occurrence of CLAUDE_SKILL_DIR_TOKEN is rewritten
    to Codex's skill-directory token unless the source line carries
    SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE.

    Idempotence holds for Target.CLAUDE and for any text under Target.CODEX
    that contains no SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE. Escaped content
    under Target.CODEX is intentionally non-idempotent: the first pass strips
    the directive and preserves CLAUDE_SKILL_DIR_TOKEN, while a second pass —
    seeing no directive — would rewrite that surviving token to
    CODEX_SKILL_DIR_TOKEN. This is safe because the build processes src/
    exclusively and never re-processes dist/ output.
    """
    protected = _protect_skill_dir_rewrite_escapes(text)
    if target is _Target.CLAUDE:
        return protected.replace(SKILL_DIR_REWRITE_PLACEHOLDER, CLAUDE_SKILL_DIR_TOKEN)

    translated = protected.replace(CLAUDE_SKILL_DIR_TOKEN, CODEX_SKILL_DIR_TOKEN)
    return translated.replace(SKILL_DIR_REWRITE_PLACEHOLDER, CLAUDE_SKILL_DIR_TOKEN)


def execution_time_injection_commands(text: str) -> tuple[str, ...]:
    """Return the commands embedded in execution-time dynamic context."""
    return tuple(
        match.group("command")
        for match in EXECUTION_TIME_INJECTION_PATTERN.finditer(text)
    )


def contains_execution_time_skill_content_injection(text: str) -> bool:
    """Return whether dynamic context can inline a skill definition."""
    return any(
        SKILL_FILENAME in command
        or (
            "../" in command
            and ("*" in command or f"/{REFERENCES_SUBDIR_NAME}/" in command)
        )
        for command in execution_time_injection_commands(text)
    )


def skill_dir_path_references(text: str, token: str) -> tuple[str, ...]:
    """Return complete path references rooted at ``token`` in source order."""
    pattern = re.compile(rf"{re.escape(token)}{SKILL_DIR_REFERENCE_SUFFIX_PATTERN}")
    return tuple(match.group(0) for match in pattern.finditer(text))


def _protect_skill_dir_rewrite_escapes(text: str) -> str:
    """Protect authoring-guidance uses of the Claude Code skill-dir token."""
    protected_lines: list[str] = []
    for line in text.splitlines(keepends=True):
        if SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE not in line:
            protected_lines.append(line)
            continue
        line_without_directive = line.replace(
            f" {SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE}",
            "",
        ).replace(SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE, "")
        protected_lines.append(
            line_without_directive.replace(
                CLAUDE_SKILL_DIR_TOKEN,
                SKILL_DIR_REWRITE_PLACEHOLDER,
            )
        )
    return "".join(protected_lines)


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


def frontmatter_field_names(text: str) -> frozenset[str]:
    """Return top-level field names from the opening YAML frontmatter fence."""
    if not text.startswith("---\n"):
        return frozenset()
    closing_index = text.find("\n---", len("---\n"))
    if closing_index == -1:
        raise FrontmatterError("frontmatter starts with --- but has no closing fence")
    fence_end = closing_index + len("\n---")
    if len(text) > fence_end and text[fence_end] not in {"\n", "\r"}:
        raise FrontmatterError("frontmatter closing fence is malformed")
    return frozenset(
        key
        for line in text[len("---\n") : closing_index].splitlines()
        if (key := _frontmatter_key(line)) is not None
    )


# ---------------------------------------------------------------------------
# Stage 5: Build orchestration
# ---------------------------------------------------------------------------


def emit_skill(
    emission: PlannedEmission,
    *,
    dist_root: Path,
    shared_root: Path,
) -> None:
    """Emit one skill's output for one target.

    Reads the emission's SKILL.md source, renders directives via shared_root,
    applies target-specific translation, and writes the result to the
    destination the build plan assigned — which is the source's mirrored path
    for an authored plugin skill and the per-plugin path for a template.
    """
    src_root = shared_root.parent
    destination = dist_root / emission.target.value / emission.relative_path
    rendered = render_planned_emission_text(emission, src_root=src_root)
    translated = _translate_rendered_text(rendered, target=emission.target)
    _write_text(destination, translated)
    shutil.copymode(emission.source, destination)


def build(
    src_root: Path,
    dist_root: Path,
    *,
    formatter_probe: FormatterProbe = shutil.which,
    formatter_runner: FormatterRunner | None = None,
) -> None:
    """End-to-end build: src/ -> dist/claude/ and dist/codex/.

    Validates src_root's tree shape, then iterates every plugin source file
    and emits both target outputs. Formatter discovery and execution remain
    injectable so callers can verify host-specific boundaries. The build is
    deterministic and idempotent — the same src_root always produces
    byte-identical outputs, and re-running the build over a previously-emitted
    dist_root produces no changes.

    Raises SourceFormatError if src_root's tree shape is invalid.
    """
    plan = plan_emissions(src_root)
    runner = _run_formatter if formatter_runner is None else formatter_runner
    formatter = _require_formatter(
        formatter_probe=formatter_probe,
        runner=runner,
        cwd=src_root,
    )
    shared_root = src_root / SHARED_DIR_NAME

    for target in _Target:
        target_root = dist_root / target.value
        if target_root.exists():
            shutil.rmtree(target_root)
        target_root.mkdir(parents=True, exist_ok=True)

    for emission in plan.emissions:
        if emission.action is EmissionAction.CONVERT_AGENT:
            _emit_converted_agent(emission, dist_root=dist_root, src_root=src_root)
            continue
        if emission.action is EmissionAction.PLACEMENT_MANIFEST:
            _emit_placement_manifest(emission, dist_root=dist_root)
            continue
        if emission.action is EmissionAction.FAN_OUT:
            _emit_planned_fan_out(
                emission,
                dist_root=dist_root,
                src_root=src_root,
            )
            continue
        if emission.action is EmissionAction.RENDER:
            if (
                SKILLS_SUBDIR_NAME in emission.relative_path.parts
                and emission.source.name == SKILL_FILENAME
            ):
                emit_skill(
                    emission,
                    dist_root=dist_root,
                    shared_root=shared_root,
                )
                continue
            _emit_rendered_file(
                emission,
                dist_root=dist_root,
                src_root=src_root,
            )
            continue
        _copy_unrendered_file(
            emission,
            dist_root=dist_root,
            src_root=src_root,
        )

    _run_dist_formatter(
        dist_root,
        formatter=formatter,
        runner=runner,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the build recipe."""
    parser = argparse.ArgumentParser(
        prog="outcomeeng.distribution.build",
        description="Build src/ plugin sources into dist/claude and dist/codex.",
    )
    parser.add_argument(
        "src_root", type=Path, nargs="?", default=Path(SOURCE_ROOT_NAME)
    )
    parser.add_argument("dist_root", type=Path, nargs="?", default=Path("dist"))
    args = parser.parse_args(argv)
    try:
        build(args.src_root, args.dist_root)
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _make_kind_global(
    kind: str,
    runtime_token_registry: dict[str, RuntimeTokenKind],
) -> Callable[..., str]:
    """Build the template global that renders the named registry ``kind``.

    Each kind (`tool`, `field`, `term`, `file`) is exposed under its own name. The
    global renders the build target's name by default; a runtime-explicit second
    argument (`tool('ask_user', 'claude')`) renders the named runtime's name
    regardless of target. Resolution is delegated to ``resolve_runtime_token`` so
    every kind shares one path. Raises RuntimeTokenError when no target is in
    context for the default form, or when the capability has no name for the
    resolved runtime.
    """

    @pass_context
    def render(context: Context, capability: str, runtime: str | None = None) -> str:
        resolved = runtime if runtime is not None else context.get("target")
        if resolved is None:
            raise RuntimeTokenError(
                f"{kind} token {capability!r} rendered with no target in context"
            )
        return resolve_runtime_token(
            kind,
            capability,
            resolved,
            registry=runtime_token_registry,
        )

    return render


def make_jinja_environment(
    shared_root: Path | None = None,
    *,
    runtime_token_registry: dict[str, RuntimeTokenKind] = RUNTIME_TOKEN_REGISTRY,
) -> Environment:
    """Return the build's configured Jinja2 environment."""
    loader = FileSystemLoader(str(shared_root)) if shared_root is not None else None
    environment = Environment(
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
    # One template global per registry kind, named after the kind: tool(), field(),
    # term(), file(). A new kind in the registry is exposed automatically.
    for kind in runtime_token_registry:
        environment.globals[kind] = _make_kind_global(kind, runtime_token_registry)
    return environment


def _render_directives(
    template: str,
    *,
    shared_root: Path | None,
    include_stack: tuple[Path, ...],
    variables: dict[str, object] | None,
    runtime_token_registry: dict[str, RuntimeTokenKind],
    raw_literals: list[tuple[str, str]],
) -> str:
    scoped_template = _render_jinja_preserving_directives(
        template,
        shared_root=shared_root,
        variables=variables,
        runtime_token_registry=runtime_token_registry,
        raw_literals=raw_literals,
    )

    def replace(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        if _is_jinja_control_block(body):
            return match.group(0)
        body_match = _DIRECTIVE_BODY_RE.fullmatch(body)
        if body_match is None:
            raise DirectiveSyntaxError(f"invalid directive: {match.group(0)!r}")
        name = body_match.group("name")
        argument = _directive_argument(body_match.group("argument"), match.group(0))
        if name == "require_skill":
            return expand_require_skill(RequireSkillDirective(skill_ref=argument))
        if name != "include":
            raise DirectiveSyntaxError(f"unknown directive {name!r}")
        if shared_root is None:
            raise IncludeResolutionError("include directive requires shared_root")
        include_path = _resolve_under_root(shared_root, argument)
        _assert_include_not_cyclic(include_path, include_stack=include_stack)
        included = expand_include(
            IncludeDirective(path=argument), shared_root=shared_root
        )
        return _render_directives(
            included,
            shared_root=shared_root,
            include_stack=(*include_stack, include_path),
            variables=variables,
            runtime_token_registry=runtime_token_registry,
            raw_literals=raw_literals,
        )

    return _DIRECTIVE_RE.sub(replace, scoped_template)


def _directive_argument(argument_literal: str, source: str) -> str:
    try:
        argument = literal_eval(argument_literal)
    except (SyntaxError, ValueError) as error:
        raise DirectiveSyntaxError(f"invalid directive: {source!r}") from error
    if not isinstance(argument, str):
        raise DirectiveSyntaxError(f"invalid directive: {source!r}")
    return argument


def _directive_literal(argument: str) -> str:
    return repr(argument).replace("%", r"\x25")


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


def _assert_include_not_cyclic(
    include_path: Path,
    *,
    include_stack: tuple[Path, ...],
) -> None:
    if include_path in include_stack:
        cycle = " -> ".join(str(path) for path in (*include_stack, include_path))
        raise CyclicIncludeError(f"cyclic include detected: {cycle}")


def _frontmatter_key(line: str) -> str | None:
    if not line or line[0].isspace() or ":" not in line:
        return None
    key, _, _ = line.partition(":")
    return key.strip()


def _is_continuation_line(line: str) -> bool:
    return bool(line.startswith((" ", "\t")) or not line.strip())


def plugin_relative_path(path: Path, *, src_root: Path) -> Path:
    """Return ``path`` relative to the source ``plugins/`` directory."""
    plugins_root = src_root / PLUGINS_DIR_NAME
    try:
        return path.relative_to(plugins_root)
    except ValueError as exc:
        raise SourceFormatError(
            f"{path} is not under source plugins directory {plugins_root}"
        ) from exc


def source_plugin_name(path: Path, *, src_root: Path) -> str:
    """Return the source plugin directory that owns ``path``."""
    relative_path = plugin_relative_path(path, src_root=src_root)
    if len(relative_path.parts) < 2:
        raise SourceFormatError(f"{path} has no owning plugin directory")
    return relative_path.parts[0]


def _is_rendered_text(path: Path) -> bool:
    return path.suffix in _TEXT_FILE_SUFFIXES


def _emit_rendered_file(
    emission: PlannedEmission,
    *,
    dist_root: Path,
    src_root: Path,
) -> None:
    destination = dist_root / emission.target.value / emission.relative_path
    rendered = render_planned_emission_text(emission, src_root=src_root)
    translated = _translate_rendered_text(rendered, target=emission.target)
    _write_text(destination, translated)
    shutil.copymode(emission.source, destination)


def _emit_converted_agent(
    emission: PlannedEmission, *, dist_root: Path, src_root: Path
) -> None:
    """Convert one agent into its target's native artifact and place it.

    The conversion runs once here rather than once per consumer, so every
    consumer receives byte-identical definitions and the placement a consumer
    performs stays a file copy. The placement manifest beside the artifacts
    tells the plugin's lifecycle skill where the target reads them from and
    which namespace this plugin owns there.
    """
    destination = dist_root / emission.target.value / emission.relative_path
    rendered = render_planned_emission_text(emission, src_root=src_root)
    converted = convert_agent_markdown(
        rendered,
        source_path=emission.source,
        name=destination.stem,
    )
    _write_text(destination, converted)


def _emit_placement_manifest(emission: PlannedEmission, *, dist_root: Path) -> None:
    """Write the placement manifest a plugin's lifecycle skill reads."""
    capability = agent_capability(emission.target)
    if capability.checkout_directory is None:
        return
    plugin = emission.relative_path.parts[0]
    destination = dist_root / emission.target.value / emission.relative_path
    _write_text(
        destination,
        json.dumps(
            {"directory": capability.checkout_directory, "prefix": f"{plugin}_"},
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )


def _copy_unrendered_file(
    emission: PlannedEmission, *, dist_root: Path, src_root: Path
) -> None:
    destination = dist_root / emission.target.value / emission.relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(emission.source, destination)


def render_source_text(
    source_file: Path,
    *,
    target: _Target,
    src_root: Path,
) -> str:
    """Render one authored text file before target-specific translation."""
    return render_text(
        source_file.read_text(encoding="utf-8"),
        shared_root=src_root / SHARED_DIR_NAME,
        variables=_render_variables(
            target,
            plugin_name=source_plugin_name(source_file, src_root=src_root),
        ),
    )


def render_planned_emission_text(
    emission: PlannedEmission,
    *,
    src_root: Path,
) -> str:
    """Render one planned text emission before target-specific translation."""
    return render_text(
        emission.source.read_text(encoding="utf-8"),
        shared_root=src_root / SHARED_DIR_NAME,
        variables=_render_variables(
            emission.target,
            plugin_name=emission.relative_path.parts[0],
        ),
    )


def _translate_rendered_text(rendered: str, *, target: _Target) -> str:
    translated = rewrite_paths_for_target(rendered, target=target)
    if target is _Target.CODEX:
        return strip_frontmatter_fields(
            translated,
            fields=CLAUDE_ONLY_FRONTMATTER_FIELDS,
        )
    return translated


def _emit_planned_fan_out(
    emission: PlannedEmission,
    *,
    dist_root: Path,
    src_root: Path,
) -> None:
    destination = dist_root / emission.target.value / emission.relative_path
    if not _is_rendered_text(emission.source):
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(emission.source, destination)
        return
    rendered = render_planned_emission_text(emission, src_root=src_root)
    translated = _translate_rendered_text(rendered, target=emission.target)
    _write_text(destination, translated)
    shutil.copymode(emission.source, destination)


def _run_formatter(
    command: tuple[str, ...],
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _format_dist(
    dist_root: Path,
    *,
    formatter_probe: FormatterProbe = shutil.which,
    runner: FormatterRunner = _run_formatter,
) -> None:
    formatter = _require_formatter(
        formatter_probe=formatter_probe,
        runner=runner,
        cwd=dist_root,
    )
    _run_dist_formatter(dist_root, formatter=formatter, runner=runner)


def _require_formatter(
    *,
    formatter_probe: FormatterProbe,
    runner: FormatterRunner,
    cwd: Path,
) -> str:
    """Return the required formatter only when its version contract holds."""
    formatter = formatter_probe(FORMATTER_COMMAND_NAME)
    if formatter is None:
        raise BuildError(
            f"{FORMATTER_COMMAND_NAME} is required to format generated dist output"
        )
    version_command = formatter_version_command(formatter)
    version_result = runner(version_command, cwd)
    if version_result.returncode != 0:
        details = (version_result.stderr or version_result.stdout).strip()
        raise BuildError(f"{FORMATTER_COMMAND_NAME} version check failed: {details}")
    actual_version = version_result.stdout.strip()
    if actual_version != FORMATTER_VERSION_OUTPUT:
        raise BuildError(
            f"{FORMATTER_COMMAND_NAME} {FORMATTER_VERSION} is required; "
            f"found {actual_version or 'unknown version'}"
        )
    return formatter


def _run_dist_formatter(
    dist_root: Path,
    *,
    formatter: str,
    runner: FormatterRunner,
) -> None:
    """Format generated output with an already-accepted formatter."""
    command = formatter_format_command(formatter)
    result = runner(command, dist_root)
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise BuildError(
            f"{FORMATTER_COMMAND_NAME} failed while formatting dist: {details}"
        )


def formatter_version_command(formatter: str) -> tuple[str, ...]:
    """Return the source-owned formatter version probe command."""
    return (formatter, "--version")


def formatter_format_command(formatter: str) -> tuple[str, ...]:
    """Return the source-owned generated-tree formatting command."""
    return (
        formatter,
        "fmt",
        "--config",
        str(FORMATTER_CONFIG_PATH),
        "--allow-no-files",
        FORMATTER_FILE_GLOB,
    )


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def plugin_source_files(src_root: Path) -> tuple[Path, ...]:
    """Return every authored plugin source file the build emits."""
    plugins_root = src_root / PLUGINS_DIR_NAME
    return tuple(
        sorted(
            path
            for path in plugins_root.rglob("*")
            if path.is_file()
            and _is_authored_source_file(path.relative_to(plugins_root))
        )
    )


@dataclass(frozen=True)
class AgentCapability:
    """One target's native handling of the agent definitions a plugin ships.

    ``manifest_declares_agents`` is the capability that decides everything else:
    a target whose plugin manifest can declare agents receives them through the
    manifest in its own authored format, so the build emits the authored file
    unchanged and no checkout placement is required. A target whose manifest
    cannot receives a converted artifact inside the plugin's lifecycle skill,
    plus the placement manifest that directs it into ``checkout_directory``.
    ``namespaced`` records whether the target namespaces a plugin's agents; a
    flat namespace takes the plugin slug as a filename and identity prefix so a
    policy matching on name can tell one plugin's agents from another's.
    """

    manifest_declares_agents: bool
    namespaced: bool
    suffix: str
    checkout_directory: str | None


# Source-owned per-target agent capabilities. Adding a target adds an entry here
# rather than editing emission logic, per
# `spx/18-plugin-build.enabler/15-build-architecture.adr.md`. This registry is a
# sibling of RUNTIME_TOKEN_REGISTRY, not an entry in it: these values parameterize
# emission, while a runtime token renders a divergent name into authored text.
AGENT_CAPABILITY_REGISTRY: Final[dict[str, AgentCapability]] = {
    "claude": AgentCapability(
        manifest_declares_agents=True,
        namespaced=True,
        suffix=".md",
        checkout_directory=None,
    ),
    "codex": AgentCapability(
        manifest_declares_agents=False,
        namespaced=False,
        suffix=".toml",
        checkout_directory=".codex/agents",
    ),
}


def agent_capability(target: _Target) -> AgentCapability:
    """Return ``target``'s agent capability from the source-owned registry."""
    try:
        return AGENT_CAPABILITY_REGISTRY[target.value]
    except KeyError as exc:
        raise SourceFormatError(
            f"no agent capability registered for target {target.value}"
        ) from exc


def plugin_names(src_root: Path) -> tuple[str, ...]:
    """Return every authored plugin's directory name."""
    plugins_root = src_root / PLUGINS_DIR_NAME
    return tuple(
        sorted(child.name for child in plugins_root.iterdir() if child.is_dir())
    )


def template_source_files(src_root: Path) -> tuple[Path, ...]:
    """Return every per-plugin template source file the build fans out."""
    templates_root = src_root / TEMPLATES_DIR_NAME
    if not templates_root.is_dir():
        return ()
    return tuple(sorted(path for path in templates_root.rglob("*") if path.is_file()))


def template_relative_path(source_file: Path, *, src_root: Path, plugin: str) -> Path:
    """Return one template source's output path inside ``plugin``'s tree.

    A template directory named ``<template>`` renders into the skill directory
    ``<plugin>-<template>``, so ``src/templates/plugin/SKILL.md`` reaches
    ``<plugin>/skills/<plugin>-plugin/SKILL.md`` in every generated target tree.
    """
    within_templates = source_file.relative_to(src_root / TEMPLATES_DIR_NAME)
    template_name = within_templates.parts[0]
    remainder = Path(*within_templates.parts[1:])
    skill_dir = f"{plugin}-{template_name}"
    return Path(plugin) / SKILLS_SUBDIR_NAME / skill_dir / remainder


def plan_emissions(src_root: Path) -> BuildPlan:
    """Return the complete collision-free output plan for ``src_root``."""
    _validate_source_tree(src_root)
    shared_root = src_root / SHARED_DIR_NAME
    plugin_sources = plugin_source_files(src_root)
    emissions: list[PlannedEmission] = []
    for source_file in plugin_sources:
        relative_path = plugin_relative_path(source_file, src_root=src_root)
        action = (
            EmissionAction.RENDER
            if _is_rendered_text(source_file)
            else EmissionAction.COPY
        )
        for target in _Target:
            target_path, target_action = _agent_aware_destination(
                relative_path, action=action, target=target
            )
            emissions.append(
                PlannedEmission(
                    source=source_file,
                    target=target,
                    relative_path=target_path,
                    action=target_action,
                )
            )
            emissions.extend(
                _planned_fan_out_emissions(
                    source_file,
                    target=target,
                    relative_path=relative_path,
                    shared_root=shared_root,
                )
            )
    emissions.extend(_planned_template_emissions(src_root, shared_root=shared_root))
    emissions.extend(_planned_placement_emissions(src_root, emissions))
    plan = BuildPlan(plugin_sources=plugin_sources, emissions=tuple(emissions))
    collisions = plan.collisions()
    if collisions:
        details = ", ".join(
            f"{target.value}/{path}: {', '.join(map(str, sources))}"
            for (target, path), sources in sorted(
                collisions.items(), key=lambda item: (item[0][0].value, item[0][1])
            )
        )
        raise SourceFormatError(f"multiple sources emit the same output: {details}")
    return plan


def agent_slug(plugin: str, stem: str, *, capability: AgentCapability) -> str:
    """Return one agent's filename stem in ``capability``'s namespace.

    A target that namespaces plugin agents carries the bare agent name; a flat
    namespace takes the plugin slug as a prefix, rendering the namespaced
    ``<plugin>:<agent>`` identity as ``<plugin>_<agent>``.
    """
    return stem if capability.namespaced else f"{plugin}_{stem}"


def _agent_aware_destination(
    relative_path: Path,
    *,
    action: EmissionAction,
    target: _Target,
) -> tuple[Path, EmissionAction]:
    """Return one source's destination and action for ``target``.

    Every non-agent source keeps the mirrored path the plan computed. An agent
    source reaching a target whose manifest cannot declare agents is converted
    into that target's native artifact and placed inside the plugin's lifecycle
    skill, the one surface the manifest declares that can carry it.
    """
    parts = relative_path.parts
    if len(parts) < 3 or parts[1] != AGENTS_SUBDIR_NAME:
        return relative_path, action
    if relative_path.suffix != MARKDOWN_FILE_SUFFIX:
        # An agent definition is authored as markdown. Any other file under
        # `agents/` is not one, so it keeps its mirrored path rather than being
        # converted into an artifact whose name would collide with the real
        # agent of the same stem.
        return relative_path, action
    capability = agent_capability(target)
    if capability.manifest_declares_agents:
        return relative_path, action
    plugin = parts[0]
    stem = Path(parts[-1]).stem
    filename = f"{agent_slug(plugin, stem, capability=capability)}{capability.suffix}"
    destination = (
        Path(plugin)
        / SKILLS_SUBDIR_NAME
        / f"{plugin}-{LIFECYCLE_TEMPLATE_NAME}"
        / AGENTS_SUBDIR_NAME
        / filename
    )
    return destination, EmissionAction.CONVERT_AGENT


def _planned_placement_emissions(
    src_root: Path,
    emissions: Sequence[PlannedEmission],
) -> tuple[PlannedEmission, ...]:
    """Return one placement manifest per plugin whose agents need placement.

    The manifest tells a plugin's lifecycle skill which checkout directory its
    target reads agent definitions from and which namespace this plugin owns
    there. It exists only where converted agents were planned, so a plugin that
    ships no agents carries no manifest and its lifecycle skill reports that.
    """
    template = src_root / TEMPLATES_DIR_NAME / LIFECYCLE_TEMPLATE_NAME / SKILL_FILENAME
    planned: dict[tuple[_Target, Path], PlannedEmission] = {}
    for emission in emissions:
        if emission.action is not EmissionAction.CONVERT_AGENT:
            continue
        manifest_path = emission.relative_path.parent / PLACEMENT_MANIFEST_FILENAME
        planned[(emission.target, manifest_path)] = PlannedEmission(
            source=template,
            target=emission.target,
            relative_path=manifest_path,
            action=EmissionAction.PLACEMENT_MANIFEST,
        )
    return tuple(
        planned[key] for key in sorted(planned, key=lambda k: (k[0].value, k[1]))
    )


def _planned_template_emissions(
    src_root: Path,
    *,
    shared_root: Path,
) -> tuple[PlannedEmission, ...]:
    """Return every per-plugin template output across plugins and targets.

    Each template source renders once per plugin per target, so one authored
    body reaches every plugin's generated tree without being copied per plugin.
    """
    emissions: list[PlannedEmission] = []
    for source_file in template_source_files(src_root):
        action = (
            EmissionAction.RENDER
            if _is_rendered_text(source_file)
            else EmissionAction.COPY
        )
        for plugin in plugin_names(src_root):
            relative_path = template_relative_path(
                source_file, src_root=src_root, plugin=plugin
            )
            for target in _Target:
                emissions.append(
                    PlannedEmission(
                        source=source_file,
                        target=target,
                        relative_path=relative_path,
                        action=action,
                    )
                )
                emissions.extend(
                    _planned_fan_out_emissions(
                        source_file,
                        target=target,
                        relative_path=relative_path,
                        shared_root=shared_root,
                    )
                )
    return tuple(emissions)


def _planned_fan_out_emissions(
    source_file: Path,
    *,
    target: _Target,
    relative_path: Path,
    shared_root: Path,
) -> tuple[PlannedEmission, ...]:
    if (
        SKILLS_SUBDIR_NAME not in relative_path.parts
        or source_file.suffix not in _TEXT_FILE_SUFFIXES
    ):
        return ()
    scoped_source = _render_target_scope(
        source_file.read_text(encoding="utf-8"),
        target=target,
        plugin_name=relative_path.parts[0],
        shared_root=shared_root,
    )
    directives = _include_directives(scoped_source)
    return tuple(
        dict.fromkeys(
            emission
            for directive in directives
            for emission in _planned_include_emissions(
                directive,
                target=target,
                relative_path=relative_path,
                shared_root=shared_root,
            )
        )
    )


def _planned_include_emissions(
    directive: IncludeDirective,
    *,
    target: _Target,
    relative_path: Path,
    shared_root: Path,
    include_stack: tuple[Path, ...] = (),
) -> tuple[PlannedEmission, ...]:
    pending = [(directive, include_stack)]
    emissions: list[PlannedEmission] = []
    while pending:
        current_directive, current_stack = pending.pop()
        fragment_path = _resolve_under_root(shared_root, current_directive.path)
        _assert_include_not_cyclic(fragment_path, include_stack=current_stack)
        fragment_body = _render_target_scope(
            expand_include(current_directive, shared_root=shared_root),
            target=target,
            plugin_name=relative_path.parts[0],
            shared_root=shared_root,
        )
        topic_root = fragment_path.parent
        emissions.extend(
            PlannedEmission(
                source=child_file,
                target=target,
                relative_path=(
                    relative_path.parent / child_file.relative_to(topic_root)
                ),
                action=EmissionAction.FAN_OUT,
            )
            for child_file in _fan_out_topic_files(topic_root)
        )
        nested_stack = (*current_stack, fragment_path)
        pending.extend(
            (nested_directive, nested_stack)
            for nested_directive in reversed(_include_directives(fragment_body))
        )
    return tuple(dict.fromkeys(emissions))


def _include_directives(text: str) -> tuple[IncludeDirective, ...]:
    return tuple(
        directive
        for directive in parse_directives(text)
        if isinstance(directive, IncludeDirective)
    )


def _fan_out_topic_files(topic_root: Path) -> tuple[Path, ...]:
    return tuple(
        child_file
        for child in sorted(topic_root.iterdir())
        if child.name != SHARED_FRAGMENT_FILENAME
        for child_file in _fan_out_child_files(child)
    )


def _fan_out_child_files(child: Path) -> tuple[Path, ...]:
    if child.is_dir():
        return tuple(sorted(path for path in child.rglob("*") if path.is_file()))
    return (child,)


def _is_authored_source_file(path: Path) -> bool:
    return not (
        IGNORED_SOURCE_DIRECTORY_NAMES.intersection(path.parts)
        or path.suffix in IGNORED_SOURCE_FILE_SUFFIXES
    )


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

    templates_root = src_root / TEMPLATES_DIR_NAME
    if templates_root.exists():
        for template_root in sorted(
            path for path in templates_root.iterdir() if path.is_dir()
        ):
            if not (template_root / SKILL_FILENAME).is_file():
                raise SourceFormatError(
                    f"template directory missing {SKILL_FILENAME}: "
                    f"{template_root.relative_to(src_root)}"
                )

    for plugin_root in sorted(path for path in plugins_root.iterdir() if path.is_dir()):
        for child in sorted(path for path in plugin_root.iterdir() if path.is_dir()):
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


if __name__ == "__main__":
    raise SystemExit(main())
