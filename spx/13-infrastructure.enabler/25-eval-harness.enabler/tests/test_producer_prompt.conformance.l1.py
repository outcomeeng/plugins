"""Conformance evidence for producer-derived eval prompt materialization."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng_evals.cli import main
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    PRODUCER_FIELD,
    PRODUCER_SECTION_KIND,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
    PromptMaterializationDrift,
    ProducerPromptError,
    materialize_prompt,
    verify_materialized_prompt,
)


PROMPT_FILENAME = "prompt.md"
PROMPT_TEMPLATE_FILENAME = "prompt.template.md"
PRODUCER_RELATIVE_PATH = "dist/claude/spec-tree/skills/audit-adr/SKILL.md"
SECTION_NAME = "audit_tag_validity"
SELECTED_RULE = "Evidence type must match the claim."
UNRELATED_RULE = "This surrounding section is not selected."
LITERAL_PRODUCER_SECTION_TOKEN = "{producer_section}"
EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
RULE_TEXT = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cc", "Cs"),
        blacklist_characters=["<", ">", "\x00"],
    ),
    min_size=1,
    max_size=80,
)
RULE_TOKEN_SUFFIX = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"),
    ),
    min_size=1,
    max_size=32,
)


def test_materializes_prompt_from_named_producer_section(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(tmp_path)

    materialize_prompt(eval_toml, repo_root=repo_root)

    prompt_text = (eval_toml.parent / PROMPT_FILENAME).read_text(encoding="utf-8")
    assert SELECTED_RULE in prompt_text
    assert UNRELATED_RULE not in prompt_text
    assert PRODUCER_RELATIVE_PATH in prompt_text
    assert SECTION_NAME in prompt_text


def test_check_accepts_current_materialized_prompt(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(tmp_path)
    materialize_prompt(eval_toml, repo_root=repo_root)

    verify_materialized_prompt(eval_toml, repo_root=repo_root)


@given(
    rule_suffix=RULE_TOKEN_SUFFIX,
    unrelated_rule=RULE_TEXT,
    updated_unrelated_rule=RULE_TEXT,
)
@settings(max_examples=30)
def test_materialized_prompt_changes_only_with_selected_section(
    rule_suffix: str,
    unrelated_rule: str,
    updated_unrelated_rule: str,
) -> None:
    selected_rule = f"selected-token-{rule_suffix}-end"
    updated_selected_rule = f"updated-token-{rule_suffix}-end"
    with TemporaryDirectory() as temp_dir:
        repo_root, eval_toml = _write_eval_fixture(Path(temp_dir))
        producer_path = repo_root / PRODUCER_RELATIVE_PATH
        prompt_path = eval_toml.parent / PROMPT_FILENAME
        producer_path.write_text(
            "\n".join(
                [
                    _producer_section("other_section", unrelated_rule),
                    _producer_section(SECTION_NAME, selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)
        original_prompt = prompt_path.read_text(encoding="utf-8")

        producer_path.write_text(
            "\n".join(
                [
                    _producer_section("other_section", updated_unrelated_rule),
                    _producer_section(SECTION_NAME, selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)

        assert prompt_path.read_text(encoding="utf-8") == original_prompt

        producer_path.write_text(
            "\n".join(
                [
                    _producer_section("other_section", updated_unrelated_rule),
                    _producer_section(SECTION_NAME, updated_selected_rule),
                ]
            ),
            encoding="utf-8",
        )
        materialize_prompt(eval_toml, repo_root=repo_root)
        updated_prompt = prompt_path.read_text(encoding="utf-8")

        assert updated_prompt != original_prompt
        assert updated_selected_rule in updated_prompt
        assert selected_rule not in updated_prompt


def test_check_rejects_stale_materialized_prompt(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(tmp_path)
    (eval_toml.parent / PROMPT_FILENAME).write_text("stale prompt\n", encoding="utf-8")

    with pytest.raises(PromptMaterializationDrift, match=PROMPT_FILENAME):
        verify_materialized_prompt(eval_toml, repo_root=repo_root)


def test_materialization_rejects_prompt_path_outside_eval_dir(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(tmp_path, prompt_path="../../prompt.md")

    with pytest.raises(ProducerPromptError, match="prompt"):
        materialize_prompt(eval_toml, repo_root=repo_root)


def test_materialization_rejects_absolute_producer_path(tmp_path: Path) -> None:
    absolute_path = tmp_path / "repo" / PRODUCER_RELATIVE_PATH
    repo_root, eval_toml = _write_eval_fixture(
        tmp_path,
        producer_relative_path=str(absolute_path),
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)


def test_materialization_rejects_producer_path_outside_repo(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = _write_eval_fixture(
        tmp_path,
        producer_relative_path="../outside/SKILL.md",
    )

    with pytest.raises(ProducerPromptError, match=PRODUCER_FIELD):
        materialize_prompt(eval_toml, repo_root=repo_root)
    assert repo_root.is_dir()


def test_materialization_preserves_placeholder_text_inside_producer_section(
    tmp_path: Path,
) -> None:
    repo_root, eval_toml = _write_eval_fixture(
        tmp_path,
        selected_rule=LITERAL_PRODUCER_SECTION_TOKEN,
    )

    materialize_prompt(eval_toml, repo_root=repo_root)

    prompt_text = (eval_toml.parent / PROMPT_FILENAME).read_text(encoding="utf-8")
    assert prompt_text.count(LITERAL_PRODUCER_SECTION_TOKEN) == 1


def test_missing_producer_section_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(tmp_path, section_name="missing")

    with pytest.raises(ProducerPromptError, match="missing"):
        materialize_prompt(eval_toml, repo_root=repo_root)


def test_similar_attribute_names_do_not_match_section_name(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(
        tmp_path,
        include_named_section=False,
        include_false_positive_attributes=True,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


def test_non_step_tags_do_not_match_section_name(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(
        tmp_path,
        include_named_section=False,
        include_non_step_named_tag=True,
    )

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


def test_duplicate_producer_section_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(tmp_path, duplicate_section=True)

    with pytest.raises(ProducerPromptError, match=SECTION_NAME):
        materialize_prompt(eval_toml, repo_root=repo_root)


def test_unsupported_prompt_source_kind_is_rejected(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(
        tmp_path, prompt_source_kind="simulation"
    )

    with pytest.raises(ProducerPromptError, match="simulation"):
        materialize_prompt(eval_toml, repo_root=repo_root)


@pytest.mark.parametrize(
    "omitted_field",
    (KIND_FIELD, PRODUCER_FIELD, SECTION_FIELD, TEMPLATE_FIELD),
)
def test_missing_prompt_source_fields_are_rejected(
    tmp_path: Path,
    omitted_field: str,
) -> None:
    repo_root, eval_toml = _write_eval_fixture(
        tmp_path,
        omitted_prompt_source_fields=(omitted_field,),
    )

    with pytest.raises(ProducerPromptError, match=omitted_field):
        materialize_prompt(eval_toml, repo_root=repo_root)


def test_cli_materializes_and_checks_prompt_drift(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(tmp_path)
    runner = CliRunner()

    write_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(eval_toml.parent),
            "--repo-root",
            str(repo_root),
        ],
    )

    assert write_result.exit_code == EXIT_SUCCESS
    assert PROMPT_FILENAME in write_result.output

    prompt_path = eval_toml.parent / PROMPT_FILENAME
    materialized_prompt = prompt_path.read_text(encoding="utf-8")
    materialized_mtime_ns = prompt_path.stat().st_mtime_ns

    check_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(eval_toml.parent),
            "--repo-root",
            str(repo_root),
            "--check",
        ],
    )

    assert check_result.exit_code == EXIT_SUCCESS
    assert prompt_path.read_text(encoding="utf-8") == materialized_prompt
    assert prompt_path.stat().st_mtime_ns == materialized_mtime_ns

    prompt_path.write_text("stale prompt\n", encoding="utf-8")
    stale_mtime_ns = prompt_path.stat().st_mtime_ns

    stale_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(eval_toml.parent),
            "--repo-root",
            str(repo_root),
            "--check",
        ],
    )

    assert stale_result.exit_code == EXIT_GENERAL_ERROR
    assert PROMPT_FILENAME in stale_result.output
    assert prompt_path.read_text(encoding="utf-8") == "stale prompt\n"
    assert prompt_path.stat().st_mtime_ns == stale_mtime_ns


def test_cli_materializes_nested_eval_roots(tmp_path: Path) -> None:
    repo_root, eval_toml = _write_eval_fixture(tmp_path)
    evals_root = repo_root / "spx" / "node" / "evals"
    prompt_path = eval_toml.parent / PROMPT_FILENAME
    runner = CliRunner()

    write_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(evals_root),
            "--repo-root",
            str(repo_root),
        ],
    )

    assert write_result.exit_code == EXIT_SUCCESS
    assert str(prompt_path) in write_result.output
    materialized_prompt = prompt_path.read_text(encoding="utf-8")
    materialized_mtime_ns = prompt_path.stat().st_mtime_ns

    check_result = runner.invoke(
        main,
        [
            "materialize-prompts",
            str(evals_root),
            "--repo-root",
            str(repo_root),
            "--check",
        ],
    )

    assert check_result.exit_code == EXIT_SUCCESS
    assert str(prompt_path) in check_result.output
    assert prompt_path.read_text(encoding="utf-8") == materialized_prompt
    assert prompt_path.stat().st_mtime_ns == materialized_mtime_ns


def _write_eval_fixture(
    tmp_path: Path,
    *,
    section_name: str = SECTION_NAME,
    selected_rule: str = SELECTED_RULE,
    duplicate_section: bool = False,
    include_named_section: bool = True,
    include_false_positive_attributes: bool = False,
    include_non_step_named_tag: bool = False,
    prompt_source_kind: str = PRODUCER_SECTION_KIND,
    prompt_path: str = PROMPT_FILENAME,
    producer_relative_path: str = PRODUCER_RELATIVE_PATH,
    omitted_prompt_source_fields: tuple[str, ...] = (),
) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    eval_dir = repo_root / "spx" / "node" / "evals" / "rule"
    producer_path = repo_root / PRODUCER_RELATIVE_PATH
    eval_dir.mkdir(parents=True)
    producer_path.parent.mkdir(parents=True)

    producer_sections = [_producer_section("other_section", UNRELATED_RULE)]
    if include_false_positive_attributes:
        producer_sections.extend(
            [
                _producer_section_with_attribute(
                    attribute_name="data-name",
                    attribute_value=SECTION_NAME,
                    body=UNRELATED_RULE,
                ),
                _producer_section_with_attribute(
                    attribute_name="noname",
                    attribute_value=SECTION_NAME,
                    body=UNRELATED_RULE,
                ),
            ]
        )
    if include_non_step_named_tag:
        producer_sections.append(_producer_example(SECTION_NAME, UNRELATED_RULE))
    if include_named_section:
        producer_sections.append(_producer_section(SECTION_NAME, selected_rule))
    if duplicate_section:
        producer_sections.append(_producer_section(SECTION_NAME, selected_rule))
    producer_path.write_text("\n".join(producer_sections), encoding="utf-8")

    (eval_dir / PROMPT_TEMPLATE_FILENAME).write_text(
        "\n".join(
            [
                "Producer: {producer_path}",
                "Section: {producer_section_name}",
                "",
                "{producer_section}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    prompt_source_lines = [
        f'{KIND_FIELD} = "{prompt_source_kind}"',
        f'{PRODUCER_FIELD} = "{producer_relative_path}"',
        f'{SECTION_FIELD} = "{section_name}"',
        f'{TEMPLATE_FIELD} = "{PROMPT_TEMPLATE_FILENAME}"',
    ]
    omitted = set(omitted_prompt_source_fields)
    (eval_dir / EVAL_TOML_FILENAME).write_text(
        "\n".join(
            [
                'title = "producer prompt"',
                'cases = "cases.jsonl"',
                f'prompt = "{prompt_path}"',
                "",
                f"[{PROMPT_SOURCE_TABLE}]",
                *[
                    line
                    for line in prompt_source_lines
                    if line.split(" = ", 1)[0] not in omitted
                ],
                "",
            ]
        ),
        encoding="utf-8",
    )
    (eval_dir / "cases.jsonl").write_text("", encoding="utf-8")
    return repo_root, eval_dir / EVAL_TOML_FILENAME


def _producer_section(name: str, body: str) -> str:
    return "\n".join(
        [
            f'<step name="{name}">',
            "",
            body,
            "",
            "</step>",
        ]
    )


def _producer_section_with_attribute(
    *,
    attribute_name: str,
    attribute_value: str,
    body: str,
) -> str:
    return "\n".join(
        [
            f'<step {attribute_name}="{attribute_value}">',
            "",
            body,
            "",
            "</step>",
        ]
    )


def _producer_example(name: str, body: str) -> str:
    return "\n".join(
        [
            f'<example name="{name}">',
            "",
            body,
            "",
            "</example>",
        ]
    )
