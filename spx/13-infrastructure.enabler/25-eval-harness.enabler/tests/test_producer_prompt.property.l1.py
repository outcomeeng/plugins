"""Property evidence for whole-producer prompt materialization."""

from __future__ import annotations

import pytest

from outcomeeng_evals.producer_prompt import (
    MATERIALIZED_PROMPT_FILENAME,
    ProducerPromptError,
    materialize_prompt,
)
from outcomeeng_testing.harnesses.producer_prompt import (
    ProducerFileMutation,
    run_producer_files_change_property,
    with_producer_files_workspace,
)
from outcomeeng_testing.harnesses.producer_section_prompt import (
    PRODUCER_RELATIVE_PATH,
    PROMPT_FILENAME,
    SECTION_NAME,
    NoncanonicalPromptPath,
    SelectedSectionMutation,
    WholeProducerMutation,
    producer_section,
    run_noncanonical_prompt_path_property,
    run_selected_section_change_property,
    run_whole_producer_change_property,
    write_complete_producer_file_fixture,
    write_eval_fixture,
)


def test_materialized_prompt_changes_only_with_selected_section() -> None:
    def assertion(mutation: SelectedSectionMutation) -> None:
        selected_rule = f"selected-token-{mutation.rule_suffix}-end"
        updated_selected_rule = f"updated-token-{mutation.rule_suffix}-end"
        repo_root, eval_toml = write_eval_fixture(mutation.tmp_path)
        producer_path = repo_root / PRODUCER_RELATIVE_PATH
        prompt_path = eval_toml.parent / PROMPT_FILENAME
        producer_path.write_text(
            "\n".join(
                [
                    producer_section("other_section", mutation.unrelated_rule),
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
                    producer_section(
                        "other_section",
                        mutation.updated_unrelated_rule,
                    ),
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
                    producer_section(
                        "other_section",
                        mutation.updated_unrelated_rule,
                    ),
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

    run_selected_section_change_property(assertion)


def test_materialization_rejects_noncanonical_prompt_path() -> None:
    def assertion(case: NoncanonicalPromptPath) -> None:
        repo_root, eval_toml = write_eval_fixture(
            case.tmp_path,
            prompt_path=case.prompt_path,
        )

        with pytest.raises(
            ProducerPromptError,
            match=MATERIALIZED_PROMPT_FILENAME,
        ):
            materialize_prompt(eval_toml, repo_root=repo_root)
        assert not (eval_toml.parent / case.prompt_path).exists()

    run_noncanonical_prompt_path_property(assertion)


def test_materialized_prompt_changes_with_each_producer_file() -> None:
    def assertion(mutation: ProducerFileMutation) -> None:
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

    run_producer_files_change_property(assertion)


def test_materialized_prompt_changes_with_single_producer_file() -> None:
    def assertion(mutation: WholeProducerMutation) -> None:
        repo_root, eval_toml = write_complete_producer_file_fixture(mutation.tmp_path)
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

    run_whole_producer_change_property(assertion)
