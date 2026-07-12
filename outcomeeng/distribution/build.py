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
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
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
    CODEX_STANDARD_MODEL,
    CODEX_STRONG_MODEL,
)
from outcomeeng.distribution.contracts import (
    ASK_USER_TOOL_NAMES,
    REQUIRE_SKILL_GUIDANCE_TEMPLATE,
    ROOT_GUIDE_FILE_NAMES,
    TEXT_FILE_SUFFIXES as _TEXT_FILE_SUFFIXES,
    Target as _Target,
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

PLUGINS_DIR_NAME: Final = "plugins"
SHARED_DIR_NAME: Final = "_shared"
SHARED_FRAGMENT_FILENAME: Final = "fragment.md"
SKILLS_SUBDIR_NAME: Final = "skills"
COMMANDS_SUBDIR_NAME: Final = "commands"
AGENTS_SUBDIR_NAME: Final = "agents"
SCRIPTS_SUBDIR_NAME: Final = "scripts"
HOOKS_SUBDIR_NAME: Final = "hooks"
CLAUDE_PLUGIN_SUBDIR_NAME: Final = ".claude-plugin"
CODEX_PLUGIN_SUBDIR_NAME: Final = ".codex-plugin"
REFERENCES_SUBDIR_NAME: Final = "references"
PLUGIN_SUBDIRS: Final = frozenset(
    {
        SKILLS_SUBDIR_NAME,
        COMMANDS_SUBDIR_NAME,
        AGENTS_SUBDIR_NAME,
        SCRIPTS_SUBDIR_NAME,
        HOOKS_SUBDIR_NAME,
        CLAUDE_PLUGIN_SUBDIR_NAME,
        CODEX_PLUGIN_SUBDIR_NAME,
    }
)

SKILL_FILENAME: Final = "SKILL.md"
COMMAND_FILE_SUFFIX: Final = ".md"
AGENT_FILE_SUFFIX: Final = ".md"


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
CLAUDE_ONLY_FRONTMATTER_FIELDS: Final = ("disable-model-invocation",)

# The literal token Claude Code expands during skill execution. Source files
# contain this token verbatim; the build preserves it in dist/claude/ outputs
# and rewrites any occurrence to Codex's skill-directory token in dist/codex/
# outputs.
CLAUDE_SKILL_DIR_TOKEN: Final = "${CLAUDE_SKILL_DIR}"
CODEX_SKILL_DIR_TOKEN: Final = "${SKILL_DIR}"
SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE: Final = "{!# no-codex-skill-dir-rewrite #!}"
SKILL_DIR_REWRITE_PLACEHOLDER: Final = "__OUTCOMEENG_CLAUDE_SKILL_DIR_LITERAL__"
# Protects the escape directive (which shares Jinja's {!# #!} comment syntax) across
# the Jinja render pass so it reaches rewrite_paths_for_target unstripped.
SKILL_DIR_REWRITE_ESCAPE_PLACEHOLDER: Final = "__OUTCOMEENG_SKILL_DIR_REWRITE_ESCAPE__"

FORMATTER_COMMAND_NAME: Final = "dprint"
FORMATTER_FILE_GLOB: Final = "**/*.{md,json,toml,py,yaml,yml,js,html}"
FormatterProbe = Callable[[str], str | None]
FormatterRunner = Callable[[tuple[str, ...]], subprocess.CompletedProcess[str]]


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


RUNTIME_TOKEN_TOOL_KIND: Final = "tool"
RUNTIME_TOKEN_FIELD_KIND: Final = "field"
RUNTIME_TOKEN_TERM_KIND: Final = "term"
RUNTIME_TOKEN_FILE_KIND: Final = "file"

RUNTIME_TOKEN_ASK_USER_CAPABILITY: Final = "ask_user"
RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY: Final = "schedule_wakeup"
RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY: Final = "configured_agent_prompt"
RUNTIME_TOKEN_CONFIGURED_AGENT_CAPABILITY: Final = "configured_agent"
RUNTIME_TOKEN_CONFIGURED_AGENT_STANDARD_MODEL_CAPABILITY: Final = (
    "configured_agent_standard_model"
)
RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_MODEL_CAPABILITY: Final = (
    "configured_agent_fast_model"
)
RUNTIME_TOKEN_CONFIGURED_AGENT_AUDITOR_MODEL_CAPABILITY: Final = (
    "configured_agent_auditor_model"
)
RUNTIME_TOKEN_CONFIGURED_AGENT_STRONG_MODELS_CAPABILITY: Final = (
    "configured_agent_strong_models"
)
RUNTIME_TOKEN_CONFIGURED_AGENT_FAST_OR_STANDARD_MODELS_CAPABILITY: Final = (
    "configured_agent_fast_or_standard_models"
)
RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY: Final = "root_guide"


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
        lint_enforced=True,
        names={
            RUNTIME_TOKEN_ASK_USER_CAPABILITY: ASK_USER_TOOL_NAMES,
            "spawn_agent": {"codex": "multi_agent_v1.spawn_agent"},
            "wait_agent": {"codex": "multi_agent_v1.wait_agent"},
            "close_agent": {"codex": "multi_agent_v1.close_agent"},
            RUNTIME_TOKEN_SCHEDULE_WAKEUP_CAPABILITY: {"claude": "ScheduleWakeup"},
        },
    ),
    RUNTIME_TOKEN_FIELD_KIND: RuntimeTokenKind(
        lint_enforced=True,
        names={
            RUNTIME_TOKEN_CONFIGURED_AGENT_PROMPT_CAPABILITY: (
                CONFIGURED_AGENT_PROMPT_FIELD_NAMES
            ),
        },
    ),
    RUNTIME_TOKEN_TERM_KIND: RuntimeTokenKind(
        lint_enforced=False,
        names=CONFIGURED_AGENT_TERM_NAMES,
    ),
    RUNTIME_TOKEN_FILE_KIND: RuntimeTokenKind(
        lint_enforced=True,
        names={
            RUNTIME_TOKEN_ROOT_GUIDE_CAPABILITY: ROOT_GUIDE_FILE_NAMES,
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
    r"(?P<quote>['\"])(?P<argument>.*?)(?P=quote)$",
    re.DOTALL,
)

# Jinja control statements share the `{!% %!}` block delimiter with the build's
# directives. A block whose first token is one of these is a Jinja statement the
# build leaves for the render pass; any other non-`name 'arg'` body is a malformed
# directive that must fail the build rather than ship verbatim.
_JINJA_CONTROL_KEYWORDS: Final = frozenset(
    {"if", "elif", "else", "endif", "for", "endfor", "set", "with", "endwith"}
)


def _is_jinja_control_block(body: str) -> bool:
    return bool(body) and body.split()[0] in _JINJA_CONTROL_KEYWORDS


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
        body = " ".join(match.group(1).split())
        body_match = _DIRECTIVE_BODY_RE.match(body)
        if body_match is None:
            if _is_jinja_control_block(body):
                # A Jinja block statement (`{!% if target == 'codex' %!}`,
                # `{!% endif %!}`) — not a directive to collect; Jinja evaluates it.
                continue
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
    """Return the coding-agent-neutral invocation text for the named skill.

    Output is identical for both Claude Code and Codex targets — the text
    instructs the agent to invoke the named skill before proceeding.
    """
    return REQUIRE_SKILL_GUIDANCE_TEMPLATE.format(skill_ref=directive.skill_ref)


# ---------------------------------------------------------------------------
# Stage 3: Template rendering
# ---------------------------------------------------------------------------


def _render_variables(target: _Target) -> dict[str, object]:
    """Return the Jinja render variables for a build target.

    Carries the build target name and the spx version floor. The floor is
    sourced from the single source of truth in
    ``outcomeeng.validation.spx_version`` so the value the build renders into
    shipped content cannot drift from the floor the product enforces.
    """
    return {"target": target.value, "spx_floor": REQUIRED_SPX_VERSION}


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
    # Run the Jinja pass when a variable token ({{! !}}) or a Jinja control block
    # ({!% if %!}) survives directive expansion — bare conditionals carry no
    # variable token but still need evaluation. The remaining {!% blocks are
    # control statements; include/require_skill directives were already expanded.
    if (
        VARIABLE_DELIMITER_START not in rendered
        and BLOCK_DELIMITER_START not in rendered
    ):
        return rendered
    # The skill-directory rewrite escape shares the {!# #!} syntax Jinja treats as
    # a comment, but it is processed later by rewrite_paths_for_target, not here.
    # Protect it across the Jinja render so the escape survives intact.
    protected = rendered.replace(
        SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE, SKILL_DIR_REWRITE_ESCAPE_PLACEHOLDER
    )
    try:
        environment = make_jinja_environment(shared_root)
        result = environment.from_string(protected).render(variables or {})
    except TemplateError as exc:
        raise TemplateRenderError(str(exc)) from exc
    return result.replace(
        SKILL_DIR_REWRITE_ESCAPE_PLACEHOLDER, SKILL_DIR_REWRITE_ESCAPE_DIRECTIVE
    )


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


# ---------------------------------------------------------------------------
# Stage 5: Build orchestration
# ---------------------------------------------------------------------------


def emit_skill(
    src_path: Path,
    *,
    target: _Target,
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
    raw_text = src_path.read_text(encoding="utf-8")
    rendered = render_text(
        raw_text,
        shared_root=shared_root,
        variables=_render_variables(target),
    )
    translated = rewrite_paths_for_target(rendered, target=target)
    if target is _Target.CODEX:
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
        raw_source=raw_text,
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

    for target in _Target:
        target_root = dist_root / target.value
        if target_root.exists():
            shutil.rmtree(target_root)
        target_root.mkdir(parents=True, exist_ok=True)

    for source_file in _iter_plugin_files(plugins_root):
        for target in _Target:
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


def _make_kind_global(kind: str) -> Callable[..., str]:
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
        return resolve_runtime_token(kind, capability, resolved)

    return render


def make_jinja_environment(shared_root: Path | None = None) -> Environment:
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
    for kind in RUNTIME_TOKEN_REGISTRY:
        environment.globals[kind] = _make_kind_global(kind)
    return environment


def _render_directives(
    template: str,
    *,
    shared_root: Path | None,
    include_stack: tuple[Path, ...],
) -> str:
    def replace(match: re.Match[str]) -> str:
        body = " ".join(match.group(1).split())
        body_match = _DIRECTIVE_BODY_RE.match(body)
        if body_match is None:
            if _is_jinja_control_block(body):
                # A Jinja block statement sharing the block delimiter — leave it
                # for Jinja to evaluate during render.
                return match.group(0)
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
    return path.suffix in _TEXT_FILE_SUFFIXES


def _emit_rendered_file(
    source_file: Path,
    *,
    target: _Target,
    dist_root: Path,
    shared_root: Path,
) -> None:
    destination = dist_root / target.value / _relative_plugin_path(source_file)
    raw_text = source_file.read_text(encoding="utf-8")
    rendered = render_text(
        raw_text,
        shared_root=shared_root,
        variables=_render_variables(target),
    )
    translated = rewrite_paths_for_target(rendered, target=target)
    if target is _Target.CODEX:
        translated = strip_frontmatter_fields(
            translated,
            fields=CLAUDE_ONLY_FRONTMATTER_FIELDS,
        )
    _write_text(destination, translated)
    shutil.copymode(source_file, destination)
    _fan_out_shared_references(
        source_file,
        destination,
        shared_root=shared_root,
        raw_source=raw_text,
    )


def _copy_unrendered_file(
    source_file: Path, *, target: _Target, dist_root: Path
) -> None:
    destination = dist_root / target.value / _relative_plugin_path(source_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_file, destination)


def _run_formatter(command: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
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
    formatter = formatter_probe(FORMATTER_COMMAND_NAME)
    if formatter is None:
        raise BuildError(
            f"{FORMATTER_COMMAND_NAME} is required to format generated dist output"
        )
    file_pattern = str(dist_root / FORMATTER_FILE_GLOB)
    result = runner((formatter, "fmt", "--allow-no-files", file_pattern))
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise BuildError(f"dprint failed while formatting dist: {details}")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _iter_plugin_files(plugins_root: Path) -> tuple[Path, ...]:
    roots = (
        plugin_root / subdir
        for plugin_root in plugins_root.iterdir()
        if plugin_root.is_dir()
        for subdir in sorted(PLUGIN_SUBDIRS)
    )
    return tuple(
        sorted(
            path
            for root in roots
            if root.is_dir()
            for path in root.rglob("*")
            if path.is_file()
        )
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


def _fan_out_shared_references(
    source_file: Path,
    destination: Path,
    *,
    shared_root: Path,
    raw_source: str,
) -> None:
    if SKILLS_SUBDIR_NAME not in source_file.parts:
        return
    for directive in parse_directives(raw_source):
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
