"""Fixture-corpus evidence for producer-derived prompt materialization."""

from __future__ import annotations

import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import click
import pytest
from click.testing import CliRunner
from hypothesis import assume, given, seed, settings

from outcomeeng_evals.cli import EXIT_GENERAL_ERROR, EXIT_SUCCESS, main
from outcomeeng_evals.cli.commands.materialize_prompts import (
    materialize_prompts_command,
)
from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    MATERIALIZED_PROMPT_FILENAME,
    PRODUCER_FIELD,
    PRODUCER_BOUNDARY_END_TEMPLATE,
    PRODUCER_BOUNDARY_START_TEMPLATE,
    PRODUCER_FENCE_CHARACTER,
    PRODUCER_FENCE_INFO_STRING,
    PRODUCER_FILE_KIND,
    PRODUCER_FILE_PLACEHOLDER,
    PRODUCER_FILES_KIND,
    PRODUCER_FILES_PLACEHOLDER,
    PRODUCER_PROMPT_KINDS,
    PRODUCER_SECTION_KIND,
    PRODUCERS_FIELD,
    PROMPT_FIELD,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
    UTF8_ENCODING,
    PromptMaterializationDrift,
    ProducerPromptDefinition,
    ProducerPromptError,
    extract_named_producer_section,
    load_producer_prompt_definition,
    materialize_prompt,
    verify_materialized_prompt,
)
from outcomeeng_testing.generators.evals import (
    absent_section_name,
    distinct_producer_rule_texts,
    missing_producer_path,
    noncanonical_prompt_filenames,
    outside_eval_prompt_path,
    outside_repository_path,
    unsupported_prompt_source_kind,
)
from outcomeeng_testing.harnesses.eval_workspaces import (
    PRODUCER_PROMPT_FIXTURE_ROOT,
    EvalWorkspace,
    TomlValue,
    copy_eval_workspace,
    remove_toml_field,
    replace_text_once,
    replace_workspace_file,
    set_toml_field,
    with_temp_workspace,
)


PROMPT_FILENAME = MATERIALIZED_PROMPT_FILENAME
PRODUCER_PROMPT_PROPERTY_SEED = 20260706
PRODUCER_PROMPT_PROPERTY_EXAMPLES = 30
NONCANONICAL_PROMPT_PROPERTY_SEED = 20260711
PRODUCER_PROMPT_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/25-eval-harness.enabler/tests/"
    "test_producer_prompt.conformance.l1.py::"
    "test_materialized_prompt_changes_only_with_selected_section"
)


def _copy_workspace(tmp_path: Path, kind: str) -> EvalWorkspace:
    workspace_root = PRODUCER_PROMPT_FIXTURE_ROOT / kind / "repo"
    return copy_eval_workspace(
        tmp_path,
        fixture_root=PRODUCER_PROMPT_FIXTURE_ROOT,
        workspace_root=workspace_root,
    )


def _definition(workspace: EvalWorkspace) -> ProducerPromptDefinition:
    return load_producer_prompt_definition(
        workspace.eval_toml,
        repo_root=workspace.repo_root,
    )


def _producer_relatives(workspace: EvalWorkspace) -> tuple[str, ...]:
    return _definition(workspace).producer_relative_paths


def _producer_path(workspace: EvalWorkspace) -> Path:
    return _definition(workspace).producer_path


def _prompt_path(workspace: EvalWorkspace) -> Path:
    return workspace.eval_toml.parent / PROMPT_FILENAME


def _section_name(workspace: EvalWorkspace) -> str:
    section_name = _definition(workspace).section_name
    if section_name is None:
        raise ValueError("workspace has no producer section")
    return section_name


def _selected_section(workspace: EvalWorkspace) -> str:
    producer_path = _producer_path(workspace)
    return extract_named_producer_section(
        producer_path.read_text(encoding=UTF8_ENCODING),
        section_name=_section_name(workspace),
        producer_path=producer_path,
    )


def _unrelated_producer_text(workspace: EvalWorkspace) -> str:
    producer_text = _producer_path(workspace).read_text(encoding=UTF8_ENCODING)
    return producer_text.replace(_selected_section(workspace), "").strip()


