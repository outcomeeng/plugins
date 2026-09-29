"""Authored-source and eval fixtures for native configuration rejection."""

from collections.abc import Iterable
from contextlib import redirect_stdout
from dataclasses import dataclass
from enum import StrEnum
from io import StringIO
from pathlib import Path

from outcomeeng.distribution.agents import (
    AGENT_DESCRIPTION_FIELD,
    AGENT_NAME_FIELD,
    parse_agent_markdown,
)
from outcomeeng.distribution.build import SHARED_DIR_NAME, TEMPLATES_DIR_NAME
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    DIST_DIR_NAME,
    FRONTMATTER_DELIMITER,
    MARKDOWN_FILE_SUFFIX,
    PLUGINS_DIR_NAME,
    PROFILE_DESCRIPTION_GLOBAL,
    SKILL_DESCRIPTION_FIELD,
    SKILL_FILENAME,
    SKILL_NAME_FIELD,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
    format_target_conditional,
    format_template_call,
)
from outcomeeng.distribution.profiles import NATIVE_CONFIGURATION_FIELDS, ProfileSyntax
from outcomeeng.models import AgentProfile
from outcomeeng.spec_tree_structure import (
    MIN_NODE_INDEX,
    NodeKind,
    format_node_directory_name,
)
from outcomeeng.validation._steps import EVALS_ROOT
from outcomeeng.validation.link_integrity import EVALS_DIRNAME
from outcomeeng.validation.profile_configuration import CONFIGURATION_ONLY_OPTION
from outcomeeng.validation.runtime_tokens import main
from outcomeeng_evals.definition import EVAL_TOML_FILENAME, PROFILE_FIELD, PROMPT_FIELD
from outcomeeng_evals.producer_prompt import (
    MATERIALIZED_PROMPT_FILENAME,
    PROMPT_SOURCE_TABLE,
    TEMPLATE_FIELD,
)
from outcomeeng_testing.generators.profile_configuration import (
    assignment_text,
    model_literals,
    native_field_assignments,
    token_document,
)
from outcomeeng_testing.harnesses.agent_conversion import (
    AGENT_CONVERSION_FIXTURES_DIR,
    DUPLICATE_REVIEWER_FIXTURE,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

# The inert whole-agent payload a profile build varies one frontmatter field of;
# its file also stands as the generated output the build must leave untouched.
_PROFILE_BUILD_FIXTURE = AGENT_CONVERSION_FIXTURES_DIR / DUPLICATE_REVIEWER_FIXTURE

# Disposable layout the harness owns: one eval rule directory under one node.
_EVAL_NODE_SLUG = "profile-guard"
_EVAL_RULE_DIRECTORY = "model-literal"
_TOML_COMMENT_PREFIX = "# "

_AUTHORED_SOURCE_DIRECTORIES = tuple(
    Path(SOURCE_ROOT_NAME) / directory
    for directory in (SHARED_DIR_NAME, PLUGINS_DIR_NAME, TEMPLATES_DIR_NAME)
)


@dataclass(frozen=True)
class PlacedLiteral:
    """One model literal or native assignment a fixture wrote, and where."""

    path: Path
    line: int
    token: str


@dataclass(frozen=True)
class ConfigurationOverrides:
    """Authored files carrying native overrides, and every override they place."""

    paths: tuple[Path, ...]
    placed: tuple[PlacedLiteral, ...]


@dataclass(frozen=True)
class EvalConfigurationOverrides:
    """An eval definition and its declared prompt templates, each naming models."""

    spec_root: Path
    definition: Path
    prompt: Path
    template: Path
    placed: tuple[PlacedLiteral, ...]


@dataclass(frozen=True)
class ConfigurationGuardRun:
    """The guard command's exit code and report for configuration-only files."""

    exit_code: int
    output: str


def _write_lines(
    path: Path, entries: Iterable[tuple[str, Iterable[str]]]
) -> tuple[PlacedLiteral, ...]:
    """Write one line per entry and return where each entry's tokens landed."""
    document = token_document(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(document.text, encoding="utf-8")
    return tuple(
        PlacedLiteral(path=path, line=placed.line, token=placed.token)
        for placed in document.placed
    )


def _conditional_entries(
    target: Target, field: str
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Every generated assignment of ``field`` inside one target's conditional."""
    tokens_by_line = {
        assignment.text: assignment.tokens
        for assignment in native_field_assignments()
        if assignment.field == field
    }
    conditional = format_target_conditional(target, "\n".join(tokens_by_line))
    return tuple(
        (line, tokens_by_line.get(line, ())) for line in conditional.splitlines()
    )


def write_configuration_overrides(root: Path) -> ConfigurationOverrides:
    """Place native overrides inside every harness conditional and skill frontmatter.

    Each authored-source directory receives one skill per harness and native
    field whose frontmatter requests the field through a profile template and
    whose body assigns it, in every syntax and admitted value, inside that
    harness's conditional.
    """
    request = format_template_call(PROFILE_DESCRIPTION_GLOBAL, AgentProfile.STANDARD)
    paths: list[Path] = []
    placed: list[PlacedLiteral] = []
    for directory in _AUTHORED_SOURCE_DIRECTORIES:
        for target in Target:
            for field in sorted(NATIVE_CONFIGURATION_FIELDS):
                path = root / directory / target.value / field / SKILL_FILENAME
                placed.extend(
                    _write_lines(
                        path,
                        (
                            (FRONTMATTER_DELIMITER, ()),
                            (
                                assignment_text(ProfileSyntax.YAML, field, request),
                                (field,),
                            ),
                            (FRONTMATTER_DELIMITER, ()),
                            *_conditional_entries(target, field),
                        ),
                    )
                )
                paths.append(path)
    return ConfigurationOverrides(paths=tuple(paths), placed=tuple(placed))


class AuthoredDefinition(StrEnum):
    """The authored definitions whose frontmatter a profile build rejects.

    Each value is the plugin subdirectory that holds that kind of definition.
    """

    AGENT = AGENTS_SUBDIR_NAME
    SKILL = SKILLS_SUBDIR_NAME


def prepare_profile_build(
    root: Path,
    field: str,
    value: str,
    *,
    definition: AuthoredDefinition = AuthoredDefinition.AGENT,
) -> tuple[Path, Path]:
    """Materialize one authored frontmatter field beside existing generated state.

    The definition takes its name, description, and body from the inert agent
    fixture, whose stem names the plugin and whose file stands as existing
    generated output. ``value`` is written as a quoted scalar exactly as given,
    so a build template request inside it renders during the build like any
    authored template value.
    """
    source = parse_agent_markdown(_PROFILE_BUILD_FIXTURE)
    name_field, description_field = {
        AuthoredDefinition.AGENT: (AGENT_NAME_FIELD, AGENT_DESCRIPTION_FIELD),
        AuthoredDefinition.SKILL: (SKILL_NAME_FIELD, SKILL_DESCRIPTION_FIELD),
    }[definition]
    content = token_document(
        (
            (FRONTMATTER_DELIMITER, ()),
            *(
                (assignment_text(ProfileSyntax.YAML, key, entry), ())
                for key, entry in (
                    (name_field, source.name),
                    (description_field, source.description),
                    (field, value),
                )
            ),
            (FRONTMATTER_DELIMITER, ()),
            (source.body, ()),
        )
    ).text
    definitions = {source.name: content}
    builder = SrcTreeBuilder(root)
    builder.add_plugin(
        _PROFILE_BUILD_FIXTURE.stem,
        skills=definitions if definition is AuthoredDefinition.SKILL else None,
        agents=definitions if definition is AuthoredDefinition.AGENT else None,
    )
    dist_root = root / DIST_DIR_NAME
    existing = dist_root / Target.CLAUDE.value / _PROFILE_BUILD_FIXTURE.name
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(_PROFILE_BUILD_FIXTURE.read_bytes())
    return builder.src_root, dist_root


def _prompt_entries() -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Prose naming each model literal, then every generated native assignment."""
    return (
        *(
            (f"Select {literal} for this review", (literal,))
            for literal in model_literals()
        ),
        *(
            (assignment.text, assignment.tokens)
            for assignment in native_field_assignments()
        ),
    )


def write_eval_configuration_overrides(root: Path) -> EvalConfigurationOverrides:
    """Place model literals and native assignments in an eval and its prompt templates.

    The definition selects a profile, which the guard passes, beside a native
    assignment for every configuration field and a comment naming every model
    literal; the authored prompt and the producer-coupled template name every
    model literal in prose and assign every native field in every syntax.
    """
    spec_root = root / EVALS_ROOT
    eval_directory = (
        spec_root
        / format_node_directory_name(MIN_NODE_INDEX, _EVAL_NODE_SLUG, NodeKind.ENABLER)
        / EVALS_DIRNAME
        / _EVAL_RULE_DIRECTORY
    )
    definition = eval_directory / EVAL_TOML_FILENAME
    prompt = eval_directory / MATERIALIZED_PROMPT_FILENAME
    template = eval_directory / f"{TEMPLATE_FIELD}{MARKDOWN_FILE_SUFFIX}"
    toml = ProfileSyntax.TOML
    definition_entries: tuple[tuple[str, tuple[str, ...]], ...] = (
        (assignment_text(toml, PROMPT_FIELD, prompt.name), ()),
        (assignment_text(toml, PROFILE_FIELD, AgentProfile.STANDARD), ()),
        *(
            (assignment_text(toml, field, AgentProfile.STANDARD), (field,))
            for field in sorted(NATIVE_CONFIGURATION_FIELDS)
        ),
        *(
            (f"{_TOML_COMMENT_PREFIX}{literal}", (literal,))
            for literal in model_literals()
        ),
        (f"[{PROMPT_SOURCE_TABLE}]", ()),
        (assignment_text(toml, TEMPLATE_FIELD, template.name), ()),
    )
    placed = (
        *_write_lines(definition, definition_entries),
        *_write_lines(prompt, _prompt_entries()),
        *_write_lines(template, _prompt_entries()),
    )
    return EvalConfigurationOverrides(
        spec_root=spec_root,
        definition=definition,
        prompt=prompt,
        template=template,
        placed=placed,
    )


def run_configuration_guard(paths: tuple[Path, ...]) -> ConfigurationGuardRun:
    """Run the guard command over ``paths`` as configuration-only arguments."""
    output = StringIO()
    with redirect_stdout(output):
        exit_code = main([CONFIGURATION_ONLY_OPTION, *(str(path) for path in paths)])
    return ConfigurationGuardRun(exit_code=exit_code, output=output.getvalue())
