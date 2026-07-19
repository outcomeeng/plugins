"""Compliance evidence for producer-derived eval prompt materialization."""

from __future__ import annotations

import os

from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    PRODUCER_FIELD,
    PRODUCER_SECTION_PLACEHOLDER,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
    UNMATCHED_STEP_DELIMITER_REASON,
)
from outcomeeng_testing.evals.producer_prompt import (
    NESTED_STEP_BODY,
    NESTED_STEP_NAME,
    CliMaterializedProducer,
    CliProducerWorkspaceObservation,
    ProducerWorkspaceCase,
    ShippedProducerEvalObservation,
    run_cli_materialized_runtime_sections,
    run_cli_producer_workspace_contract,
    run_cli_shipped_producer_evals,
)


def test_materializes_runtime_sections_through_cli() -> None:
    def predicate(observation: CliMaterializedProducer) -> None:
        assert observation.result.exit_code == os.EX_OK
        assert observation.selected_section in observation.prompt_text
        assert observation.case.relative_path in observation.prompt_text
        assert observation.case.section_name in observation.prompt_text

    run_cli_materialized_runtime_sections(predicate)


def test_shipped_producer_eval_declarations_are_current() -> None:
    def predicate(observation: ShippedProducerEvalObservation) -> None:
        assert observation.result.exit_code == os.EX_OK
        assert observation.definition.eval_toml_path == observation.eval_toml
        assert observation.definition.producer_path.is_file()
        assert observation.definition.template_path.is_file()
        assert observation.definition.prompt_path.is_file()

    run_cli_shipped_producer_evals(predicate)


def test_cli_enforces_producer_prompt_contract() -> None:
    def predicate(observation: CliProducerWorkspaceObservation) -> None:
        workspace = observation.workspace
        match observation.case:
            case ProducerWorkspaceCase.DEFAULT:
                assert observation.result.exit_code == os.EX_OK
                assert workspace.prompt_path.is_file()
            case ProducerWorkspaceCase.PRODUCER_FILE_WITH_SECTION:
                assert observation.result.exit_code != os.EX_OK
                assert SECTION_FIELD in observation.result.output
            case ProducerWorkspaceCase.PROMPT_OUTSIDE_EVAL:
                assert observation.result.exit_code != os.EX_OK
            case ProducerWorkspaceCase.TEMPLATE_ALIASES_PROMPT:
                assert observation.original_prompt is not None
                assert observation.result.exit_code != os.EX_OK
                assert TEMPLATE_FIELD in observation.result.output
                assert (
                    workspace.prompt_path.read_text(encoding="utf-8")
                    == observation.original_prompt
                )
            case (
                ProducerWorkspaceCase.ABSOLUTE_TEMPLATE
                | ProducerWorkspaceCase.TEMPLATE_OUTSIDE_EVAL
            ):
                assert observation.result.exit_code != os.EX_OK
                assert TEMPLATE_FIELD in observation.result.output
            case ProducerWorkspaceCase.ABSOLUTE_PRODUCER:
                assert observation.result.exit_code != os.EX_OK
                assert PRODUCER_FIELD in observation.result.output
            case ProducerWorkspaceCase.PRODUCER_OUTSIDE_REPO:
                assert observation.result.exit_code != os.EX_OK
                assert PRODUCER_FIELD in observation.result.output
                assert workspace.repo_root.is_dir()
            case ProducerWorkspaceCase.PLACEHOLDER_TEXT:
                assert observation.result.exit_code == os.EX_OK
                assert (
                    workspace.prompt_path.read_text(encoding="utf-8").count(
                        PRODUCER_SECTION_PLACEHOLDER
                    )
                    == 1
                )
            case (
                ProducerWorkspaceCase.MISSING_SECTION
                | ProducerWorkspaceCase.SIMILAR_ATTRIBUTES
                | ProducerWorkspaceCase.NON_STEP_TAG
                | ProducerWorkspaceCase.DUPLICATE_SECTION
            ):
                assert observation.result.exit_code != os.EX_OK
                assert workspace.case.section_name in observation.result.output
            case ProducerWorkspaceCase.LITERAL_CLOSING_DELIMITER:
                assert observation.result.exit_code != os.EX_OK
                assert UNMATCHED_STEP_DELIMITER_REASON in observation.result.output
            case ProducerWorkspaceCase.NESTED_STEP:
                assert observation.result.exit_code == os.EX_OK
                prompt_text = workspace.prompt_path.read_text(encoding="utf-8")
                assert f'name="{workspace.case.section_name}"' in prompt_text
                assert f'name="{NESTED_STEP_NAME}"' in prompt_text
                assert NESTED_STEP_BODY in prompt_text
            case ProducerWorkspaceCase.UNSUPPORTED_KIND:
                assert observation.result.exit_code != os.EX_OK
                assert observation.case.value in observation.result.output
            case ProducerWorkspaceCase.MISSING_KIND:
                assert observation.result.exit_code != os.EX_OK
                assert KIND_FIELD in observation.result.output
            case ProducerWorkspaceCase.MISSING_PRODUCER:
                assert observation.result.exit_code != os.EX_OK
                assert PRODUCER_FIELD in observation.result.output
            case ProducerWorkspaceCase.MISSING_SECTION_FIELD:
                assert observation.result.exit_code != os.EX_OK
                assert SECTION_FIELD in observation.result.output
            case ProducerWorkspaceCase.MISSING_TEMPLATE:
                assert observation.result.exit_code != os.EX_OK
                assert TEMPLATE_FIELD in observation.result.output
            case ProducerWorkspaceCase.VALID_PRODUCER_FILE:
                assert observation.result.exit_code == os.EX_OK
                assert workspace.prompt_path.is_file()
                assert PROMPT_SOURCE_TABLE in workspace.eval_toml.read_text(
                    encoding="utf-8"
                )
                assert workspace.producer_path.read_text(
                    encoding="utf-8"
                ) in workspace.prompt_path.read_text(encoding="utf-8")
            case _:
                raise AssertionError(
                    f"unasserted producer workspace case: {observation.case}"
                )

    run_cli_producer_workspace_contract(predicate)
