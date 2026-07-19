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

from outcomeeng.distribution.contracts import DIST_DIR_NAME, Target
from outcomeeng_evals.cli import main
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    MATERIALIZED_PROMPT_FILENAME,
    PRODUCER_FIELD,
    PRODUCER_FILE_KIND,
    PRODUCER_FILE_PLACEHOLDER,
    PRODUCER_PATH_PLACEHOLDER,
    PRODUCER_SECTION_KIND,
    PRODUCER_SECTION_NAME_PLACEHOLDER,
    PRODUCER_SECTION_PLACEHOLDER,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
    ProducerPromptDefinition,
    load_producer_prompt_definition,
    materialize_prompt,
)

PROMPT_FILENAME = MATERIALIZED_PROMPT_FILENAME
PROMPT_TEMPLATE_FILENAME = "prompt.template.md"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCER_SOURCE_PATHS = tuple(
    sorted(
        producer_path
        for target in Target
        for producer_path in PROJECT_ROOT.glob(
            f"{DIST_DIR_NAME}/{target.value}/*/skills/audit*tests/SKILL.md"
        )
    )
)
PRODUCER_RELATIVE_PATHS = tuple(
    path.relative_to(PROJECT_ROOT).as_posix() for path in PRODUCER_SOURCE_PATHS
)
NESTED_STEP_NAME = "nested_step"
NESTED_STEP_BODY = "Nested body."
STALE_PROMPT_SUFFIX = "stale"
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
DISTINCT_SECTION_BODIES = st.tuples(SECTION_BODY_TEXT, SECTION_BODY_TEXT).filter(
    lambda bodies: bodies[0] != bodies[1]
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


class ProducerWorkspaceCase(StrEnum):
    """Rule-derived workspace configurations for compliance evidence."""

    DEFAULT = "default"
    PRODUCER_FILE_WITH_SECTION = "producer-file-with-section"
    PROMPT_OUTSIDE_EVAL = "prompt-outside-eval"
    TEMPLATE_ALIASES_PROMPT = "template-aliases-prompt"
    ABSOLUTE_TEMPLATE = "absolute-template"
    TEMPLATE_OUTSIDE_EVAL = "template-outside-eval"
    ABSOLUTE_PRODUCER = "absolute-producer"
    PRODUCER_OUTSIDE_REPO = "producer-outside-repo"
    PLACEHOLDER_TEXT = "placeholder-text"
    MISSING_SECTION = "missing-section"
    SIMILAR_ATTRIBUTES = "similar-attributes"
    NON_STEP_TAG = "non-step-tag"
    DUPLICATE_SECTION = "duplicate-section"
    LITERAL_CLOSING_DELIMITER = "literal-closing-delimiter"
    NESTED_STEP = "nested-step"
    UNSUPPORTED_KIND = "simulation"
    MISSING_KIND = "missing-kind"
    MISSING_PRODUCER = "missing-producer"
    MISSING_SECTION_FIELD = "missing-section-field"
    MISSING_TEMPLATE = "missing-template"
    VALID_PRODUCER_FILE = "valid-producer-file"


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
class CliMaterializedProducer:
    case: ProducerCase
    producer_text: str
    selected_section: str
    prompt_text: str
    result: Result


@dataclass(frozen=True)
class CliProducerWorkspaceObservation:
    case: ProducerWorkspaceCase
    workspace: ProducerWorkspace
    original_prompt: str | None
    result: Result


@dataclass(frozen=True)
class ShippedProducerEvalObservation:
    eval_toml: Path
    definition: ProducerPromptDefinition
    result: Result


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


@dataclass(frozen=True)
class NestedCliObservation:
    write_result: Result
    check_result: Result
    prompt_path: Path


def producer_cases() -> tuple[ProducerCase, ...]:
    """Return every named step section from every runtime producer."""
    cases: list[ProducerCase] = []
    for relative_path, source_path in zip(
        PRODUCER_RELATIVE_PATHS,
        PRODUCER_SOURCE_PATHS,
        strict=True,
    ):
        source = source_path.read_text(encoding="utf-8")
        for section_name in named_steps(source):
            cases.append(ProducerCase(relative_path, section_name))
    return tuple(cases)


def named_steps(source: str) -> tuple[str, ...]:
    """Read every exact ``<step name=...>`` opening from runtime text."""
    marker = '<step name="'
    names: list[str] = []
    cursor = 0
    while (start := source.find(marker, cursor)) >= 0:
        name_start = start + len(marker)
        name_end = source.find('"', name_start)
        if name_end < 0:
            break
        names.append(source[name_start:name_end])
        cursor = name_end + 1
    return tuple(names)


def first_named_step(source: str) -> str | None:
    """Read the first exact ``<step name=...>`` opening from runtime text."""
    return next(iter(named_steps(source)), None)


def selected_section_text(source: str, section_name: str) -> str:
    """Extract one runtime step with a deliberately simple independent oracle."""
    opening = f'<step name="{section_name}">'
    start = source.index(opening)
    end = source.index("</step>", start) + len("</step>")
    return source[start:end]


def sibling_section_text(source: str, section_name: str) -> str:
    """Return one independently named runtime section beside the selected one."""
    for sibling_name in named_steps(source):
        if sibling_name != section_name:
            return selected_section_text(source, sibling_name)
    raise RuntimeError(f"runtime producer section {section_name!r} has no sibling")


def section_with_body(section: str, body: str) -> str:
    """Replace a copied section's body while preserving its source-owned opening."""
    opening_end = section.index(">") + 1
    return f"{section[:opening_end]}\n{body}\n</step>"


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
        f"Producer: {PRODUCER_PATH_PLACEHOLDER}\n\n{PRODUCER_FILE_PLACEHOLDER}\n"
        if prompt_source_kind == PRODUCER_FILE_KIND
        else f"Producer: {PRODUCER_PATH_PLACEHOLDER}\n"
        f"Section: {PRODUCER_SECTION_NAME_PLACEHOLDER}\n\n"
        f"{PRODUCER_SECTION_PLACEHOLDER}\n"
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
        case = ProducerCase(relative_path, "")
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


def run_materialized_runtime_files(
    predicate: Callable[[tuple[MaterializedProducer, ...]], None],
) -> None:
    """Deliver the complete whole-file observation mapping to the linked test."""
    with TemporaryDirectory() as temp_dir:
        predicate(materialize_runtime_files(Path(temp_dir)))


def run_cli_materialized_runtime_sections(
    predicate: Callable[[CliMaterializedProducer], None],
) -> None:
    """Deliver every runtime section after the real CLI materializes it."""
    with TemporaryDirectory() as temp_dir:
        runner = CliRunner()
        for index, case in enumerate(producer_cases()):
            workspace = write_eval_workspace(
                Path(temp_dir) / f"section-{index}", case=case
            )
            producer_text = workspace.producer_path.read_text(encoding="utf-8")
            result = runner.invoke(main, _materialize_command(workspace))
            predicate(
                CliMaterializedProducer(
                    case=case,
                    producer_text=producer_text,
                    selected_section=selected_section_text(
                        producer_text,
                        case.section_name,
                    ),
                    prompt_text=(
                        workspace.prompt_path.read_text(encoding="utf-8")
                        if workspace.prompt_path.is_file()
                        else ""
                    ),
                    result=result,
                )
            )


def run_cli_shipped_producer_evals(
    predicate: Callable[[ShippedProducerEvalObservation], None],
) -> None:
    """Check every repository-owned producer-coupled eval through the real CLI."""
    runner = CliRunner()
    count = 0
    prompt_source_marker = f"[{PROMPT_SOURCE_TABLE}]"
    for eval_toml in sorted(PROJECT_ROOT.rglob(EVAL_TOML_FILENAME)):
        if prompt_source_marker not in eval_toml.read_text(encoding="utf-8"):
            continue
        count += 1
        definition = load_producer_prompt_definition(
            eval_toml,
            repo_root=PROJECT_ROOT,
        )
        predicate(
            ShippedProducerEvalObservation(
                eval_toml=eval_toml,
                definition=definition,
                result=runner.invoke(
                    main,
                    [
                        "materialize-prompts",
                        str(eval_toml.parent),
                        "--repo-root",
                        str(PROJECT_ROOT),
                        "--check",
                    ],
                ),
            )
        )
    if count == 0:
        raise RuntimeError("repository contains no producer-coupled eval definitions")


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
        ProducerMutation.NESTED_STEP: (
            f'{opening}{body}<step name="{NESTED_STEP_NAME}">'
            f"{NESTED_STEP_BODY}</step>\n</step>"
        ),
        ProducerMutation.PLACEHOLDER_TEXT: f"{opening}\n{PRODUCER_SECTION_PLACEHOLDER}\n</step>",
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
    command = _materialize_command(workspace)
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


def run_cli_materialization_mapping(
    predicate: Callable[[CliMaterializationObservation], None],
) -> None:
    """Deliver write/current/stale CLI observations to the linked test."""
    with TemporaryDirectory() as temp_dir:
        predicate(cli_materialization_observation(Path(temp_dir)))


def run_nested_cli_mapping(
    predicate: Callable[[NestedCliObservation], None],
) -> None:
    """Deliver nested-root CLI observations to the linked test."""
    with TemporaryDirectory() as temp_dir:
        write_result, check_result, workspace = nested_cli_results(Path(temp_dir))
        predicate(
            NestedCliObservation(
                write_result=write_result,
                check_result=check_result,
                prompt_path=workspace.prompt_path,
            )
        )


def run_cli_producer_workspace_contract(
    predicate: Callable[[CliProducerWorkspaceObservation], None],
) -> None:
    """Deliver every source-owned compliance case through the real CLI."""
    with TemporaryDirectory() as temp_dir:
        runner = CliRunner()
        root = Path(temp_dir)
        for index, case in enumerate(ProducerWorkspaceCase):
            workspace = _workspace_for_case(root / f"case-{index}", case)
            original_prompt = (
                workspace.prompt_path.read_text(encoding="utf-8")
                if workspace.prompt_path.is_file()
                else None
            )
            predicate(
                CliProducerWorkspaceObservation(
                    case=case,
                    workspace=workspace,
                    original_prompt=original_prompt,
                    result=runner.invoke(main, _materialize_command(workspace)),
                )
            )


def _materialize_command(workspace: ProducerWorkspace) -> list[str]:
    """Return the source-owned CLI invocation for one workspace."""
    return [
        "materialize-prompts",
        str(workspace.eval_toml.parent),
        "--repo-root",
        str(workspace.repo_root),
    ]


def _workspace_for_case(
    root: Path,
    case: ProducerWorkspaceCase,
) -> ProducerWorkspace:
    """Materialize one compliance-case workspace without encoding its verdict."""
    if case is ProducerWorkspaceCase.PRODUCER_FILE_WITH_SECTION:
        return write_eval_workspace(root, prompt_source_kind=PRODUCER_FILE_KIND)
    if case is ProducerWorkspaceCase.PROMPT_OUTSIDE_EVAL:
        return write_eval_workspace(root, prompt_path="../../prompt.md")
    if case is ProducerWorkspaceCase.TEMPLATE_ALIASES_PROMPT:
        return write_eval_workspace(
            root,
            prompt_template_path=MATERIALIZED_PROMPT_FILENAME,
        )
    if case is ProducerWorkspaceCase.ABSOLUTE_TEMPLATE:
        return write_eval_workspace(
            root,
            prompt_template_path=str(root.resolve() / PROMPT_TEMPLATE_FILENAME),
        )
    if case is ProducerWorkspaceCase.TEMPLATE_OUTSIDE_EVAL:
        return write_eval_workspace(
            root,
            prompt_template_path=f"../{PROMPT_TEMPLATE_FILENAME}",
        )
    if case is ProducerWorkspaceCase.ABSOLUTE_PRODUCER:
        return write_eval_workspace(root, producer_relative_path=str(root.resolve()))
    if case is ProducerWorkspaceCase.PRODUCER_OUTSIDE_REPO:
        return write_eval_workspace(
            root,
            producer_relative_path="../outside/SKILL.md",
        )
    mutation_by_case = {
        ProducerWorkspaceCase.PLACEHOLDER_TEXT: ProducerMutation.PLACEHOLDER_TEXT,
        ProducerWorkspaceCase.MISSING_SECTION: ProducerMutation.MISSING_SECTION,
        ProducerWorkspaceCase.SIMILAR_ATTRIBUTES: ProducerMutation.SIMILAR_ATTRIBUTES,
        ProducerWorkspaceCase.NON_STEP_TAG: ProducerMutation.NON_STEP_TAG,
        ProducerWorkspaceCase.DUPLICATE_SECTION: ProducerMutation.DUPLICATE_SECTION,
        ProducerWorkspaceCase.LITERAL_CLOSING_DELIMITER: ProducerMutation.LITERAL_CLOSING_DELIMITER,
        ProducerWorkspaceCase.NESTED_STEP: ProducerMutation.NESTED_STEP,
    }
    if case in mutation_by_case:
        return write_eval_workspace(root, mutation=mutation_by_case[case])
    if case is ProducerWorkspaceCase.UNSUPPORTED_KIND:
        return write_eval_workspace(root, prompt_source_kind="simulation")
    omitted_by_case = {
        ProducerWorkspaceCase.MISSING_KIND: KIND_FIELD,
        ProducerWorkspaceCase.MISSING_PRODUCER: PRODUCER_FIELD,
        ProducerWorkspaceCase.MISSING_SECTION_FIELD: SECTION_FIELD,
        ProducerWorkspaceCase.MISSING_TEMPLATE: TEMPLATE_FIELD,
    }
    if case in omitted_by_case:
        return write_eval_workspace(root, omitted_fields=(omitted_by_case[case],))
    if case is ProducerWorkspaceCase.VALID_PRODUCER_FILE:
        workspace = write_eval_workspace(root, prompt_source_kind=PRODUCER_FILE_KIND)
        write_prompt_source_definition(
            workspace.eval_toml,
            prompt_source_kind=PRODUCER_FILE_KIND,
            producer_relative_path=workspace.case.relative_path,
            section_name=workspace.case.section_name,
            prompt_path=PROMPT_FILENAME,
            prompt_template_path=PROMPT_TEMPLATE_FILENAME,
            include_section=False,
            omitted_fields=(),
        )
        return workspace
    return write_eval_workspace(root)


def run_section_mutation_property(
    predicate: Callable[[SectionMutationObservation], None],
) -> None:
    """Generate section mutations while leaving the predicate in the linked test."""
    cases = producer_cases()
    if not cases:
        raise RuntimeError("runtime audit-test producer corpus has no named sections")
    examples_per_case = max(1, PROPERTY_EXAMPLES // len(cases))

    for index, case in enumerate(cases):
        with TemporaryDirectory() as temp_dir:
            workspace = write_eval_workspace(
                Path(temp_dir) / f"section-{index}",
                case=case,
            )
            source = workspace.producer_path.read_text(encoding="utf-8")

            @seed(PROPERTY_SEED + index)
            @settings(max_examples=examples_per_case)
            @given(
                token_suffix=SECTION_TOKEN_SUFFIXES,
                unrelated_bodies=DISTINCT_SECTION_BODIES,
            )
            def exercise(
                token_suffix: str,
                unrelated_bodies: tuple[str, str],
            ) -> None:
                selected = selected_section_text(source, workspace.case.section_name)
                sibling = sibling_section_text(source, workspace.case.section_name)
                original_token = f"selected-token-{token_suffix}-end"
                updated_token = f"updated-token-{token_suffix}-end"
                selected_with_token = selected.replace(
                    f'<step name="{workspace.case.section_name}">',
                    f'<step name="{workspace.case.section_name}">\n{original_token}',
                    1,
                )
                source_with_token = source.replace(selected, selected_with_token, 1)
                original_sibling = section_with_body(sibling, unrelated_bodies[0])
                updated_sibling = section_with_body(sibling, unrelated_bodies[1])
                source_with_original_sibling = source_with_token.replace(
                    sibling,
                    original_sibling,
                    1,
                )
                workspace.producer_path.write_text(
                    source_with_original_sibling,
                    encoding="utf-8",
                )
                materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
                original_prompt = workspace.prompt_path.read_text(encoding="utf-8")
                source_with_updated_sibling = source_with_token.replace(
                    sibling,
                    updated_sibling,
                    1,
                )
                workspace.producer_path.write_text(
                    source_with_updated_sibling,
                    encoding="utf-8",
                )
                materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
                unrelated_prompt = workspace.prompt_path.read_text(encoding="utf-8")
                workspace.producer_path.write_text(
                    source_with_updated_sibling.replace(
                        original_token,
                        updated_token,
                        1,
                    ),
                    encoding="utf-8",
                )
                materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
                predicate(
                    SectionMutationObservation(
                        original_prompt=original_prompt,
                        unrelated_prompt=unrelated_prompt,
                        selected_prompt=workspace.prompt_path.read_text(
                            encoding="utf-8"
                        ),
                        original_token=original_token,
                        updated_token=updated_token,
                    )
                )

            try:
                exercise()
            except AssertionError as error:
                error.add_note(f"Producer: {case.relative_path}#{case.section_name}")
                error.add_note(f"Hypothesis seed: {PROPERTY_SEED + index}")
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
