from pathlib import Path

from outcomeeng_testing.harnesses.document_levels import (
    UNTITLED_DOCUMENT,
    load_document_levels,
    run_levels_command,
)

module = load_document_levels()
VALID_LEVEL = str(next(iter(module.Level)).value)


def test_missing_title_names_the_expected_title_form() -> None:
    observation = run_levels_command(
        module, ["--level", VALID_LEVEL, str(UNTITLED_DOCUMENT)]
    )

    assert observation.exit_code == module.EXIT_FAILURE
    assert f"{module.TITLE_PREFIX}<title>" in observation.stderr


def test_missing_file_names_the_path(tmp_path: Path) -> None:
    absent = tmp_path / "absent.md"

    observation = run_levels_command(module, ["--level", VALID_LEVEL, str(absent)])

    assert observation.exit_code == module.EXIT_FAILURE
    assert absent.as_posix() in observation.stderr


def test_invalid_level_names_the_allowed_levels() -> None:
    invalid = str(max(level.value for level in module.Level) + 1)
    allowed = ", ".join(str(level.value) for level in module.Level)

    observation = run_levels_command(
        module, ["--level", invalid, str(UNTITLED_DOCUMENT)]
    )

    assert observation.exit_code == module.EXIT_FAILURE
    assert allowed in observation.stderr