def _section_body(section: str) -> str:
    lines = section.splitlines()
    return "\n".join(lines[1:-1]).strip()


def _variant_path(name: str) -> Path:
    return (
        PRODUCER_PROMPT_FIXTURE_ROOT
        / PRODUCER_SECTION_KIND
        / "variants"
        / f"{name.replace('_', '-')}.md"
    )


def _install_section_variant(workspace: EvalWorkspace, name: str) -> Path:
    return replace_workspace_file(
        workspace,
        relative_path=Path(_producer_relatives(workspace)[0]),
        fixture_path=_variant_path(name),
    )


def _materialize(workspace: EvalWorkspace) -> str:
    return materialize_prompt(
        workspace.eval_toml,
        repo_root=workspace.repo_root,
    ).read_text(encoding=UTF8_ENCODING)


def _assert_complete_producer_block(
    prompt: str,
    *,
    relative_path: str,
    producer_text: str,
) -> None:
    path_label = json.dumps(relative_path)
    start = PRODUCER_BOUNDARY_START_TEMPLATE.format(path_label=path_label)
    end = PRODUCER_BOUNDARY_END_TEMPLATE.format(path_label=path_label)
    block_start = prompt.index(start)
    block_end = prompt.index(end, block_start) + len(end)
    block = prompt[block_start:block_end]
    lines = block.splitlines()
    opening = lines[2]
    fence = opening.removesuffix(PRODUCER_FENCE_INFO_STRING)
    assert opening.endswith(PRODUCER_FENCE_INFO_STRING)
    assert fence and set(fence) == {PRODUCER_FENCE_CHARACTER}
    assert lines[-3] == fence
    longest_run = max(
        (
            len(match.group(0))
            for match in re.finditer(
                rf"{re.escape(PRODUCER_FENCE_CHARACTER)}+",
                producer_text,
            )
        ),
        default=0,
    )
    assert len(fence) > longest_run
    assert producer_text in block


def _cli_options() -> tuple[str, str]:
    options = [
        parameter
        for parameter in materialize_prompts_command.params
        if isinstance(parameter, click.Option)
    ]
    check = next(parameter for parameter in options if parameter.is_flag)
    repo_root = next(parameter for parameter in options if not parameter.is_flag)
    return repo_root.opts[0], check.opts[0]


@with_temp_workspace
def assert_materializes_prompt_from_named_producer_section(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    prompt_text = _materialize(workspace)
    definition = _definition(workspace)

    assert _selected_section(workspace) in prompt_text
    assert _unrelated_producer_text(workspace) not in prompt_text
    assert definition.producer_relative_path in prompt_text
    assert _section_name(workspace) in prompt_text


@with_temp_workspace
def assert_materializes_prompt_from_complete_producer_file(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_FILE_KIND)
    producer_text = _producer_path(workspace).read_text(encoding=UTF8_ENCODING)
    prompt_text = _materialize(workspace)
    relative_path = _producer_relatives(workspace)[0]

    assert producer_text in prompt_text
    assert relative_path in prompt_text
    _assert_complete_producer_block(
        prompt_text,
        relative_path=relative_path,
        producer_text=producer_text,
    )


@with_temp_workspace
def assert_materializes_prompt_from_ordered_complete_producer_files(
    tmp_path: Path,
) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_FILES_KIND)
    first_render = _materialize(workspace)
    materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
    second_render = _prompt_path(workspace).read_text(encoding=UTF8_ENCODING)

    cursor = 0
    producer_relatives = _producer_relatives(workspace)
    for relative_path in producer_relatives:
        producer_text = (workspace.repo_root / relative_path).read_text(
            encoding=UTF8_ENCODING
        )
        path_position = first_render.index(relative_path, cursor)
        content_position = first_render.index(producer_text, path_position)
        assert path_position < content_position
        cursor = content_position + len(producer_text)
        assert first_render.count(relative_path) == 2
        _assert_complete_producer_block(
            first_render,
            relative_path=relative_path,
            producer_text=producer_text,
        )
    assert second_render == first_render

    unterminated_path = workspace.repo_root / producer_relatives[0]
    unterminated_bytes = unterminated_path.read_bytes().rstrip(b"\r\n")
    unterminated_path.write_bytes(unterminated_bytes)
    unterminated_text = unterminated_bytes.decode(UTF8_ENCODING)
    rendered = materialize_prompt(
        workspace.eval_toml,
        repo_root=workspace.repo_root,
    ).read_text(encoding=UTF8_ENCODING)
    _assert_complete_producer_block(
        rendered,
        relative_path=producer_relatives[0],
        producer_text=unterminated_text,
    )


