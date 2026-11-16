"""Conformance evidence for producer-derived eval prompt materialization."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    PRODUCER_FIELD,
    PRODUCER_FILE_KIND,
    PRODUCER_FILE_PLACEHOLDER,
    PRODUCER_SECTION_PLACEHOLDER,
    SECTION_FIELD,
    TEMPLATE_FIELD,
    PromptMaterializationDrift,
    ProducerPromptError,
    materialize_prompt,
    verify_materialized_prompt,
)
from outcomeeng_testing.harnesses.eval_workspaces import with_temp_workspace
from outcomeeng_testing.harnesses.producer_section_prompt import (
    LITERAL_PRODUCER_SECTION_TOKEN,
    LITERAL_STEP_CLOSING_DELIMITER,
    NESTED_STEP_BODY,
    NESTED_STEP_NAME,
    PRODUCER_PATH_OUTSIDE_REPOSITORY,
    PRODUCER_RELATIVE_PATH,
    PROMPT_FILENAME,
    PROMPT_PATH_OUTSIDE_EVAL_DIRECTORY,
    SECTION_NAME,
    SELECTED_RULE,
    STALE_PROMPT,
    UNRELATED_RULE,
    UNSUPPORTED_PROMPT_SOURCE_KIND,
    producer_section,
    write_eval_fixture,
    write_complete_producer_file_fixture,
    write_producer_file_fixture_with_repeated_body,
    write_producer_file_fixture_without_body,
    write_producer_section_fixture_with_repeated_body,
    write_producer_section_fixture_without_body,
)


@with_temp_workspace
def test_materializes_prompt_from_named_producer_section(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)

    materialize_prompt(eval_toml, repo_root=repo_root)

    prompt_text = (eval_toml.parent / PROMPT_FILENAME).read_text(encoding="utf-8")
    assert SELECTED_RULE in prompt_text
    assert UNRELATED_RULE not in prompt_text
    assert PRODUCER_RELATIVE_PATH in prompt_text
    assert SECTION_NAME in prompt_text


@with_temp_workspace
def test_materializes_prompt_from_complete_producer_file(tmp_path: Path) -> None:
    repo_root, eval_toml = write_complete_producer_file_fixture(tmp_path)
    producer_text = (repo_root / PRODUCER_RELATIVE_PATH).read_text(encoding="utf-8")

    materialize_prompt(eval_toml, repo_root=repo_root)

    prompt_text = (eval_toml.parent / PROMPT_FILENAME).read_text(encoding="utf-8")
    assert producer_text in prompt_text
    assert PRODUCER_RELATIVE_PATH in prompt_text


@with_temp_workspace
def test_producer_file_rejects_section_selector(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_source_kind=PRODUCER_FILE_KIND,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_producer_section_rejects_template_without_body(tmp_path: Path) -> None:
    repo_root, eval_toml = write_producer_section_fixture_without_body(tmp_path)

    with pytest.raises(ProducerPromptError) as error:
        materialize_prompt(eval_toml, repo_root=repo_root)

    assert PRODUCER_SECTION_PLACEHOLDER in str(error.value)


@with_temp_workspace
def test_producer_section_rejects_template_with_repeated_body(tmp_path: Path) -> None:
    repo_root, eval_toml = write_producer_section_fixture_with_repeated_body(tmp_path)

    with pytest.raises(ProducerPromptError) as error:
        materialize_prompt(eval_toml, repo_root=repo_root)

    assert PRODUCER_SECTION_PLACEHOLDER in str(error.value)


@with_temp_workspace
def test_producer_file_rejects_template_without_body(tmp_path: Path) -> None:
    repo_root, eval_toml = write_producer_file_fixture_without_body(tmp_path)

    with pytest.raises(ProducerPromptError) as error:
        materialize_prompt(eval_toml, repo_root=repo_root)

    assert PRODUCER_FILE_PLACEHOLDER in str(error.value)


@with_temp_workspace
def test_producer_file_rejects_template_with_repeated_body(tmp_path: Path) -> None:
    repo_root, eval_toml = write_producer_file_fixture_with_repeated_body(tmp_path)

    with pytest.raises(ProducerPromptError) as error:
        materialize_prompt(eval_toml, repo_root=repo_root)

    assert PRODUCER_FILE_PLACEHOLDER in str(error.value)


@with_temp_workspace
def test_check_accepts_current_materialized_prompt(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    materialize_prompt(eval_toml, repo_root=repo_root)

    verify_materialized_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_check_rejects_stale_materialized_prompt(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    (eval_toml.parent / PROMPT_FILENAME).write_text(STALE_PROMPT, encoding="utf-8")

    with pytest.raises(PromptMaterializationDrift, match=PROMPT_FILENAME):
        verify_materialized_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_materialization_rejects_prompt_path_outside_eval_dir(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_path=PROMPT_PATH_OUTSIDE_EVAL_DIRECTORY,
    )

    with pytest.raises(ProducerPromptError, match="prompt"):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_materialization_rejects_prompt_template_alias(tmp_path: Path) -> None:
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
def test_materialization_rejects_absolute_producer_path(tmp_path: Path) -> None:
    absolute_path = tmp_path / "repo" / PRODUCER_RELATIVE_PATH
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        producer_relative_path=str(absolute_path),
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_materialization_rejects_producer_path_outside_repo(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        producer_relative_path=PRODUCER_PATH_OUTSIDE_REPOSITORY,
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)
    assert repo_root.is_dir()


@with_temp_workspace
def test_materialization_preserves_placeholder_text_inside_producer_section(
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
def test_missing_producer_section_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        section_name="missing",
    )

    with pytest.raises(ProducerPromptError, match="missing"):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_similar_attribute_names_do_not_match_section_name(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        include_named_section=False,
        include_false_positive_attributes=True,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_non_step_tags_do_not_match_section_name(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        include_named_section=False,
        include_non_step_named_tag=True,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_selected_section_rejects_literal_step_closing_delimiter(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        selected_rule=LITERAL_STEP_CLOSING_DELIMITER,
    )

    with pytest.raises(ProducerPromptError, match="step closing delimiter"):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_selected_section_preserves_nested_step_section(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        selected_rule=producer_section(NESTED_STEP_NAME, NESTED_STEP_BODY),
    )

    prompt_path = materialize_prompt(eval_toml, repo_root=repo_root)

    prompt = prompt_path.read_text(encoding="utf-8")
    assert f'name="{SECTION_NAME}"' in prompt
    assert f'name="{NESTED_STEP_NAME}"' in prompt
    assert NESTED_STEP_BODY in prompt


@with_temp_workspace
def test_duplicate_producer_section_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path, duplicate_section=True)

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_unsupported_prompt_source_kind_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_source_kind=UNSUPPORTED_PROMPT_SOURCE_KIND,
    )

    with pytest.raises(ProducerPromptError, match=UNSUPPORTED_PROMPT_SOURCE_KIND):
        materialize_prompt(eval_toml, repo_root=repo_root)


@with_temp_workspace
def test_missing_prompt_source_fields_are_rejected(tmp_path: Path) -> None:
    for omitted_field in (KIND_FIELD, PRODUCER_FIELD, SECTION_FIELD, TEMPLATE_FIELD):
        repo_root, eval_toml = write_eval_fixture(
            tmp_path / omitted_field,
            omitted_prompt_source_fields=(omitted_field,),
        )

        with pytest.raises(ProducerPromptError, match=omitted_field):
            materialize_prompt(eval_toml, repo_root=repo_root)
