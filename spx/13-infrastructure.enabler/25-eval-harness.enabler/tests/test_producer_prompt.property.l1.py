"""Property evidence for whole-producer prompt materialization."""

from __future__ import annotations

import pytest
from hypothesis import given

from outcomeeng_evals.producer_prompt import (
    MATERIALIZED_PROMPT_FILENAME,
    ProducerPromptError,
    materialize_prompt,
)
from outcomeeng_testing.generators.producer_prompt import (
    NoncanonicalPromptPath,
    ProducerFileMutation,
    SelectedSectionMutation,
    WholeProducerMutation,
    noncanonical_prompt_paths,
    producer_file_mutations,
    selected_section_mutations,
    whole_producer_mutations,
)
from outcomeeng_testing.harnesses.eval_workspaces import temporary_workspace
from outcomeeng_testing.harnesses.producer_prompt import (
    PRODUCER_RELATIVE_PATHS,
    producer_prompt_property,
    with_producer_files_workspace,
)
from outcomeeng_testing.harnesses.producer_section_prompt import (
    PRODUCER_RELATIVE_PATH,
    PROMPT_FILENAME,
    SECTION_NAME,
    UNRELATED_SECTION_NAME,
    producer_section,
    write_complete_producer_file_fixture,
    write_eval_fixture,
)


@producer_prompt_property
@given(mutation=selected_section_mutations())
def test_materialized_prompt_changes_only_with_selected_section(
    mutation: SelectedSectionMutation,
) -> None:
    with temporary_workspace() as tmp_path:
        repo_root, eval_toml = write_eval_fixture(tmp_path)
        producer_path = repo_root / PRODUCER_RELATIVE_PATH
        prompt_path = eval_toml.parent / PROMPT_FILENAME
        producer_path.write_text(
            "\n".join(
                [
                    producer_section(
                        UNRELATED_SECTION_NAME,
                        mutation.unrelated_rule,
                    ),
                    producer_section(SECTION_NAME, mutation.selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)
        original_prompt = prompt_path.read_text(encoding="utf-8")

        producer_path.write_text(
            "\n".join(
                [
                    producer_section(
                        UNRELATED_SECTION_NAME,
                        mutation.updated_unrelated_rule,
                    ),
                    producer_section(SECTION_NAME, mutation.selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)

        assert prompt_path.read_text(encoding="utf-8") == original_prompt

        producer_path.write_text(
            "\n".join(
                [
                    producer_section(
                        UNRELATED_SECTION_NAME,
                        mutation.updated_unrelated_rule,
                    ),
                    producer_section(SECTION_NAME, mutation.updated_selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)
        updated_prompt = prompt_path.read_text(encoding="utf-8")

        assert updated_prompt != original_prompt
        assert mutation.updated_selected_rule in updated_prompt
        assert mutation.selected_rule not in updated_prompt


@producer_prompt_property
@given(case=noncanonical_prompt_paths())
def test_materialization_rejects_noncanonical_prompt_path(
    case: NoncanonicalPromptPath,
) -> None:
    with temporary_workspace() as tmp_path:
        repo_root, eval_toml = write_eval_fixture(
            tmp_path,
            prompt_path=case.prompt_path,
        )

        with pytest.raises(
            ProducerPromptError,
            match=MATERIALIZED_PROMPT_FILENAME,
        ):
            materialize_prompt(eval_toml, repo_root=repo_root)
        assert not (eval_toml.parent / case.prompt_path).exists()


@producer_prompt_property
@given(mutation=producer_file_mutations(len(PRODUCER_RELATIVE_PATHS)))
def test_materialized_prompt_changes_with_each_producer_file(
    mutation: ProducerFileMutation,
) -> None:
    with with_producer_files_workspace() as workspace:
        materialize_prompt(
            workspace.eval_toml_path,
            repo_root=workspace.repo_root,
        )
        original_prompt = workspace.read_prompt()
        workspace.append_to_producer(
            mutation.producer_index,
            mutation.suffix,
        )

        materialize_prompt(
            workspace.eval_toml_path,
            repo_root=workspace.repo_root,
        )
        updated_prompt = workspace.read_prompt()

        assert updated_prompt != original_prompt
        assert mutation.suffix in updated_prompt


@producer_prompt_property
@given(mutation=whole_producer_mutations())
def test_materialized_prompt_changes_with_single_producer_file(
    mutation: WholeProducerMutation,
) -> None:
    with temporary_workspace() as tmp_path:
        repo_root, eval_toml = write_complete_producer_file_fixture(tmp_path)
        prompt_path = eval_toml.parent / PROMPT_FILENAME
        producer_path = repo_root / PRODUCER_RELATIVE_PATH

        materialize_prompt(eval_toml, repo_root=repo_root)
        original_prompt = prompt_path.read_text(encoding="utf-8")
        producer_path.write_text(
            producer_path.read_text(encoding="utf-8") + mutation.suffix,
            encoding="utf-8",
        )

        materialize_prompt(eval_toml, repo_root=repo_root)
        updated_prompt = prompt_path.read_text(encoding="utf-8")

        assert updated_prompt != original_prompt
        assert mutation.suffix in updated_prompt
