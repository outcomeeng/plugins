"""Compliance evidence for the materialize-prompts CLI."""

from __future__ import annotations

from pathlib import Path

from outcomeeng_evals.cli import EXIT_GENERAL_ERROR, EXIT_SUCCESS
from outcomeeng_testing.harnesses.eval_workspaces import with_temp_workspace
from outcomeeng_testing.harnesses.producer_section_prompt import (
    PROMPT_FILENAME,
    STALE_PROMPT,
    invoke_materialize_prompts,
    write_eval_fixture,
    write_external_eval_fixture,
)


@with_temp_workspace
def test_cli_materializes_and_checks_prompt_drift(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)

    write_result = invoke_materialize_prompts(
        eval_toml.parent,
        repo_root=repo_root,
        check=False,
    )

    assert write_result.exit_code == EXIT_SUCCESS
    assert PROMPT_FILENAME in write_result.output

    prompt_path = eval_toml.parent / PROMPT_FILENAME
    materialized_prompt = prompt_path.read_text(encoding="utf-8")
    materialized_mtime_ns = prompt_path.stat().st_mtime_ns

    check_result = invoke_materialize_prompts(
        eval_toml.parent,
        repo_root=repo_root,
        check=True,
    )

    assert check_result.exit_code == EXIT_SUCCESS
    assert prompt_path.read_text(encoding="utf-8") == materialized_prompt
    assert prompt_path.stat().st_mtime_ns == materialized_mtime_ns

    prompt_path.write_text(STALE_PROMPT, encoding="utf-8")
    stale_mtime_ns = prompt_path.stat().st_mtime_ns

    stale_result = invoke_materialize_prompts(
        eval_toml.parent,
        repo_root=repo_root,
        check=True,
    )

    assert stale_result.exit_code == EXIT_GENERAL_ERROR
    assert PROMPT_FILENAME in stale_result.output
    assert prompt_path.read_text(encoding="utf-8") == STALE_PROMPT
    assert prompt_path.stat().st_mtime_ns == stale_mtime_ns


@with_temp_workspace
def test_cli_materializes_nested_eval_roots(tmp_path: Path) -> None:
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    evals_root = repo_root / "spx" / "node" / "evals"
    prompt_path = eval_toml.parent / PROMPT_FILENAME

    write_result = invoke_materialize_prompts(
        evals_root,
        repo_root=repo_root,
        check=False,
    )

    assert write_result.exit_code == EXIT_SUCCESS
    assert str(prompt_path) in write_result.output
    materialized_prompt = prompt_path.read_text(encoding="utf-8")
    materialized_mtime_ns = prompt_path.stat().st_mtime_ns

    check_result = invoke_materialize_prompts(
        evals_root,
        repo_root=repo_root,
        check=True,
    )

    assert check_result.exit_code == EXIT_SUCCESS
    assert str(prompt_path) in check_result.output
    assert prompt_path.read_text(encoding="utf-8") == materialized_prompt
    assert prompt_path.stat().st_mtime_ns == materialized_mtime_ns


@with_temp_workspace
def test_cli_rejects_eval_root_outside_repository(tmp_path: Path) -> None:
    repo_root, eval_toml = write_external_eval_fixture(tmp_path)

    result = invoke_materialize_prompts(
        eval_toml.parent,
        repo_root=repo_root,
        check=False,
    )

    assert result.exit_code == EXIT_GENERAL_ERROR
    assert not (eval_toml.parent / PROMPT_FILENAME).exists()