@with_temp_workspace
def assert_producer_files_check_detects_each_source_change(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_FILES_KIND)
    materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)

    for relative_path in _producer_relatives(workspace):
        producer_path = workspace.repo_root / relative_path
        original = producer_path.read_text(encoding=UTF8_ENCODING)
        producer_path.write_text(
            original + original,
            encoding=UTF8_ENCODING,
        )
        with pytest.raises(PromptMaterializationDrift, match=PROMPT_FILENAME):
            verify_materialized_prompt(
                workspace.eval_toml,
                repo_root=workspace.repo_root,
            )
        producer_path.write_text(original, encoding=UTF8_ENCODING)
        verify_materialized_prompt(
            workspace.eval_toml,
            repo_root=workspace.repo_root,
        )


@with_temp_workspace
def assert_invalid_producer_files_definitions_are_rejected(tmp_path: Path) -> None:
    source_workspace = _copy_workspace(tmp_path, PRODUCER_FILES_KIND)
    producer_relatives = _producer_relatives(source_workspace)
    for index, (producers, include_section, include_singular) in enumerate(
        _invalid_producer_files_definitions(tmp_path, producer_relatives)
    ):
        workspace = _copy_workspace(tmp_path / str(index), PRODUCER_FILES_KIND)
        set_toml_field(
            workspace.eval_toml,
            table=PROMPT_SOURCE_TABLE,
            field=PRODUCERS_FIELD,
            value=producers,
        )
        if include_section:
            set_toml_field(
                workspace.eval_toml,
                table=PROMPT_SOURCE_TABLE,
                field=SECTION_FIELD,
                value=SECTION_FIELD,
            )
        if include_singular:
            set_toml_field(
                workspace.eval_toml,
                table=PROMPT_SOURCE_TABLE,
                field=PRODUCER_FIELD,
                value=producer_relatives[0],
            )
        with pytest.raises(ProducerPromptError, match=PRODUCERS_FIELD):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


def _invalid_producer_files_definitions(
    tmp_path: Path,
    producer_relatives: tuple[str, ...],
) -> tuple[tuple[TomlValue, bool, bool], ...]:
    primary = producer_relatives[0]
    return (
        ([], False, False),
        ([primary, primary], False, False),
        ([primary, f"./{primary}"], False, False),
        ([missing_producer_path(primary)], False, False),
        ([EXIT_GENERAL_ERROR], False, False),
        ([str((tmp_path / primary).resolve())], False, False),
        ([outside_repository_path(primary)], False, False),
        (list(producer_relatives), True, False),
        (list(producer_relatives), False, True),
        (primary, False, False),
    )


