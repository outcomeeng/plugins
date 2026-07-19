"""Resource and generated-domain harnesses for section producer prompts."""

from __future__ import annotations

from pathlib import Path
from shutil import copyfile, copytree

from click.testing import CliRunner, Result

from outcomeeng_evals.cli import main
from outcomeeng_evals.cli.commands.materialize_prompts import (
    materialize_prompts_command,
)
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.producer_prompt import (
    KIND_FIELD,
    MATERIALIZED_PROMPT_FILENAME,
    PRODUCER_FIELD,
    PRODUCER_FILE_KIND,
    PRODUCER_FILE_PLACEHOLDER,
    PRODUCER_PATH_PLACEHOLDER,
    PRODUCER_SECTION_KIND,
    PRODUCER_SECTION_NAME_PLACEHOLDER,
    PRODUCER_SECTION_PLACEHOLDER,
    PROMPT_SOURCE_TABLE,
    SECTION_FIELD,
    TEMPLATE_FIELD,
)

PROMPT_FILENAME = MATERIALIZED_PROMPT_FILENAME
PROMPT_TEMPLATE_FILENAME = "prompt.template.md"
PRODUCER_RELATIVE_PATH = "dist/claude/spec-tree/skills/audit-adr/SKILL.md"
COMPLETE_PRODUCER_FIXTURE_PATH = (
    Path(__file__).parent.parent / "fixtures" / "producer_prompt" / "base-skill.md"
)
SECTION_NAME = "audit_tag_validity"
UNRELATED_SECTION_NAME = "other_section"
SELECTED_RULE = "Evidence type must match the claim."
UNRELATED_RULE = "This surrounding section is not selected."
LITERAL_PRODUCER_SECTION_TOKEN = PRODUCER_SECTION_PLACEHOLDER
STALE_PROMPT = "stale prompt\n"
PROMPT_PATH_OUTSIDE_EVAL_DIRECTORY = "../../prompt.md"
PRODUCER_PATH_OUTSIDE_REPOSITORY = "../outside/SKILL.md"
UNSUPPORTED_PROMPT_SOURCE_KIND = "simulation"
LITERAL_STEP_CLOSING_DELIMITER = "Literal </step> delimiter in prose."
NESTED_STEP_NAME = "nested_step"
NESTED_STEP_BODY = "Nested body."


def invoke_materialize_prompts(
    eval_root: Path,
    *,
    repo_root: Path,
    check: bool,
) -> Result:
    """Invoke the source-owned materialize-prompts command."""
    command_name = materialize_prompts_command.name
    if command_name is None:
        raise RuntimeError("materialize-prompts command has no registered name")
    arguments = [
        command_name,
        str(eval_root),
        "--repo-root",
        str(repo_root),
    ]
    if check:
        arguments.append("--check")
    return CliRunner().invoke(main, arguments)


