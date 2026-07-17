"""Compliance evidence for producer-derived eval prompt materialization."""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    MATERIALIZED_PROMPT_FILENAME,
    PRODUCER_FIELD,
    PRODUCER_FILE_KIND,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
    PromptMaterializationDrift,
    ProducerPromptError,
    materialize_prompt,
    verify_materialized_prompt,
)
from outcomeeng_testing.evals.producer_prompt import (
    LITERAL_PRODUCER_SECTION_TOKEN,
    PROMPT_FILENAME,
    PROMPT_TEMPLATE_FILENAME,
    ProducerMutation,
    materialize_runtime_sections,
    write_eval_workspace,
    write_prompt_source_definition,
)
from outcomeeng_testing.harnesses.eval_workspaces import with_temp_workspace


@with_temp_workspace
def test_materializes_prompt_from_named_producer_sections(tmp_path: Path) -> None:
    for observation in materialize_runtime_sections(tmp_path):
        assert observation.selected_section in observation.prompt_text
        assert observation.case.relative_path in observation.prompt_text
        assert observation.case.section_name in observation.prompt_text


@with_temp_workspace
def test_producer_file_rejects_section_selector(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, prompt_source_kind=PRODUCER_FILE_KIND)

    with pytest.raises(ProducerPromptError, match=SECTION_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_check_accepts_current_materialized_prompt(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path)
    materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    verify_materialized_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_check_rejects_stale_materialized_prompt(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path)
    materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
    workspace.prompt_path.write_text(
        f"{workspace.prompt_path.read_text(encoding='utf-8')}stale",
        encoding="utf-8",
    )

    with pytest.raises(PromptMaterializationDrift, match=PROMPT_FILENAME):
        verify_materialized_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_prompt_path_outside_eval_dir(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, prompt_path="../../prompt.md")

    with pytest.raises(ProducerPromptError, match="prompt"):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_prompt_template_alias(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        prompt_template_path=MATERIALIZED_PROMPT_FILENAME,
    )
    original_prompt = workspace.prompt_path.read_text(encoding="utf-8")

    with pytest.raises(ProducerPromptError, match=TEMPLATE_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    assert workspace.prompt_path.read_text(encoding="utf-8") == original_prompt


@with_temp_workspace
def test_rejects_absolute_producer_path(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        producer_relative_path=str(tmp_path.resolve()),
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_producer_path_outside_repo(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        producer_relative_path="../outside/SKILL.md",
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    assert workspace.repo_root.is_dir()


@with_temp_workspace
def test_preserves_placeholder_text_inside_selected_section(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        mutation=ProducerMutation.PLACEHOLDER_TEXT,
    )

    materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    assert (
        workspace.prompt_path.read_text(encoding="utf-8").count(
            LITERAL_PRODUCER_SECTION_TOKEN
        )
        == 1
    )


@with_temp_workspace
def test_rejects_missing_selected_section(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        mutation=ProducerMutation.MISSING_SECTION,
    )

    with pytest.raises(ProducerPromptError, match=workspace.case.section_name):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_similar_attributes_do_not_select_a_section(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        mutation=ProducerMutation.SIMILAR_ATTRIBUTES,
    )

    with pytest.raises(ProducerPromptError, match=workspace.case.section_name):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_non_step_tags_do_not_select_a_section(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        mutation=ProducerMutation.NON_STEP_TAG,
    )

    with pytest.raises(ProducerPromptError, match=workspace.case.section_name):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_duplicate_selected_sections(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        mutation=ProducerMutation.DUPLICATE_SECTION,
    )

    with pytest.raises(ProducerPromptError, match=workspace.case.section_name):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_literal_step_closing_delimiter(tmp_path: Path) -> None:
    workspace = write_eval_workspace(
        tmp_path,
        mutation=ProducerMutation.LITERAL_CLOSING_DELIMITER,
    )

    with pytest.raises(ProducerPromptError, match="step closing delimiter"):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_preserves_nested_step_section(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, mutation=ProducerMutation.NESTED_STEP)

    materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
    prompt = workspace.prompt_path.read_text(encoding="utf-8")

    assert f'name="{workspace.case.section_name}"' in prompt
    assert 'name="nested_step"' in prompt
    assert "Nested body." in prompt


@with_temp_workspace
def test_rejects_unsupported_prompt_source_kind(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, prompt_source_kind="simulation")

    with pytest.raises(ProducerPromptError, match="simulation"):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_missing_prompt_source_kind(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, omitted_fields=(KIND_FIELD,))

    with pytest.raises(ProducerPromptError, match=KIND_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_missing_prompt_source_producer(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, omitted_fields=(PRODUCER_FIELD,))

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_missing_prompt_source_section(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, omitted_fields=(SECTION_FIELD,))

    with pytest.raises(ProducerPromptError, match=SECTION_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_rejects_missing_prompt_source_template(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, omitted_fields=(TEMPLATE_FIELD,))

    with pytest.raises(ProducerPromptError, match=TEMPLATE_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def test_producer_file_definition_omits_section(tmp_path: Path) -> None:
    workspace = write_eval_workspace(tmp_path, prompt_source_kind=PRODUCER_FILE_KIND)
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

    materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    assert workspace.prompt_path.is_file()
    assert PROMPT_SOURCE_TABLE in workspace.eval_toml.read_text(encoding="utf-8")
