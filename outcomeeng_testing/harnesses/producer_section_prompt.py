"""Resource and generated-domain harnesses for section producer prompts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile, copytree
from tempfile import TemporaryDirectory

from click.testing import CliRunner, Result
from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng_evals.cli import main
from outcomeeng_evals.cli.commands.materialize_prompts import (
    materialize_prompts_command,
)
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
)

PROMPT_FILENAME = MATERIALIZED_PROMPT_FILENAME
PROMPT_TEMPLATE_FILENAME = "prompt.template.md"
PRODUCER_RELATIVE_PATH = "dist/claude/spec-tree/skills/audit-adr/SKILL.md"
COMPLETE_PRODUCER_FIXTURE_PATH = (
    Path(__file__).parent.parent / "fixtures" / "producer_prompt" / "base-skill.md"
)
SECTION_NAME = "audit_tag_validity"
SELECTED_RULE = "Evidence type must match the claim."
UNRELATED_RULE = "This surrounding section is not selected."
LITERAL_PRODUCER_SECTION_TOKEN = "{producer_section}"
STALE_PROMPT = "stale prompt\n"
PROMPT_PATH_OUTSIDE_EVAL_DIRECTORY = "../../prompt.md"
PRODUCER_PATH_OUTSIDE_REPOSITORY = "../outside/SKILL.md"
UNSUPPORTED_PROMPT_SOURCE_KIND = "simulation"
LITERAL_STEP_CLOSING_DELIMITER = "Literal </step> delimiter in prose."
NESTED_STEP_NAME = "nested_step"
NESTED_STEP_BODY = "Nested body."
PRODUCER_PROMPT_PROPERTY_SEED = 20260706
PRODUCER_PROMPT_PROPERTY_EXAMPLES = 30
NONCANONICAL_PROMPT_PROPERTY_SEED = 20260711
WHOLE_PRODUCER_PROPERTY_SEED = 20260717
PRODUCER_PROMPT_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
    "test_producer_prompt.property.l1.py::"
    "test_materialized_prompt_changes_only_with_selected_section"
)
NONCANONICAL_PROMPT_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
    "test_producer_prompt.property.l1.py::"
    "test_materialization_rejects_noncanonical_prompt_path"
)
WHOLE_PRODUCER_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
    "test_producer_prompt.property.l1.py::"
    "test_materialized_prompt_changes_with_single_producer_file"
)
RULE_TEXT = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cc", "Cs"),
        blacklist_characters=["<", ">", "\x00"],
    ),
    min_size=1,
    max_size=80,
)
RULE_TOKEN_SUFFIX = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"),
    ),
    min_size=1,
    max_size=32,
)
NONCANONICAL_PROMPT_FILENAMES = st.from_regex(
    r"[a-z][a-z0-9_-]{0,20}\.md",
    fullmatch=True,
).filter(lambda value: value != MATERIALIZED_PROMPT_FILENAME)


@dataclass(frozen=True)
class SelectedSectionMutation:
    """One generated mutation with harness-owned temporary storage."""

    tmp_path: Path
    rule_suffix: str
    unrelated_rule: str
    updated_unrelated_rule: str


@dataclass(frozen=True)
class NoncanonicalPromptPath:
    """One generated noncanonical prompt path with temporary storage."""

    tmp_path: Path
    prompt_path: str


@dataclass(frozen=True)
class WholeProducerMutation:
    """One generated whole-producer mutation with temporary storage."""

    tmp_path: Path
    suffix: str


def run_selected_section_change_property(
    assertion: Callable[[SelectedSectionMutation], None],
) -> None:
    """Run selected-section mutations through a test-owned predicate."""

    @seed(PRODUCER_PROMPT_PROPERTY_SEED)
    @settings(max_examples=PRODUCER_PROMPT_PROPERTY_EXAMPLES)
    @given(
        rule_suffix=RULE_TOKEN_SUFFIX,
        unrelated_rule=RULE_TEXT,
        updated_unrelated_rule=RULE_TEXT,
    )
    def generated_assertion(
        rule_suffix: str,
        unrelated_rule: str,
        updated_unrelated_rule: str,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            assertion(
                SelectedSectionMutation(
                    tmp_path=Path(temp_dir),
                    rule_suffix=rule_suffix,
                    unrelated_rule=unrelated_rule,
                    updated_unrelated_rule=updated_unrelated_rule,
                )
            )

    try:
        generated_assertion()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {PRODUCER_PROMPT_PROPERTY_SEED}")
        error.add_note(f"Replay path: {PRODUCER_PROMPT_PROPERTY_REPLAY_PATH}")
        raise


def run_noncanonical_prompt_path_property(
    assertion: Callable[[NoncanonicalPromptPath], None],
) -> None:
    """Run generated prompt paths through a test-owned predicate."""

    @seed(NONCANONICAL_PROMPT_PROPERTY_SEED)
    @settings(max_examples=PRODUCER_PROMPT_PROPERTY_EXAMPLES)
    @given(prompt_path=NONCANONICAL_PROMPT_FILENAMES)
    def generated_assertion(prompt_path: str) -> None:
        with TemporaryDirectory() as temp_dir:
            assertion(
                NoncanonicalPromptPath(
                    tmp_path=Path(temp_dir),
                    prompt_path=prompt_path,
                )
            )

    try:
        generated_assertion()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {NONCANONICAL_PROMPT_PROPERTY_SEED}")
        error.add_note(f"Replay path: {NONCANONICAL_PROMPT_PROPERTY_REPLAY_PATH}")
        raise


def run_whole_producer_change_property(
    assertion: Callable[[WholeProducerMutation], None],
) -> None:
    """Run whole-producer mutations through a test-owned predicate."""

    @seed(WHOLE_PRODUCER_PROPERTY_SEED)
    @settings(max_examples=PRODUCER_PROMPT_PROPERTY_EXAMPLES)
    @given(suffix=RULE_TEXT)
    def generated_assertion(suffix: str) -> None:
        with TemporaryDirectory() as temp_dir:
            assertion(
                WholeProducerMutation(
                    tmp_path=Path(temp_dir),
                    suffix=suffix,
                )
            )

    try:
        generated_assertion()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {WHOLE_PRODUCER_PROPERTY_SEED}")
        error.add_note(f"Replay path: {WHOLE_PRODUCER_PROPERTY_REPLAY_PATH}")
        raise


def invoke_materialize_prompts(
    eval_root: Path,
    *,
    repo_root: Path,
    check: bool,
) -> Result:
    """Invoke the source-owned materialize-prompts command."""
    command_name = materialize_prompts_command.name
    if command_name is None:
        raise RuntimeError("materialize-prompts command has no registered name")
    arguments = [
        command_name,
        str(eval_root),
        "--repo-root",
        str(repo_root),
    ]
    if check:
        arguments.append("--check")
    return CliRunner().invoke(main, arguments)


def write_eval_fixture(
    tmp_path: Path,
    *,
    section_name: str = SECTION_NAME,
    selected_rule: str = SELECTED_RULE,
    duplicate_section: bool = False,
    include_named_section: bool = True,
    include_false_positive_attributes: bool = False,
    include_non_step_named_tag: bool = False,
    prompt_source_kind: str = PRODUCER_SECTION_KIND,
    prompt_path: str = PROMPT_FILENAME,
    prompt_template_path: str = PROMPT_TEMPLATE_FILENAME,
    producer_relative_path: str = PRODUCER_RELATIVE_PATH,
    omitted_prompt_source_fields: tuple[str, ...] = (),
) -> tuple[Path, Path]:
    """Write one producer prompt eval into temporary repository storage."""
    repo_root = tmp_path / "repo"
    eval_dir = repo_root / "spx" / "node" / "evals" / "rule"
    producer_path = repo_root / PRODUCER_RELATIVE_PATH
    eval_dir.mkdir(parents=True)
    producer_path.parent.mkdir(parents=True)

    producer_sections = [producer_section("other_section", UNRELATED_RULE)]
    if include_false_positive_attributes:
        producer_sections.extend(
            [
                producer_section_with_attribute(
                    attribute_name="data-name",
                    attribute_value=SECTION_NAME,
                    body=UNRELATED_RULE,
                ),
                producer_section_with_attribute(
                    attribute_name="noname",
                    attribute_value=SECTION_NAME,
                    body=UNRELATED_RULE,
                ),
            ]
        )
    if include_non_step_named_tag:
        producer_sections.append(producer_example(SECTION_NAME, UNRELATED_RULE))
    if include_named_section:
        producer_sections.append(producer_section(SECTION_NAME, selected_rule))
    if duplicate_section:
        producer_sections.append(producer_section(SECTION_NAME, selected_rule))
    producer_path.write_text("\n".join(producer_sections), encoding="utf-8")

    if prompt_template_path == PROMPT_FILENAME:
        (eval_dir / PROMPT_FILENAME).write_text(
            "existing prompt\n",
            encoding="utf-8",
        )
    else:
        (eval_dir / prompt_template_path).write_text(
            "\n".join(
                [
                    "Producer: {producer_path}",
                    "Section: {producer_section_name}",
                    "",
                    "{producer_section}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    prompt_source_lines = [
        f'{KIND_FIELD} = "{prompt_source_kind}"',
        f'{PRODUCER_FIELD} = "{producer_relative_path}"',
        f'{SECTION_FIELD} = "{section_name}"',
        f'{TEMPLATE_FIELD} = "{prompt_template_path}"',
    ]
    omitted = set(omitted_prompt_source_fields)
    (eval_dir / EVAL_TOML_FILENAME).write_text(
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
    (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
    return repo_root, eval_dir / EVAL_TOML_FILENAME


def write_complete_producer_file_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Write one whole-producer eval into temporary repository storage."""
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_source_kind=PRODUCER_FILE_KIND,
    )
    copyfile(
        COMPLETE_PRODUCER_FIXTURE_PATH,
        repo_root / PRODUCER_RELATIVE_PATH,
    )
    (eval_toml.parent / PROMPT_TEMPLATE_FILENAME).write_text(
        "Producer: {producer_path}\n\n{producer_file}\n",
        encoding="utf-8",
    )
    write_prompt_source_definition(
        eval_toml,
        prompt_source_kind=PRODUCER_FILE_KIND,
        include_section=False,
    )
    return repo_root, eval_toml


