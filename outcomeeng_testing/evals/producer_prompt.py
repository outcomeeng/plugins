"""Workspace and observation infrastructure for producer-prompt evidence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from click.testing import CliRunner, Result
from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng_evals.cli import main
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    MATERIALIZED_PROMPT_FILENAME,
    PRODUCER_FIELD,
    PRODUCER_FILE_KIND,
    PRODUCER_SECTION_KIND,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
    materialize_prompt,
)

PROMPT_FILENAME = MATERIALIZED_PROMPT_FILENAME
PROMPT_TEMPLATE_FILENAME = "prompt.template.md"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCER_SOURCE_PATHS = tuple(
    sorted(PROJECT_ROOT.glob("dist/claude/*/skills/audit*tests/SKILL.md"))
)
PRODUCER_RELATIVE_PATHS = tuple(
    path.relative_to(PROJECT_ROOT).as_posix() for path in PRODUCER_SOURCE_PATHS
)
LITERAL_PRODUCER_SECTION_TOKEN = "{producer_section}"
PROPERTY_SEED = 20260706
PROPERTY_EXAMPLES = 30
NONCANONICAL_PROMPT_SEED = 20260711
SECTION_TOKEN_SUFFIXES = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")),
    min_size=1,
    max_size=32,
)
SECTION_BODY_TEXT = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cc", "Cs"),
        blacklist_characters=["<", ">", "\x00"],
    ),
    min_size=1,
    max_size=80,
)
NONCANONICAL_PROMPT_FILENAMES = st.from_regex(
    r"[a-z][a-z0-9_-]{0,20}\.md",
    fullmatch=True,
).filter(lambda value: value != MATERIALIZED_PROMPT_FILENAME)


class ProducerMutation(StrEnum):
    NONE = "none"
    MISSING_SECTION = "missing-section"
    DUPLICATE_SECTION = "duplicate-section"
    SIMILAR_ATTRIBUTES = "similar-attributes"
    NON_STEP_TAG = "non-step-tag"
    LITERAL_CLOSING_DELIMITER = "literal-closing-delimiter"
    NESTED_STEP = "nested-step"
    PLACEHOLDER_TEXT = "placeholder-text"


@dataclass(frozen=True)
class ProducerCase:
    relative_path: str
    section_name: str


@dataclass(frozen=True)
class ProducerWorkspace:
    repo_root: Path
    eval_toml: Path
    producer_path: Path
    prompt_path: Path
    case: ProducerCase


@dataclass(frozen=True)
class MaterializedProducer:
    case: ProducerCase
    producer_text: str
    selected_section: str
    prompt_text: str


@dataclass(frozen=True)
class SectionMutationObservation:
    original_prompt: str
    unrelated_prompt: str
    selected_prompt: str
    original_token: str
    updated_token: str


@dataclass(frozen=True)
class CliMaterializationObservation:
    write_result: Result
    check_result: Result
    stale_result: Result
    prompt_path: Path
    materialized_prompt: str
    materialized_mtime_ns: int
    stale_prompt: str
    stale_mtime_ns: int


def producer_cases() -> tuple[ProducerCase, ...]:
    """Return runtime producers that expose at least one named step section."""
    cases: list[ProducerCase] = []
    for relative_path, source_path in zip(
        PRODUCER_RELATIVE_PATHS,
        PRODUCER_SOURCE_PATHS,
        strict=True,
    ):
        source = source_path.read_text(encoding="utf-8")
        section_name = first_named_step(source)
        if section_name is not None:
            cases.append(ProducerCase(relative_path, section_name))
    return tuple(cases)


def first_named_step(source: str) -> str | None:
    """Read the first exact ``<step name=...>`` opening from runtime text."""
    marker = '<step name="'
    start = source.find(marker)
    if start < 0:
        return None
    name_start = start + len(marker)
    name_end = source.find('"', name_start)
    if name_end < 0:
        return None
    return source[name_start:name_end]


def selected_section_text(source: str, section_name: str) -> str:
    """Extract one runtime step with a deliberately simple independent oracle."""
    opening = f'<step name="{section_name}">'
    start = source.index(opening)
    end = source.index("</step>", start) + len("</step>")
    return source[start:end]


def write_eval_workspace(
    tmp_path: Path,
    *,
    case: ProducerCase | None = None,
    prompt_source_kind: str = PRODUCER_SECTION_KIND,
    prompt_path: str = PROMPT_FILENAME,
    prompt_template_path: str = PROMPT_TEMPLATE_FILENAME,
    producer_relative_path: str | None = None,
    section_name: str | None = None,
    include_section: bool = True,
    omitted_fields: tuple[str, ...] = (),
    mutation: ProducerMutation = ProducerMutation.NONE,
) -> ProducerWorkspace:
    """Create an isolated eval workspace from shipped runtime producer files."""
    selected_case = case or first_producer_case()
    repo_root = tmp_path / "repo"
    eval_dir = repo_root / "spx" / "node" / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    copy_runtime_producer_corpus(repo_root)

    selected_relative_path = producer_relative_path or selected_case.relative_path
    producer_path = repo_root / selected_case.relative_path
    if mutation is not ProducerMutation.NONE:
        producer_path.write_text(
            mutate_runtime_producer(
                producer_path.read_text(encoding="utf-8"),
                selected_case.section_name,
                mutation,
            ),
            encoding="utf-8",
        )

    template_text = (
        "Producer: {producer_path}\n\n{producer_file}\n"
        if prompt_source_kind == PRODUCER_FILE_KIND
        else "Producer: {producer_path}\nSection: {producer_section_name}\n\n"
        "{producer_section}\n"
    )
    (eval_dir / prompt_template_path).write_text(template_text, encoding="utf-8")
    write_prompt_source_definition(
        eval_dir / EVAL_TOML_FILENAME,
        prompt_source_kind=prompt_source_kind,
        producer_relative_path=selected_relative_path,
        section_name=section_name or selected_case.section_name,
        prompt_path=prompt_path,
        prompt_template_path=prompt_template_path,
        include_section=include_section,
        omitted_fields=omitted_fields,
    )
    (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
    return ProducerWorkspace(
        repo_root=repo_root,
        eval_toml=eval_dir / EVAL_TOML_FILENAME,
        producer_path=producer_path,
        prompt_path=eval_dir / PROMPT_FILENAME,
        case=selected_case,
    )


def first_producer_case() -> ProducerCase:
    """Return one source-derived section case or report an unusable runtime corpus."""
    cases = producer_cases()
    if not cases:
        raise RuntimeError(
            "runtime audit-test producer corpus has no named step sections"
        )
    return cases[0]


def copy_runtime_producer_corpus(repo_root: Path) -> None:
    """Copy all shipped audit-test skills with repository-relative paths intact."""
    if not PRODUCER_SOURCE_PATHS:
        raise RuntimeError("runtime audit-test producer corpus is empty")
    for source_path, relative_path in zip(
        PRODUCER_SOURCE_PATHS,
        PRODUCER_RELATIVE_PATHS,
        strict=True,
    ):
        destination = repo_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(source_path, destination)


def materialize_runtime_files(tmp_path: Path) -> tuple[MaterializedProducer, ...]:
    """Materialize every shipped audit-test skill as a whole-file producer."""
    observations: list[MaterializedProducer] = []
    for index, relative_path in enumerate(PRODUCER_RELATIVE_PATHS):
        case = ProducerCase(relative_path, first_producer_case().section_name)
        workspace = write_eval_workspace(
            tmp_path / f"producer-{index}",
            case=case,
            prompt_source_kind=PRODUCER_FILE_KIND,
            include_section=False,
        )
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        producer_text = workspace.producer_path.read_text(encoding="utf-8")
        observations.append(
            MaterializedProducer(
                case=case,
                producer_text=producer_text,
                selected_section="",
                prompt_text=workspace.prompt_path.read_text(encoding="utf-8"),
            )
        )
    return tuple(observations)


def materialize_runtime_sections(tmp_path: Path) -> tuple[MaterializedProducer, ...]:
    """Materialize one source-derived named section from each eligible producer."""
    observations: list[MaterializedProducer] = []
    for index, case in enumerate(producer_cases()):
        workspace = write_eval_workspace(tmp_path / f"section-{index}", case=case)
        producer_text = workspace.producer_path.read_text(encoding="utf-8")
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        observations.append(
            MaterializedProducer(
                case=case,
                producer_text=producer_text,
                selected_section=selected_section_text(
                    producer_text, case.section_name
                ),
                prompt_text=workspace.prompt_path.read_text(encoding="utf-8"),
            )
        )
    return tuple(observations)


def mutate_runtime_producer(
    source: str,
    section_name: str,
    mutation: ProducerMutation,
) -> str:
    """Apply one contract-derived mutation to a copied runtime producer."""
    section = selected_section_text(source, section_name)
    opening = f'<step name="{section_name}">'
    body = section.removeprefix(opening).removesuffix("</step>")
    replacements = {
        ProducerMutation.MISSING_SECTION: section.replace(
            opening,
            '<step name="missing-runtime-section">',
            1,
        ),
        ProducerMutation.DUPLICATE_SECTION: f"{section}\n{section}",
        ProducerMutation.SIMILAR_ATTRIBUTES: section.replace(
            opening,
            f'<step data-name="{section_name}" noname="{section_name}">',
            1,
        ),
        ProducerMutation.NON_STEP_TAG: section.replace(
            opening, f'<example name="{section_name}">', 1
        ).replace(
            "</step>",
            "</example>",
            1,
        ),
        ProducerMutation.LITERAL_CLOSING_DELIMITER: f"{opening}{body}literal </step> delimiter\n</step>",
        ProducerMutation.NESTED_STEP: f'{opening}{body}<step name="nested_step">Nested body.</step>\n</step>',
        ProducerMutation.PLACEHOLDER_TEXT: f"{opening}\n{LITERAL_PRODUCER_SECTION_TOKEN}\n</step>",
    }
    replacement = replacements.get(mutation)
    if replacement is None:
        return source
    return source.replace(section, replacement, 1)


def write_prompt_source_definition(
    eval_toml: Path,
    *,
    prompt_source_kind: str,
    producer_relative_path: str,
    section_name: str,
    prompt_path: str,
    prompt_template_path: str,
    include_section: bool,
    omitted_fields: tuple[str, ...],
) -> None:
    """Write one eval definition from source-owned prompt field names."""
    prompt_source_lines = [
        f'{KIND_FIELD} = "{prompt_source_kind}"',
        f'{PRODUCER_FIELD} = "{producer_relative_path}"',
    ]
    if include_section:
        prompt_source_lines.append(f'{SECTION_FIELD} = "{section_name}"')
    prompt_source_lines.append(f'{TEMPLATE_FIELD} = "{prompt_template_path}"')
    omitted = set(omitted_fields)
    eval_toml.write_text(
        "\n".join(
            [
                'title = "producer prompt"',
                'cases = "cases.jsonl"',
                f'prompt = "{prompt_path}"',
                "",
                f"[{PROMPT_SOURCE_TABLE}]",
                *[
                    line
                    for line in prompt_source_lines
                    if line.split(" = ", 1)[0] not in omitted
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )


def cli_materialization_observation(tmp_path: Path) -> CliMaterializationObservation:
    """Run write, current-check, and stale-check CLI paths and return observations."""
    workspace = write_eval_workspace(tmp_path)
    runner = CliRunner()
    command = [
        "materialize-prompts",
        str(workspace.eval_toml.parent),
        "--repo-root",
        str(workspace.repo_root),
    ]
    write_result = runner.invoke(main, command)
    materialized_prompt = workspace.prompt_path.read_text(encoding="utf-8")
    materialized_mtime_ns = workspace.prompt_path.stat().st_mtime_ns
    check_result = runner.invoke(main, [*command, "--check"])
    stale_prompt = f"{materialized_prompt}\nstale\n"
    workspace.prompt_path.write_text(stale_prompt, encoding="utf-8")
    stale_mtime_ns = workspace.prompt_path.stat().st_mtime_ns
    stale_result = runner.invoke(main, [*command, "--check"])
    return CliMaterializationObservation(
        write_result=write_result,
        check_result=check_result,
        stale_result=stale_result,
        prompt_path=workspace.prompt_path,
        materialized_prompt=materialized_prompt,
        materialized_mtime_ns=materialized_mtime_ns,
        stale_prompt=stale_prompt,
        stale_mtime_ns=stale_mtime_ns,
    )


def nested_cli_results(tmp_path: Path) -> tuple[Result, Result, ProducerWorkspace]:
    """Run write and check from the evals ancestor rather than the rule directory."""
    workspace = write_eval_workspace(tmp_path)
    runner = CliRunner()
    command = [
        "materialize-prompts",
        str(workspace.repo_root / "spx" / "node" / "evals"),
        "--repo-root",
        str(workspace.repo_root),
    ]
    return (
        runner.invoke(main, command),
        runner.invoke(main, [*command, "--check"]),
        workspace,
    )


def run_section_mutation_property(
    predicate: Callable[[SectionMutationObservation], None],
) -> None:
    """Generate section mutations while leaving the predicate in the linked test."""

    @seed(PROPERTY_SEED)
    @settings(max_examples=PROPERTY_EXAMPLES)
    @given(
        token_suffix=SECTION_TOKEN_SUFFIXES,
        unrelated_body=SECTION_BODY_TEXT,
        updated_unrelated_body=SECTION_BODY_TEXT,
    )
    def exercise(
        token_suffix: str,
        unrelated_body: str,
        updated_unrelated_body: str,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = write_eval_workspace(Path(temp_dir))
            source = workspace.producer_path.read_text(encoding="utf-8")
            selected = selected_section_text(source, workspace.case.section_name)
            original_token = f"selected-token-{token_suffix}-end"
            updated_token = f"updated-token-{token_suffix}-end"
            selected_with_token = selected.replace(
                f'<step name="{workspace.case.section_name}">',
                f'<step name="{workspace.case.section_name}">\n{original_token}',
                1,
            )
            source_with_token = source.replace(selected, selected_with_token, 1)
            workspace.producer_path.write_text(
                f"{unrelated_body}\n{source_with_token}",
                encoding="utf-8",
            )
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
            original_prompt = workspace.prompt_path.read_text(encoding="utf-8")
            workspace.producer_path.write_text(
                f"{updated_unrelated_body}\n{source_with_token}",
                encoding="utf-8",
            )
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
            unrelated_prompt = workspace.prompt_path.read_text(encoding="utf-8")
            workspace.producer_path.write_text(
                f"{updated_unrelated_body}\n{source_with_token.replace(original_token, updated_token, 1)}",
                encoding="utf-8",
            )
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
            predicate(
                SectionMutationObservation(
                    original_prompt=original_prompt,
                    unrelated_prompt=unrelated_prompt,
                    selected_prompt=workspace.prompt_path.read_text(encoding="utf-8"),
                    original_token=original_token,
                    updated_token=updated_token,
                )
            )

    try:
        exercise()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {PROPERTY_SEED}")
        error.add_note(
            "Replay path: just test "
            "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
            "test_producer_prompt.property.l1.py"
        )
        raise


def run_noncanonical_prompt_property(
    predicate: Callable[[ProducerWorkspace, str], None],
) -> None:
    """Generate noncanonical prompt names and pass each workspace to the test."""

    @seed(NONCANONICAL_PROMPT_SEED)
    @settings(max_examples=PROPERTY_EXAMPLES)
    @given(prompt_path=NONCANONICAL_PROMPT_FILENAMES)
    def exercise(prompt_path: str) -> None:
        with TemporaryDirectory() as temp_dir:
            predicate(
                write_eval_workspace(Path(temp_dir), prompt_path=prompt_path),
                prompt_path,
            )

    try:
        exercise()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {NONCANONICAL_PROMPT_SEED}")
        error.add_note(
            "Replay path: just test "
            "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
            "test_producer_prompt.property.l1.py"
        )
        raise
