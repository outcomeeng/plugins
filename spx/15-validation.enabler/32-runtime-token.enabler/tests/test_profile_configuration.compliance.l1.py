"""Native configuration literals cannot use token-check exemptions."""

from pathlib import Path

from outcomeeng.distribution.contracts import SOURCE_ROOT_NAME
from outcomeeng.validation._steps import (
    EVALS_ROOT,
    RUNTIME_TOKEN_STEP,
    VALIDATION_STEPS,
    runtime_token_files,
)
from outcomeeng.validation.runtime_tokens import (
    PROFILE_CONFIGURATION_REMEDIATION,
    VIOLATION_REPORT_TEMPLATE,
    scan_configuration_paths,
    scan_paths,
)
from outcomeeng.validation.profile_configuration import (
    CONFIGURATION_ONLY_OPTION,
    eval_configuration_files,
    find_profile_literals,
)
from outcomeeng_testing.generators.profile_configuration import (
    native_field_assignments,
    native_value_prose,
    profile_selection_texts,
)
from outcomeeng_testing.harnesses.profile_validation import (
    run_configuration_guard,
    write_configuration_overrides,
    write_eval_configuration_overrides,
)
from outcomeeng_testing.harnesses.runtime_tokens import observe_source


def test_overrides_are_rejected_in_frontmatter_and_ignored_conditionals(
    tmp_path: Path,
) -> None:
    fixture = write_configuration_overrides(tmp_path)
    ignored = frozenset(path.relative_to(tmp_path).as_posix() for path in fixture.paths)
    selected = tuple(
        Path(path) for path in runtime_token_files(tmp_path / SOURCE_ROOT_NAME)
    )
    violations = scan_paths(selected, ignore=ignored, repo_root=tmp_path)

    assert fixture.placed
    assert set(selected) == set(fixture.paths)
    assert sorted(
        (violation.path, violation.line, violation.token) for violation in violations
    ) == sorted((placed.path, placed.line, placed.token) for placed in fixture.placed)


def test_profile_literals_report_profile_remediation() -> None:
    assignments = native_field_assignments()

    assert assignments
    for assignment in assignments:
        observed = observe_source(assignment.text)
        assert observed.violations
        assert PROFILE_CONFIGURATION_REMEDIATION in observed.output


def test_every_native_configuration_value_passes_as_ordinary_prose() -> None:
    sentences = native_value_prose()

    assert sentences
    for sentence in sentences:
        assert find_profile_literals(sentence) == []


def test_generated_configuration_requests_and_profile_selections_pass() -> None:
    texts = profile_selection_texts()

    assert texts
    for text in texts:
        assert find_profile_literals(text) == []


def test_eval_definitions_and_prompt_templates_report_each_model_literal(
    tmp_path: Path,
) -> None:
    fixture = write_eval_configuration_overrides(tmp_path)
    selected = eval_configuration_files(fixture.spec_root)
    violations = scan_configuration_paths(selected)

    assert fixture.placed
    assert set(selected) == {fixture.definition, fixture.prompt, fixture.template}
    assert sorted(
        (violation.path, violation.line, violation.token) for violation in violations
    ) == sorted((placed.path, placed.line, placed.token) for placed in fixture.placed)


def test_guard_command_reports_eval_literal_paths_and_lines(tmp_path: Path) -> None:
    fixture = write_eval_configuration_overrides(tmp_path)
    run = run_configuration_guard(eval_configuration_files(fixture.spec_root))

    assert fixture.placed
    assert run.exit_code != 0
    for placed in fixture.placed:
        assert (
            VIOLATION_REPORT_TEMPLATE.format(
                path=placed.path,
                line=placed.line,
                token=placed.token,
                remediation=PROFILE_CONFIGURATION_REMEDIATION,
            )
            in run.output
        )


def test_gate_guards_every_repository_eval_definition_and_prompt_template() -> None:
    boundary = RUNTIME_TOKEN_STEP.argv.index(CONFIGURATION_ONLY_OPTION)
    selected = eval_configuration_files(Path(EVALS_ROOT))

    assert RUNTIME_TOKEN_STEP in VALIDATION_STEPS
    assert selected
    assert RUNTIME_TOKEN_STEP.argv[boundary + 1 :] == tuple(
        str(path) for path in selected
    )
