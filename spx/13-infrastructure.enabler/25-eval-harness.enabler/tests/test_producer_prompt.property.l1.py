"""Property evidence for producer-derived prompt materialization."""

import pytest

from outcomeeng_evals.producer_prompt import (
    MATERIALIZED_PROMPT_FILENAME,
    ProducerPromptError,
    materialize_prompt,
)
from outcomeeng_testing.evals.producer_prompt import (
    ProducerWorkspace,
    SectionMutationObservation,
    run_noncanonical_prompt_property,
    run_section_mutation_property,
)


def test_only_selected_section_changes_materialized_prompt() -> None:
    def predicate(observation: SectionMutationObservation) -> None:
        assert observation.unrelated_prompt == observation.original_prompt
        assert observation.selected_prompt != observation.original_prompt
        assert observation.updated_token in observation.selected_prompt
        assert observation.original_token not in observation.selected_prompt

    run_section_mutation_property(predicate)


def test_noncanonical_prompt_paths_are_rejected() -> None:
    def predicate(workspace: ProducerWorkspace, prompt_path: str) -> None:
        with pytest.raises(ProducerPromptError, match=MATERIALIZED_PROMPT_FILENAME):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        assert not (workspace.eval_toml.parent / prompt_path).exists()

    run_noncanonical_prompt_property(predicate)