@with_temp_workspace
def assert_producer_file_rejects_section_selector(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_FILE_KIND)
    set_toml_field(
        workspace.eval_toml,
        table=PROMPT_SOURCE_TABLE,
        field=SECTION_FIELD,
        value=SECTION_FIELD,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_complete_file_templates_reject_invalid_placeholders(
    tmp_path: Path,
) -> None:
    for kind, placeholder in (
        (PRODUCER_FILE_KIND, PRODUCER_FILE_PLACEHOLDER),
        (PRODUCER_FILES_KIND, PRODUCER_FILES_PLACEHOLDER),
    ):
        source_workspace = _copy_workspace(tmp_path / kind, kind)
        for index, replacement in enumerate(
            (
                "",
                f"{placeholder}\n{placeholder}",
                f"{_producer_relatives(source_workspace)[0]} {placeholder}",
            )
        ):
            workspace = _copy_workspace(tmp_path / kind / str(index), kind)
            definition = load_producer_prompt_definition(
                workspace.eval_toml,
                repo_root=workspace.repo_root,
            )
            replace_text_once(
                definition.template_path,
                old=placeholder,
                new=replacement,
            )
            with pytest.raises(ProducerPromptError, match=re.escape(placeholder)):
                materialize_prompt(
                    workspace.eval_toml,
                    repo_root=workspace.repo_root,
                )


@with_temp_workspace
def assert_check_accepts_current_materialized_prompt(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    _materialize(workspace)
    verify_materialized_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


def assert_materialized_prompt_changes_only_with_selected_section() -> None:
    @seed(PRODUCER_PROMPT_PROPERTY_SEED)
    @settings(max_examples=PRODUCER_PROMPT_PROPERTY_EXAMPLES)
    @given(
        rules=distinct_producer_rule_texts(),
    )
    def assertion(rules: tuple[str, str, str]) -> None:
        materialized_prompt_changes_only_with_selected_section(
            unrelated_rule=rules[0],
            updated_unrelated_rule=rules[1],
            updated_selected_rule=rules[2],
        )

    try:
        assertion()
    except AssertionError as error:
        error.add_note(f"Hypothesis seed: {PRODUCER_PROMPT_PROPERTY_SEED}")
        error.add_note(f"Replay path: {PRODUCER_PROMPT_PROPERTY_REPLAY_PATH}")
        raise


def materialized_prompt_changes_only_with_selected_section(
    *,
    unrelated_rule: str,
    updated_unrelated_rule: str,
    updated_selected_rule: str,
) -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = _copy_workspace(Path(temp_dir), PRODUCER_SECTION_KIND)
        producer_path = _producer_path(workspace)
        prompt_path = _prompt_path(workspace)
        selected_rule = _section_body(_selected_section(workspace))
        unrelated_rule_from_source = _section_body(_unrelated_producer_text(workspace))
        producer_text = producer_path.read_text(encoding=UTF8_ENCODING)
        assume(
            all(
                rule not in producer_text
                for rule in (
                    unrelated_rule,
                    updated_unrelated_rule,
                    updated_selected_rule,
                )
            )
        )
        replace_text_once(
            producer_path,
            old=unrelated_rule_from_source,
            new=unrelated_rule,
        )
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        original_prompt = prompt_path.read_text(encoding=UTF8_ENCODING)

        replace_text_once(
            producer_path,
            old=unrelated_rule,
            new=updated_unrelated_rule,
        )
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        assert prompt_path.read_text(encoding=UTF8_ENCODING) == original_prompt

        replace_text_once(
            producer_path,
            old=selected_rule,
            new=updated_selected_rule,
        )
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        updated_prompt = prompt_path.read_text(encoding=UTF8_ENCODING)

        assert updated_prompt != original_prompt
        assert updated_selected_rule in updated_prompt
        assert selected_rule not in updated_prompt


@with_temp_workspace
def assert_check_rejects_stale_materialized_prompt(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    prompt_path = _prompt_path(workspace)
    current_prompt = _materialize(workspace)
    prompt_path.write_text(current_prompt + current_prompt, encoding=UTF8_ENCODING)

    with pytest.raises(PromptMaterializationDrift, match=PROMPT_FILENAME):
        verify_materialized_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_materialization_rejects_prompt_path_outside_eval_dir(
    tmp_path: Path,
) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    set_toml_field(
        workspace.eval_toml,
        table=None,
        field=PROMPT_FIELD,
        value=outside_eval_prompt_path(PROMPT_FILENAME),
    )

    with pytest.raises(ProducerPromptError, match=PROMPT_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_materialization_rejects_prompt_template_alias(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    original_prompt = _materialize(workspace)
    set_toml_field(
        workspace.eval_toml,
        table=PROMPT_SOURCE_TABLE,
        field=TEMPLATE_FIELD,
        value=PROMPT_FILENAME,
    )

    with pytest.raises(ProducerPromptError, match=TEMPLATE_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
    assert _prompt_path(workspace).read_text(encoding=UTF8_ENCODING) == original_prompt


@with_temp_workspace
def assert_materialization_rejects_absolute_producer_path(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    absolute_path = _producer_path(workspace).resolve()
    set_toml_field(
        workspace.eval_toml,
        table=PROMPT_SOURCE_TABLE,
        field=PRODUCER_FIELD,
        value=str(absolute_path),
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_materialization_rejects_producer_path_outside_repo(
    tmp_path: Path,
) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    producer_relative = _producer_relatives(workspace)[0]
    set_toml_field(
        workspace.eval_toml,
        table=PROMPT_SOURCE_TABLE,
        field=PRODUCER_FIELD,
        value=outside_repository_path(producer_relative),
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
    assert workspace.repo_root.is_dir()


def assert_materialization_rejects_noncanonical_prompt_path() -> None:
    @seed(NONCANONICAL_PROMPT_PROPERTY_SEED)
    @settings(max_examples=PRODUCER_PROMPT_PROPERTY_EXAMPLES)
    @given(prompt_path=noncanonical_prompt_filenames())
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


def materialization_rejects_noncanonical_prompt_path(*, prompt_path: str) -> None:
    with TemporaryDirectory() as temp_dir:
        workspace = _copy_workspace(Path(temp_dir), PRODUCER_SECTION_KIND)
        set_toml_field(
            workspace.eval_toml,
            table=None,
            field=PROMPT_FIELD,
            value=prompt_path,
        )
        with pytest.raises(ProducerPromptError, match=MATERIALIZED_PROMPT_FILENAME):
            materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)
        assert not (workspace.eval_toml.parent / prompt_path).exists()


@with_temp_workspace
def assert_materialization_preserves_placeholder_text_inside_producer_section(
    tmp_path: Path,
) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    producer_path = _install_section_variant(workspace, "literal_placeholder")
    selected = extract_named_producer_section(
        producer_path.read_text(encoding=UTF8_ENCODING),
        section_name=_section_name(workspace),
        producer_path=producer_path,
    )
    prompt_text = materialize_prompt(
        workspace.eval_toml,
        repo_root=workspace.repo_root,
    ).read_text(encoding=UTF8_ENCODING)
    assert selected in prompt_text


@with_temp_workspace
def assert_missing_producer_section_is_rejected(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    producer_text = _producer_path(workspace).read_text(encoding=UTF8_ENCODING)
    missing_section = absent_section_name(
        _section_name(workspace),
        producer_text,
    )
    set_toml_field(
        workspace.eval_toml,
        table=PROMPT_SOURCE_TABLE,
        field=SECTION_FIELD,
        value=missing_section,
    )

    with pytest.raises(ProducerPromptError, match=missing_section):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_similar_attribute_names_do_not_match_section_name(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    _install_section_variant(workspace, "similar_attribute_names")

    with pytest.raises(ProducerPromptError, match=_section_name(workspace)):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_non_step_tags_do_not_match_section_name(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    _install_section_variant(workspace, "non_step_name")

    with pytest.raises(ProducerPromptError, match=_section_name(workspace)):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_selected_section_rejects_literal_step_closing_delimiter(
    tmp_path: Path,
) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    _install_section_variant(workspace, "literal_step_closing")

    with pytest.raises(ProducerPromptError):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_selected_section_preserves_nested_step_section(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    producer_path = _install_section_variant(workspace, "nested_step")
    selected = extract_named_producer_section(
        producer_path.read_text(encoding=UTF8_ENCODING),
        section_name=_section_name(workspace),
        producer_path=producer_path,
    )
    prompt = materialize_prompt(
        workspace.eval_toml,
        repo_root=workspace.repo_root,
    ).read_text(encoding=UTF8_ENCODING)
    assert selected in prompt


@with_temp_workspace
def assert_duplicate_producer_section_is_rejected(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    producer_path = _producer_path(workspace)
    producer_text = producer_path.read_text(encoding=UTF8_ENCODING)
    selected = extract_named_producer_section(
        producer_text,
        section_name=_section_name(workspace),
        producer_path=producer_path,
    )
    producer_path.write_text(
        f"{producer_text}\n{selected}\n",
        encoding=UTF8_ENCODING,
    )

    with pytest.raises(ProducerPromptError, match=_section_name(workspace)):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


@with_temp_workspace
def assert_unsupported_prompt_source_kind_is_rejected(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    unsupported_kind = unsupported_prompt_source_kind(PRODUCER_PROMPT_KINDS)
    set_toml_field(
        workspace.eval_toml,
        table=PROMPT_SOURCE_TABLE,
        field=KIND_FIELD,
        value=unsupported_kind,
    )

    with pytest.raises(ProducerPromptError, match=unsupported_kind):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


def assert_missing_prompt_source_fields_are_rejected(
    tmp_path: Path,
    omitted_field: str,
) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    remove_toml_field(
        workspace.eval_toml,
        table=PROMPT_SOURCE_TABLE,
        field=omitted_field,
    )
    with pytest.raises(ProducerPromptError, match=omitted_field):
        materialize_prompt(workspace.eval_toml, repo_root=workspace.repo_root)


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
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    repo_root_option, check_option = _cli_options()
    runner = CliRunner()

    write_result = runner.invoke(
        materialize_prompts_command,
        [
            str(workspace.eval_toml.parent),
            repo_root_option,
            str(workspace.repo_root),
        ],
    )
    assert write_result.exit_code == EXIT_SUCCESS
    assert PROMPT_FILENAME in write_result.output

    prompt_path = _prompt_path(workspace)
    materialized_prompt = prompt_path.read_text(encoding=UTF8_ENCODING)
    materialized_mtime_ns = prompt_path.stat().st_mtime_ns
    check_result = runner.invoke(
        materialize_prompts_command,
        [
            str(workspace.eval_toml.parent),
            repo_root_option,
            str(workspace.repo_root),
            check_option,
        ],
    )
    assert check_result.exit_code == EXIT_SUCCESS
    assert prompt_path.read_text(encoding=UTF8_ENCODING) == materialized_prompt
    assert prompt_path.stat().st_mtime_ns == materialized_mtime_ns

    stale_prompt = materialized_prompt + materialized_prompt
    prompt_path.write_text(stale_prompt, encoding=UTF8_ENCODING)
    stale_mtime_ns = prompt_path.stat().st_mtime_ns
    stale_result = runner.invoke(
        materialize_prompts_command,
        [
            str(workspace.eval_toml.parent),
            repo_root_option,
            str(workspace.repo_root),
            check_option,
        ],
    )
    assert stale_result.exit_code == EXIT_GENERAL_ERROR
    assert PROMPT_FILENAME in stale_result.output
    assert prompt_path.read_text(encoding=UTF8_ENCODING) == stale_prompt
    assert prompt_path.stat().st_mtime_ns == stale_mtime_ns


@with_temp_workspace
def assert_cli_materializes_nested_eval_roots(tmp_path: Path) -> None:
    workspace = _copy_workspace(tmp_path, PRODUCER_SECTION_KIND)
    repo_root_option, check_option = _cli_options()
    evals_root = workspace.eval_toml.parent.parent
    prompt_path = _prompt_path(workspace)
    runner = CliRunner()
    command_name = materialize_prompts_command.name
    assert command_name is not None

    write_result = runner.invoke(
        main,
        [command_name, str(evals_root), repo_root_option, str(workspace.repo_root)],
    )
    assert write_result.exit_code == EXIT_SUCCESS
    assert str(prompt_path) in write_result.output
    materialized_prompt = prompt_path.read_text(encoding=UTF8_ENCODING)
    materialized_mtime_ns = prompt_path.stat().st_mtime_ns

    check_result = runner.invoke(
        main,
        [
            command_name,
            str(evals_root),
            repo_root_option,
            str(workspace.repo_root),
            check_option,
        ],
    )
    assert check_result.exit_code == EXIT_SUCCESS
    assert str(prompt_path) in check_result.output
    assert prompt_path.read_text(encoding=UTF8_ENCODING) == materialized_prompt
    assert prompt_path.stat().st_mtime_ns == materialized_mtime_ns
