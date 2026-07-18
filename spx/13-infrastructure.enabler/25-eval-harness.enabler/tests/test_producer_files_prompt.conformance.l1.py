"""Conformance evidence for plural-producer prompt materialization."""

from __future__ import annotations

import pytest

from outcomeeng_evals.producer_prompt import (
    PRODUCERS_FIELD,
    PRODUCER_FILES_KIND,
    PRODUCER_FILES_PLACEHOLDER,
    ProducerPromptError,
    materialize_prompt,
)
from outcomeeng_testing.harnesses.producer_prompt import (
    with_absolute_producer_files_workspace,
    with_duplicate_producer_files_placeholder_workspace,
    with_duplicate_producer_files_workspace,
    with_empty_producer_files_workspace,
    with_missing_producer_files_placeholder_workspace,
    with_parent_traversal_producer_files_workspace,
    with_producer_files_workspace,
    with_sectioned_producer_files_workspace,
)


def test_materializes_prompt_from_ordered_producer_files() -> None:
    with with_producer_files_workspace() as workspace:
        materialize_prompt(workspace.eval_toml_path, repo_root=workspace.repo_root)
        prompt_text = workspace.read_prompt()
        producer_block_positions = tuple(
            position
            for relative_path, producer_text in zip(
                workspace.producer_relative_paths,
                workspace.producer_texts,
                strict=True,
            )
            for position in (
                prompt_text.rindex(relative_path),
                prompt_text.index(producer_text),
            )
        )
        assert producer_block_positions == tuple(sorted(producer_block_positions))


def test_producer_files_rejects_empty_source_set() -> None:
    with with_empty_producer_files_workspace() as workspace:
        with pytest.raises(ProducerPromptError, match=PRODUCERS_FIELD):
            materialize_prompt(
                workspace.eval_toml_path,
                repo_root=workspace.repo_root,
            )


def test_producer_files_rejects_duplicate_source_path() -> None:
    with with_duplicate_producer_files_workspace() as workspace:
        with pytest.raises(ProducerPromptError, match=PRODUCERS_FIELD):
            materialize_prompt(
                workspace.eval_toml_path,
                repo_root=workspace.repo_root,
            )


def test_producer_files_rejects_absolute_source_path() -> None:
    with with_absolute_producer_files_workspace() as workspace:
        with pytest.raises(ProducerPromptError, match=PRODUCERS_FIELD):
            materialize_prompt(
                workspace.eval_toml_path,
                repo_root=workspace.repo_root,
            )


def test_producer_files_rejects_parent_traversal_source_path() -> None:
    with with_parent_traversal_producer_files_workspace() as workspace:
        with pytest.raises(ProducerPromptError, match=PRODUCERS_FIELD):
            materialize_prompt(
                workspace.eval_toml_path,
                repo_root=workspace.repo_root,
            )


def test_producer_files_rejects_section_with_actual_source_kind() -> None:
    with with_sectioned_producer_files_workspace() as workspace:
        with pytest.raises(ProducerPromptError, match=PRODUCER_FILES_KIND):
            materialize_prompt(
                workspace.eval_toml_path,
                repo_root=workspace.repo_root,
            )


def test_producer_files_rejects_template_without_producer_bodies() -> None:
    with with_missing_producer_files_placeholder_workspace() as workspace:
        with pytest.raises(ProducerPromptError) as error:
            materialize_prompt(
                workspace.eval_toml_path,
                repo_root=workspace.repo_root,
            )
        assert PRODUCER_FILES_PLACEHOLDER in str(error.value)


def test_producer_files_rejects_template_with_repeated_producer_bodies() -> None:
    with with_duplicate_producer_files_placeholder_workspace() as workspace:
        with pytest.raises(ProducerPromptError) as error:
            materialize_prompt(
                workspace.eval_toml_path,
                repo_root=workspace.repo_root,
            )
        assert PRODUCER_FILES_PLACEHOLDER in str(error.value)