def write_external_eval_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Write one eval outside the temporary repository boundary."""
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    external_eval_dir = tmp_path / "external" / "evals" / "rule"
    copytree(eval_toml.parent, external_eval_dir)
    return repo_root, external_eval_dir / EVAL_TOML_FILENAME


def write_prompt_source_definition(
    eval_toml: Path,
    *,
    prompt_source_kind: str,
    include_section: bool,
) -> None:
    """Replace one temporary eval's prompt-source definition."""
    prompt_source_lines = [
        f'{KIND_FIELD} = "{prompt_source_kind}"',
        f'{PRODUCER_FIELD} = "{PRODUCER_RELATIVE_PATH}"',
    ]
    if include_section:
        prompt_source_lines.append(f'{SECTION_FIELD} = "{SECTION_NAME}"')
    prompt_source_lines.append(f'{TEMPLATE_FIELD} = "{PROMPT_TEMPLATE_FILENAME}"')
    eval_toml.write_text(
        "\n".join(
            [
                'title = "producer prompt"',
                'cases = "cases.jsonl"',
                f'prompt = "{PROMPT_FILENAME}"',
                "",
                f"[{PROMPT_SOURCE_TABLE}]",
                *prompt_source_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )


def producer_section(name: str, body: str) -> str:
    """Render one synthetic step section."""
    return "\n".join(
        [
            f'<step name="{name}">',
            "",
            body,
            "",
            "</step>",
        ]
    )


def producer_section_with_attribute(
    *,
    attribute_name: str,
    attribute_value: str,
    body: str,
) -> str:
    """Render one synthetic step with a noncanonical attribute."""
    return "\n".join(
        [
            f'<step {attribute_name}="{attribute_value}">',
            "",
            body,
            "",
            "</step>",
        ]
    )


def producer_example(name: str, body: str) -> str:
    """Render one synthetic non-step named element."""
    return "\n".join(
        [
            f'<example name="{name}">',
            "",
            body,
            "",
            "</example>",
        ]
    )