def write_eval_fixture(
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
    prompt_template_path: str = PROMPT_TEMPLATE_FILENAME,
    producer_relative_path: str = PRODUCER_RELATIVE_PATH,
    omitted_prompt_source_fields: tuple[str, ...] = (),
    producer_placeholder_count: int = 1,
) -> tuple[Path, Path]:
    """Write one producer prompt eval into temporary repository storage."""
    repo_root = tmp_path / "repo"
    eval_dir = repo_root / "spx" / "node" / "evals" / "rule"
    producer_path = repo_root / PRODUCER_RELATIVE_PATH
    eval_dir.mkdir(parents=True)
    producer_path.parent.mkdir(parents=True)

    producer_sections = [producer_section(UNRELATED_SECTION_NAME, UNRELATED_RULE)]
    if include_false_positive_attributes:
        producer_sections.extend(
            [
                producer_section_with_attribute(
                    attribute_name="data-name",
                    attribute_value=SECTION_NAME,
                    body=UNRELATED_RULE,
                ),
                producer_section_with_attribute(
                    attribute_name="noname",
                    attribute_value=SECTION_NAME,
                    body=UNRELATED_RULE,
                ),
            ]
        )
    if include_non_step_named_tag:
        producer_sections.append(producer_example(SECTION_NAME, UNRELATED_RULE))
    if include_named_section:
        producer_sections.append(producer_section(SECTION_NAME, selected_rule))
    if duplicate_section:
        producer_sections.append(producer_section(SECTION_NAME, selected_rule))
    producer_path.write_text("\n".join(producer_sections), encoding="utf-8")

    if prompt_template_path == PROMPT_FILENAME:
        (eval_dir / PROMPT_FILENAME).write_text(
            "existing prompt\n",
            encoding="utf-8",
        )
    else:
        (eval_dir / prompt_template_path).write_text(
            "\n".join(
                [
                    f"Producer: {PRODUCER_PATH_PLACEHOLDER}",
                    f"Section: {PRODUCER_SECTION_NAME_PLACEHOLDER}",
                    "",
                    *([PRODUCER_SECTION_PLACEHOLDER] * producer_placeholder_count),
                    "",
                ]
            ),
            encoding="utf-8",
        )
    prompt_source_lines = [
        f'{KIND_FIELD} = "{prompt_source_kind}"',
        f'{PRODUCER_FIELD} = "{producer_relative_path}"',
        f'{SECTION_FIELD} = "{section_name}"',
        f'{TEMPLATE_FIELD} = "{prompt_template_path}"',
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


def write_complete_producer_file_fixture(
    tmp_path: Path,
    *,
    producer_placeholder_count: int = 1,
) -> tuple[Path, Path]:
    """Write one whole-producer eval into temporary repository storage."""
    repo_root, eval_toml = write_eval_fixture(
        tmp_path,
        prompt_source_kind=PRODUCER_FILE_KIND,
    )
    copyfile(
        COMPLETE_PRODUCER_FIXTURE_PATH,
        repo_root / PRODUCER_RELATIVE_PATH,
    )
    (eval_toml.parent / PROMPT_TEMPLATE_FILENAME).write_text(
        "\n".join(
            [
                f"Producer: {PRODUCER_PATH_PLACEHOLDER}",
                "",
                *([PRODUCER_FILE_PLACEHOLDER] * producer_placeholder_count),
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_prompt_source_definition(
        eval_toml,
        prompt_source_kind=PRODUCER_FILE_KIND,
        include_section=False,
    )
    return repo_root, eval_toml


def write_producer_section_fixture_without_body(tmp_path: Path) -> tuple[Path, Path]:
    """Write one section eval whose template omits the selected section."""
    return write_eval_fixture(tmp_path, producer_placeholder_count=0)


def write_producer_section_fixture_with_repeated_body(
    tmp_path: Path,
) -> tuple[Path, Path]:
    """Write one section eval whose template repeats the selected section."""
    return write_eval_fixture(tmp_path, producer_placeholder_count=2)


def write_producer_file_fixture_without_body(tmp_path: Path) -> tuple[Path, Path]:
    """Write one whole-file eval whose template omits the producer body."""
    return write_complete_producer_file_fixture(
        tmp_path,
        producer_placeholder_count=0,
    )


def write_producer_file_fixture_with_repeated_body(
    tmp_path: Path,
) -> tuple[Path, Path]:
    """Write one whole-file eval whose template repeats the producer body."""
    return write_complete_producer_file_fixture(
        tmp_path,
        producer_placeholder_count=2,
    )


def write_external_eval_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Write one eval outside the temporary repository boundary."""
    repo_root, eval_toml = write_eval_fixture(tmp_path)
    external_eval_dir = tmp_path / "external" / "evals" / "rule"
    copytree(eval_toml.parent, external_eval_dir)
    return repo_root, external_eval_dir / EVAL_TOML_FILENAME


def write_prompt_source_definition(
    eval_toml: Path,
    *,
    prompt_source_kind: str,
    include_section: bool,
) -> None:
    """Replace one temporary eval's prompt-source definition."""
    prompt_source_lines = [
        f'{KIND_FIELD} = "{prompt_source_kind}"',
        f'{PRODUCER_FIELD} = "{PRODUCER_RELATIVE_PATH}"',
    ]
    if include_section:
        prompt_source_lines.append(f'{SECTION_FIELD} = "{SECTION_NAME}"')
    prompt_source_lines.append(f'{TEMPLATE_FIELD} = "{PROMPT_TEMPLATE_FILENAME}"')
    eval_toml.write_text(
        "\n".join(
            [
                'title = "producer prompt"',
                'cases = "cases.jsonl"',
                f'prompt = "{PROMPT_FILENAME}"',
                "",
                f"[{PROMPT_SOURCE_TABLE}]",
                *prompt_source_lines,
                "",
            ]
        ),
        encoding="utf-8",
    )


def producer_section(name: str, body: str) -> str:
    """Render one synthetic step section."""
    return "\n".join(
        [
            f'<step name="{name}">',
            "",
            body,
            "",
            "</step>",
        ]
    )


def producer_section_with_attribute(
    *,
    attribute_name: str,
    attribute_value: str,
    body: str,
) -> str:
    """Render one synthetic step with a noncanonical attribute."""
    return "\n".join(
        [
            f'<step {attribute_name}="{attribute_value}">',
            "",
            body,
            "",
            "</step>",
        ]
    )


def producer_example(name: str, body: str) -> str:
    """Render one synthetic non-step named element."""
    return "\n".join(
        [
            f'<example name="{name}">',
            "",
            body,
            "",
            "</example>",
        ]
    )
