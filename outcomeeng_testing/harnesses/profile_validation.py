"""Authored-source and eval fixtures for native configuration rejection."""

from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
import json

from outcomeeng.distribution.contracts import (
    PROFILE_DESCRIPTION_GLOBAL,
    Target,
    format_target_conditional,
    format_template_call,
)
from outcomeeng.distribution.profiles import NATIVE_CONFIGURATION_FIELDS
from outcomeeng.models import CLAUDE_MODEL_FAMILIES, MODEL_IDENTIFIERS, AgentProfile
from outcomeeng.validation._steps import EVALS_ROOT
from outcomeeng.validation.link_integrity import EVALS_DIRNAME
from outcomeeng.validation.profile_configuration import CONFIGURATION_ONLY_OPTION
from outcomeeng.validation.runtime_tokens import main
from outcomeeng_evals.definition import EVAL_TOML_FILENAME, PROFILE_FIELD
from outcomeeng_evals.producer_prompt import (
    MATERIALIZED_PROMPT_FILENAME,
    PROMPT_FIELD,
    PROMPT_SOURCE_TABLE,
    TEMPLATE_FIELD,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

_EVAL_NODE_DIRECTORY = Path("10-profile-guard.enabler")
_EVAL_RULE_DIRECTORY = "model-literal"
_PROMPT_TEMPLATE_SUFFIX = ".template.md"

_AUTHORED_SOURCE_DIRECTORIES = (
    Path("src/_shared"),
    Path("src/plugins"),
    Path("src/templates"),
)


def write_configuration_overrides(root: Path) -> tuple[Path, ...]:
    """Place native overrides inside every harness conditional and skill frontmatter."""
    paths: list[Path] = []
    for directory in _AUTHORED_SOURCE_DIRECTORIES:
        for target in Target:
            for field in sorted(NATIVE_CONFIGURATION_FIELDS):
                path = root / directory / target.value / field / "SKILL.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                request = format_template_call(
                    PROFILE_DESCRIPTION_GLOBAL, AgentProfile.STANDARD
                )
                path.write_text(
                    "---\n"
                    + f"{field}: {json.dumps(request)}\n"
                    + "---\n"
                    + format_target_conditional(target, f'{field} = "value"')
                    + "\n",
                    encoding="utf-8",
                )
                paths.append(path)
    return tuple(paths)


def prepare_profile_build(
    root: Path, field: str, value: str, *, skill: bool = False
) -> tuple[Path, Path]:
    """Materialize one authored frontmatter field beside existing generated state.

    ``value`` is written as a quoted scalar exactly as given, so a build
    template request inside it renders during the build like any authored
    template value.
    """
    content = (
        "---\nname: reviewer\ndescription: Review.\n"
        + f"{field}: {json.dumps(value)}\n---\nReview.\n"
    )
    builder = SrcTreeBuilder(root)
    builder.add_plugin(
        "sample",
        skills={"reviewer": content} if skill else None,
        agents=None if skill else {"reviewer": content},
    )
    dist_root = root / "dist"
    existing = dist_root / "claude" / "sentinel.txt"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("Existing generated output.\n", encoding="utf-8")
    return builder.src_root, dist_root


@dataclass(frozen=True)
class PlacedLiteral:
    """One model literal or native assignment a fixture wrote, and where."""

    path: Path
    line: int
    token: str


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


def _model_literals() -> tuple[str, ...]:
    return tuple(sorted(MODEL_IDENTIFIERS | CLAUDE_MODEL_FAMILIES))


def _write_lines(
    path: Path,
    lines: list[tuple[str, str | None]],
) -> tuple[PlacedLiteral, ...]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{line}\n" for line, _ in lines), encoding="utf-8")
    return tuple(
        PlacedLiteral(path=path, line=number, token=token)
        for number, (_, token) in enumerate(lines, start=1)
        if token is not None
    )


def _prompt_lines() -> list[tuple[str, str | None]]:
    """Prose naming each model literal, then each native field set in place."""
    return [
        *(
            (f"Select {literal} for this review", literal)
            for literal in _model_literals()
        ),
        *(
            (f"{field}: {AgentProfile.STANDARD}", field)
            for field in sorted(NATIVE_CONFIGURATION_FIELDS)
        ),
    ]


def write_eval_configuration_overrides(root: Path) -> EvalConfigurationOverrides:
    """Place model literals and native assignments in an eval and its prompt templates.

    The definition selects a profile, which the guard passes, beside a native
    assignment for every configuration field and a comment naming every model
    literal; the authored prompt and the producer-coupled template name every
    model literal in prose and set every native field.
    """
    spec_root = root / EVALS_ROOT
    eval_directory = (
        spec_root / _EVAL_NODE_DIRECTORY / EVALS_DIRNAME / _EVAL_RULE_DIRECTORY
    )
    definition = eval_directory / EVAL_TOML_FILENAME
    prompt = eval_directory / MATERIALIZED_PROMPT_FILENAME
    template = prompt.with_suffix(_PROMPT_TEMPLATE_SUFFIX)
    definition_lines: list[tuple[str, str | None]] = [
        (f'{PROMPT_FIELD} = "{prompt.name}"', None),
        (f'{PROFILE_FIELD} = "{AgentProfile.STANDARD}"', None),
        *(
            (f'{field} = "{AgentProfile.STANDARD}"', field)
            for field in sorted(NATIVE_CONFIGURATION_FIELDS)
        ),
        *((f"# {literal}", literal) for literal in _model_literals()),
        (f"[{PROMPT_SOURCE_TABLE}]", None),
        (f'{TEMPLATE_FIELD} = "{template.name}"', None),
    ]
    placed = (
        *_write_lines(definition, definition_lines),
        *_write_lines(prompt, _prompt_lines()),
        *_write_lines(template, _prompt_lines()),
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
