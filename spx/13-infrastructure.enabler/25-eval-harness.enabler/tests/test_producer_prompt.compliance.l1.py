"""Compliance evidence for producer-derived eval prompt materialization."""

from __future__ import annotations

import pytest

from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    PRODUCER_FIELD,
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
    NESTED_STEP_BODY,
    NESTED_STEP_NAME,
    PROMPT_FILENAME,
    STALE_PROMPT_SUFFIX,
    MaterializedProducer,
    ProducerWorkspace,
    ProducerWorkspaceCase,
    run_materialized_runtime_sections,
    run_producer_workspace_case,
)


def test_materializes_prompt_from_named_producer_sections() -> None:
    def predicate(observation: MaterializedProducer) -> None:
        assert observation.selected_section in observation.prompt_text
        assert observation.case.relative_path in observation.prompt_text
        assert observation.case.section_name in observation.prompt_text

    run_materialized_runtime_sections(predicate)


def test_producer_file_rejects_section_selector() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError, match=SECTION_FIELD):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(
        ProducerWorkspaceCase.PRODUCER_FILE_WITH_SECTION,
        predicate,
    )


def test_check_accepts_current_materialized_prompt() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        verify_materialized_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(ProducerWorkspaceCase.DEFAULT, predicate)


def test_check_rejects_stale_materialized_prompt() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        workspace.prompt_path.write_text(
            f"{workspace.prompt_path.read_text(encoding='utf-8')}{STALE_PROMPT_SUFFIX}",
            encoding="utf-8",
        )
        with pytest.raises(PromptMaterializationDrift, match=PROMPT_FILENAME):
            verify_materialized_prompt(
                workspace.eval_toml,
                repo_root=workspace.repo_root,
            )

    run_producer_workspace_case(ProducerWorkspaceCase.DEFAULT, predicate)


def test_rejects_prompt_path_outside_eval_dir() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(ProducerWorkspaceCase.PROMPT_OUTSIDE_EVAL, predicate)


def test_rejects_prompt_template_alias() -> None:
    def predicate(workspace: ProducerWorkspace, original_prompt: str | None) -> None:
        assert original_prompt is not None
        with pytest.raises(ProducerPromptError, match=TEMPLATE_FIELD):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        assert workspace.prompt_path.read_text(encoding="utf-8") == original_prompt

    run_producer_workspace_case(
        ProducerWorkspaceCase.TEMPLATE_ALIASES_PROMPT,
        predicate,
    )


def test_rejects_absolute_producer_path() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(ProducerWorkspaceCase.ABSOLUTE_PRODUCER, predicate)


def test_rejects_producer_path_outside_repo() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        assert workspace.repo_root.is_dir()

    run_producer_workspace_case(
        ProducerWorkspaceCase.PRODUCER_OUTSIDE_REPO,
        predicate,
    )


def test_preserves_placeholder_text_inside_selected_section() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        assert (
            workspace.prompt_path.read_text(encoding="utf-8").count(
                LITERAL_PRODUCER_SECTION_TOKEN
            )
            == 1
        )

    run_producer_workspace_case(ProducerWorkspaceCase.PLACEHOLDER_TEXT, predicate)


def test_rejects_missing_selected_section() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError, match=workspace.case.section_name):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(ProducerWorkspaceCase.MISSING_SECTION, predicate)


def test_similar_attributes_do_not_select_a_section() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError, match=workspace.case.section_name):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(ProducerWorkspaceCase.SIMILAR_ATTRIBUTES, predicate)


def test_non_step_tags_do_not_select_a_section() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError, match=workspace.case.section_name):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(ProducerWorkspaceCase.NON_STEP_TAG, predicate)


def test_rejects_duplicate_selected_sections() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError, match=workspace.case.section_name):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(ProducerWorkspaceCase.DUPLICATE_SECTION, predicate)


def test_rejects_literal_step_closing_delimiter() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(
        ProducerWorkspaceCase.LITERAL_CLOSING_DELIMITER,
        predicate,
    )


def test_preserves_nested_step_section() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        assert (
            f'name="{workspace.case.section_name}"'
            in workspace.prompt_path.read_text(encoding="utf-8")
        )
        assert f'name="{NESTED_STEP_NAME}"' in workspace.prompt_path.read_text(
            encoding="utf-8"
        )
        assert NESTED_STEP_BODY in workspace.prompt_path.read_text(encoding="utf-8")

    run_producer_workspace_case(ProducerWorkspaceCase.NESTED_STEP, predicate)


def test_rejects_unsupported_prompt_source_kind() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(
            ProducerPromptError,
            match=ProducerWorkspaceCase.UNSUPPORTED_KIND.value,
        ):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(ProducerWorkspaceCase.UNSUPPORTED_KIND, predicate)


@pytest.mark.parametrize(
    ("case", "field"),
    (
        (ProducerWorkspaceCase.MISSING_KIND, KIND_FIELD),
        (ProducerWorkspaceCase.MISSING_PRODUCER, PRODUCER_FIELD),
        (ProducerWorkspaceCase.MISSING_SECTION_FIELD, SECTION_FIELD),
        (ProducerWorkspaceCase.MISSING_TEMPLATE, TEMPLATE_FIELD),
    ),
)
def test_rejects_missing_prompt_source_fields(
    case: ProducerWorkspaceCase,
    field: str,
) -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        with pytest.raises(ProducerPromptError, match=field):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    run_producer_workspace_case(case, predicate)


def test_producer_file_definition_omits_section() -> None:
    def predicate(workspace: ProducerWorkspace, _: str | None) -> None:
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        assert workspace.prompt_path.is_file()
        assert PROMPT_SOURCE_TABLE in workspace.eval_toml.read_text(encoding="utf-8")

    run_producer_workspace_case(ProducerWorkspaceCase.VALID_PRODUCER_FILE, predicate)
