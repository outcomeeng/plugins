"""Marketplace-owned fixtures for producer-derived prompt tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from click.testing import CliRunner
from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng_evals.cli import main
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    MATERIALIZED_PROMPT_FILENAME,
    PRODUCER_FIELD,
    PRODUCER_FILE_KIND,
    PRODUCER_FILES_KIND,
    PRODUCER_SECTION_KIND,
    PRODUCERS_FIELD,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
    PromptMaterializationDrift,
    ProducerPromptError,
    materialize_prompt,
    verify_materialized_prompt,
)
from outcomeeng_testing.harnesses.eval_workspaces import with_temp_workspace

PROMPT_FILENAME = MATERIALIZED_PROMPT_FILENAME
PROMPT_TEMPLATE_FILENAME = "prompt.template.md"
PRODUCER_RELATIVE_PATH = "dist/claude/spec-tree/skills/audit-adr/SKILL.md"
ADDITIONAL_PRODUCER_RELATIVE_PATH = (
    "dist/claude/spec-tree/skills/audit-adr/references/policy.md"
)
PRODUCER_FILES_RELATIVE_PATHS = (
    PRODUCER_RELATIVE_PATH,
    ADDITIONAL_PRODUCER_RELATIVE_PATH,
)
PRODUCER_FILE_CONTENTS = (
    "Primary complete producer.\n",
    "Additional complete producer.\n",
)
UPDATED_PRODUCER_SUFFIX = "Updated producer.\n"
MISSING_PRODUCER_RELATIVE_PATH = (
    "dist/claude/spec-tree/skills/audit-adr/references/absent.md"
)
SECTION_NAME = "audit_tag_validity"
SELECTED_RULE = "Evidence type must match the claim."
UNRELATED_RULE = "This surrounding section is not selected."
LITERAL_PRODUCER_SECTION_TOKEN = "{producer_section}"
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
PRODUCER_PROMPT_PROPERTY_SEED = 20260706
PRODUCER_PROMPT_PROPERTY_EXAMPLES = 30
NONCANONICAL_PROMPT_PROPERTY_SEED = 20260711
PRODUCER_PROMPT_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
    "test_producer_prompt.conformance.l1.py::"
    "test_materialized_prompt_changes_only_with_selected_section"
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


@with_temp_workspace
def assert_materializes_prompt_from_named_producer_section(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)

    materialize_prompt(eval_toml, repo_root=repo_root)

    prompt_text = (eval_toml.parent / PROMPT_FILENAME).read_text(encoding="utf-8")
    assert SELECTED_RULE in prompt_text
    assert UNRELATED_RULE not in prompt_text
    assert PRODUCER_RELATIVE_PATH in prompt_text
    assert SECTION_NAME in prompt_text


@with_temp_workspace
def assert_materializes_prompt_from_complete_producer_file(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_source_kind=PRODUCER_FILE_KIND,
    )
    eval_dir = eval_toml.parent
    producer_text = (repo_root / PRODUCER_RELATIVE_PATH).read_text(encoding="utf-8")
    (eval_dir / PROMPT_TEMPLATE_FILENAME).write_text(
        "Producer: {producer_path}\n\n{producer_file}\n",
        encoding="utf-8",
    )
    write_prompt_source_definition(
        eval_toml,
        prompt_source_kind=PRODUCER_FILE_KIND,
        include_section=False,
    )

    materialize_prompt(eval_toml, repo_root=repo_root)

    prompt_text = (eval_dir / PROMPT_FILENAME).read_text(encoding="utf-8")
    assert producer_text in prompt_text
    assert PRODUCER_RELATIVE_PATH in prompt_text


@with_temp_workspace
def assert_materializes_prompt_from_ordered_complete_producer_files(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = write_producer_files_fixture(tmp_path)

    first_render = materialize_prompt(eval_toml, repo_root=repo_root).read_text(
        encoding="utf-8"
    )
    materialize_prompt(eval_toml, repo_root=repo_root)
    second_render = (eval_toml.parent / PROMPT_FILENAME).read_text(encoding="utf-8")

    first_path_position = first_render.index(PRODUCER_FILES_RELATIVE_PATHS[0])
    first_content_position = first_render.index(PRODUCER_FILE_CONTENTS[0])
    second_path_position = first_render.index(PRODUCER_FILES_RELATIVE_PATHS[1])
    second_content_position = first_render.index(PRODUCER_FILE_CONTENTS[1])
    assert first_path_position < first_content_position
    assert first_content_position < second_path_position
    assert second_path_position < second_content_position
    assert all(first_render.count(path) == 2 for path in PRODUCER_FILES_RELATIVE_PATHS)
    assert second_render == first_render


@with_temp_workspace
def assert_producer_files_check_detects_each_source_change(tmp_path: Path) -> None:
    repo_root, eval_toml = write_producer_files_fixture(tmp_path)
    materialize_prompt(eval_toml, repo_root=repo_root)

    for producer_relative_path, original_content in zip(
        PRODUCER_FILES_RELATIVE_PATHS,
        PRODUCER_FILE_CONTENTS,
        strict=True,
    ):
        producer_path = repo_root / producer_relative_path
        producer_path.write_text(
            f"{original_content}{UPDATED_PRODUCER_SUFFIX}",
            encoding="utf-8",
        )
        with pytest.raises(PromptMaterializationDrift, match=PROMPT_FILENAME):
            verify_materialized_prompt(eval_toml, repo_root=repo_root)
        producer_path.write_text(original_content, encoding="utf-8")
        verify_materialized_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_invalid_producer_files_definitions_are_rejected(tmp_path: Path) -> None:
    invalid_definitions: tuple[tuple[object, bool, bool], ...] = (
        ([], False, False),
        ([PRODUCER_RELATIVE_PATH, PRODUCER_RELATIVE_PATH], False, False),
        ([PRODUCER_RELATIVE_PATH, f"./{PRODUCER_RELATIVE_PATH}"], False, False),
        ([MISSING_PRODUCER_RELATIVE_PATH], False, False),
        ([1], False, False),
        ([str((tmp_path / PRODUCER_RELATIVE_PATH).resolve())], False, False),
        (["../outside/SKILL.md"], False, False),
        (list(PRODUCER_FILES_RELATIVE_PATHS), True, False),
        (list(PRODUCER_FILES_RELATIVE_PATHS), False, True),
        (PRODUCER_RELATIVE_PATH, False, False),
    )
    for index, (producers, include_section, include_singular) in enumerate(
        invalid_definitions
    ):
        repo_root, eval_toml = write_producer_files_fixture(
            tmp_path / str(index),
            producers=producers,
            include_section=include_section,
            include_singular=include_singular,
        )
        with pytest.raises(ProducerPromptError, match=PRODUCERS_FIELD):
            materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_producer_file_rejects_section_selector(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_source_kind=PRODUCER_FILE_KIND,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_check_accepts_current_materialized_prompt(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    materialize_prompt(eval_toml, repo_root=repo_root)

    verify_materialized_prompt(eval_toml, repo_root=repo_root)


def assert_materialized_prompt_changes_only_with_selected_section() -> None:
    @seed(PRODUCER_PROMPT_PROPERTY_SEED)
    @settings(max_examples=PRODUCER_PROMPT_PROPERTY_EXAMPLES)
    @given(
        rule_suffix=RULE_TOKEN_SUFFIX,
        unrelated_rule=RULE_TEXT,
        updated_unrelated_rule=RULE_TEXT,
    )
    def assertion(
        rule_suffix: str,
        unrelated_rule: str,
        updated_unrelated_rule: str,
    ) -> None:
        materialized_prompt_changes_only_with_selected_section(
            rule_suffix=rule_suffix,
            unrelated_rule=unrelated_rule,
            updated_unrelated_rule=updated_unrelated_rule,
        )

    try:
        assertion()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {PRODUCER_PROMPT_PROPERTY_SEED}")
        error.add_note(f"Replay path: {PRODUCER_PROMPT_PROPERTY_REPLAY_PATH}")
        raise


def materialized_prompt_changes_only_with_selected_section(
    *,
    rule_suffix: str,
    unrelated_rule: str,
    updated_unrelated_rule: str,
) -> None:
    selected_rule = f"selected-token-{rule_suffix}-end"
    updated_selected_rule = f"updated-token-{rule_suffix}-end"
    with TemporaryDirectory() as temp_dir:
        repo_root, eval_toml = write_eval_fixture(Path(temp_dir))
        producer_path = repo_root / PRODUCER_RELATIVE_PATH
        prompt_path = eval_toml.parent / PROMPT_FILENAME
        producer_path.write_text(
            "\n".join(
                [
                    producer_section("other_section", unrelated_rule),
                    producer_section(SECTION_NAME, selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)
        original_prompt = prompt_path.read_text(encoding="utf-8")

        producer_path.write_text(
            "\n".join(
                [
                    producer_section("other_section", updated_unrelated_rule),
                    producer_section(SECTION_NAME, selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)

        assert prompt_path.read_text(encoding="utf-8") == original_prompt

        producer_path.write_text(
            "\n".join(
                [
                    producer_section("other_section", updated_unrelated_rule),
                    producer_section(SECTION_NAME, updated_selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)
        updated_prompt = prompt_path.read_text(encoding="utf-8")

        assert updated_prompt != original_prompt
        assert updated_selected_rule in updated_prompt
        assert selected_rule not in updated_prompt


@with_temp_workspace
def assert_check_rejects_stale_materialized_prompt(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    (eval_toml.parent / PROMPT_FILENAME).write_text("stale prompt\n", encoding="utf-8")

    with pytest.raises(PromptMaterializationDrift, match=PROMPT_FILENAME):
        verify_materialized_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_materialization_rejects_prompt_path_outside_eval_dir(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path, prompt_path="../../prompt.md")

    with pytest.raises(ProducerPromptError, match="prompt"):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_materialization_rejects_prompt_template_alias(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_template_path=PROMPT_FILENAME,
    )
    original_prompt = (eval_toml.parent / PROMPT_FILENAME).read_text(encoding="utf-8")

    with pytest.raises(ProducerPromptError, match=TEMPLATE_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)

    assert (eval_toml.parent / PROMPT_FILENAME).read_text(
        encoding="utf-8"
    ) == original_prompt


@with_temp_workspace
def assert_materialization_rejects_absolute_producer_path(tmp_path: Path) -> None:
    absolute_path = tmp_path / "repo" / PRODUCER_RELATIVE_PATH
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        producer_relative_path=str(absolute_path),
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_materialization_rejects_producer_path_outside_repo(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        producer_relative_path="../outside/SKILL.md",
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)
    assert repo_root.is_dir()


def assert_materialization_rejects_noncanonical_prompt_path() -> None:
    @seed(NONCANONICAL_PROMPT_PROPERTY_SEED)
    @settings(max_examples=PRODUCER_PROMPT_PROPERTY_EXAMPLES)
    @given(prompt_path=NONCANONICAL_PROMPT_FILENAMES)
    def assertion(prompt_path: str) -> None:
        materialization_rejects_noncanonical_prompt_path(prompt_path=prompt_path)

    try:
        assertion()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {NONCANONICAL_PROMPT_PROPERTY_SEED}")
        error.add_note(
            "Replay path: just test "
            "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
            "test_producer_prompt.conformance.l1.py::"
            "test_materialization_rejects_noncanonical_prompt_path"
        )
        raise


def materialization_rejects_noncanonical_prompt_path(
    *,
    prompt_path: str,
) -> None:
    with TemporaryDirectory() as tmp:
        repo_root, eval_toml = write_eval_fixture(
            Path(tmp),
            prompt_path=prompt_path,
        )

        with pytest.raises(
            ProducerPromptError,
            match=MATERIALIZED_PROMPT_FILENAME,
        ):
            materialize_prompt(eval_toml, repo_root=repo_root)
        assert not (eval_toml.parent / prompt_path).exists()


@with_temp_workspace
def assert_materialization_preserves_placeholder_text_inside_producer_section(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        selected_rule=LITERAL_PRODUCER_SECTION_TOKEN,
    )

    materialize_prompt(eval_toml, repo_root=repo_root)

    prompt_text = (eval_toml.parent / PROMPT_FILENAME).read_text(encoding="utf-8")
    assert prompt_text.count(LITERAL_PRODUCER_SECTION_TOKEN) == 1


@with_temp_workspace
def assert_missing_producer_section_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path, section_name="missing")

    with pytest.raises(ProducerPromptError, match="missing"):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_similar_attribute_names_do_not_match_section_name(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        include_named_section=False,
        include_false_positive_attributes=True,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_non_step_tags_do_not_match_section_name(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        include_named_section=False,
        include_non_step_named_tag=True,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_selected_section_rejects_literal_step_closing_delimiter(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        selected_rule="Literal </step> delimiter in prose.",
    )

    with pytest.raises(ProducerPromptError, match="step closing delimiter"):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_selected_section_preserves_nested_step_section(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        selected_rule=producer_section("nested_step", "Nested body."),
    )

    prompt_path = materialize_prompt(eval_toml, repo_root=repo_root)

    prompt = prompt_path.read_text(encoding="utf-8")
    assert f'name="{SECTION_NAME}"' in prompt
    assert 'name="nested_step"' in prompt
    assert "Nested body." in prompt


@with_temp_workspace
def assert_duplicate_producer_section_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path, duplicate_section=True)

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_unsupported_prompt_source_kind_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_source_kind="simulation",
    )

    with pytest.raises(ProducerPromptError, match="simulation"):
        materialize_prompt(eval_toml, repo_root=repo_root)


def assert_missing_prompt_source_fields_are_rejected(
    tmp_path: Path,
    omitted_field: str,
) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        omitted_prompt_source_fields=(omitted_field,),
    )

    with pytest.raises(ProducerPromptError, match=omitted_field):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def assert_required_prompt_source_fields_are_rejected_when_missing(
    tmp_path: Path,
) -> None:
    for omitted_field in (KIND_FIELD, PRODUCER_FIELD, SECTION_FIELD, TEMPLATE_FIELD):
        assert_missing_prompt_source_fields_are_rejected(
            tmp_path / omitted_field,
            omitted_field,
        )


@with_temp_workspace
def assert_cli_materializes_and_checks_prompt_drift(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    runner = CliRunner()

    write_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(eval_toml.parent),
            "--repo-root",
            str(repo_root),
        ],
    )

    assert write_result.exit_code == EXIT_SUCCESS
    assert PROMPT_FILENAME in write_result.output

    prompt_path = eval_toml.parent / PROMPT_FILENAME
    materialized_prompt = prompt_path.read_text(encoding="utf-8")
    materialized_mtime_ns = prompt_path.stat().st_mtime_ns

    check_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(eval_toml.parent),
            "--repo-root",
            str(repo_root),
            "--check",
        ],
    )

    assert check_result.exit_code == EXIT_SUCCESS
    assert prompt_path.read_text(encoding="utf-8") == materialized_prompt
    assert prompt_path.stat().st_mtime_ns == materialized_mtime_ns

    prompt_path.write_text("stale prompt\n", encoding="utf-8")
    stale_mtime_ns = prompt_path.stat().st_mtime_ns

    stale_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(eval_toml.parent),
            "--repo-root",
            str(repo_root),
            "--check",
        ],
    )

    assert stale_result.exit_code == EXIT_GENERAL_ERROR
    assert PROMPT_FILENAME in stale_result.output
    assert prompt_path.read_text(encoding="utf-8") == "stale prompt\n"
    assert prompt_path.stat().st_mtime_ns == stale_mtime_ns


@with_temp_workspace
def assert_cli_materializes_nested_eval_roots(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    evals_root = repo_root / "spx" / "node" / "evals"
    prompt_path = eval_toml.parent / PROMPT_FILENAME
    runner = CliRunner()

    write_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(evals_root),
            "--repo-root",
            str(repo_root),
        ],
    )

    assert write_result.exit_code == EXIT_SUCCESS
    assert str(prompt_path) in write_result.output
    materialized_prompt = prompt_path.read_text(encoding="utf-8")
    materialized_mtime_ns = prompt_path.stat().st_mtime_ns

    check_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(evals_root),
            "--repo-root",
            str(repo_root),
            "--check",
        ],
    )

    assert check_result.exit_code == EXIT_SUCCESS
    assert str(prompt_path) in check_result.output
    assert prompt_path.read_text(encoding="utf-8") == materialized_prompt
    assert prompt_path.stat().st_mtime_ns == materialized_mtime_ns


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


def write_prompt_source_definition(
    eval_toml: Path,
    *,
    prompt_source_kind: str,
    include_section: bool,
) -> None:
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


def write_producer_files_fixture(
    tmp_path: Path,
    *,
    producers: object | None = None,
    include_section: bool = False,
    include_singular: bool = False,
) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    eval_dir = repo_root / "spx" / "node" / "evals" / "rule"
    eval_dir.mkdir(parents=True)
    for producer_relative_path, content in zip(
        PRODUCER_FILES_RELATIVE_PATHS,
        PRODUCER_FILE_CONTENTS,
        strict=True,
    ):
        producer_path = repo_root / producer_relative_path
        producer_path.parent.mkdir(parents=True, exist_ok=True)
        producer_path.write_text(content, encoding="utf-8")
    (eval_dir / PROMPT_TEMPLATE_FILENAME).write_text(
        "Complete producers:\n\n{producer_files}\n",
        encoding="utf-8",
    )
    configured_producers = (
        list(PRODUCER_FILES_RELATIVE_PATHS) if producers is None else producers
    )
    prompt_source_lines = [
        f'{KIND_FIELD} = "{PRODUCER_FILES_KIND}"',
        f"{PRODUCERS_FIELD} = {_toml_value(configured_producers)}",
    ]
    if include_section:
        prompt_source_lines.append(f'{SECTION_FIELD} = "{SECTION_NAME}"')
    if include_singular:
        prompt_source_lines.append(f'{PRODUCER_FIELD} = "{PRODUCER_RELATIVE_PATH}"')
    prompt_source_lines.append(f'{TEMPLATE_FIELD} = "{PROMPT_TEMPLATE_FILENAME}"')
    eval_toml = eval_dir / EVAL_TOML_FILENAME
    eval_toml.write_text(
        "\n".join(
            [
                'title = "producer files prompt"',
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
    (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
    return repo_root, eval_toml


def _toml_value(value: object) -> str:
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    return str(value)


def producer_section(name: str, body: str) -> str:
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
    return "\n".join(
        [
            f'<example name="{name}">',
            "",
            body,
            "",
            "</example>",
        ]
    )
