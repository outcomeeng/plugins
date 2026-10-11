"""Native configuration literals cannot use token-check exemptions."""

from pathlib import Path

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import (
    AgentProfile,
    MODEL_IDENTIFIERS,
    NATIVE_CONFIGURATION_FIELDS,
    PROFILE_FIELD,
    native_configuration_values,
    resolve_profile,
)
from outcomeeng.validation._steps import runtime_token_files
from outcomeeng.validation.runtime_tokens import (
    PROFILE_CONFIGURATION_REMEDIATION,
    scan_paths,
)
from outcomeeng.validation.profile_configuration import find_profile_literals
from outcomeeng_testing.generators.profile_binding import (
    AUTHORED_BINDINGS,
    BARE_NAME_BINDINGS,
    PLACEHOLDER_BINDINGS,
    READ_BINDINGS,
    SURROUNDING_CONTEXTS,
)
from outcomeeng_testing.harnesses.profile_validation import (
    write_configuration_overrides,
    write_literal_overrides,
)
from outcomeeng_testing.harnesses.runtime_tokens import observe_source


def test_overrides_are_rejected_in_frontmatter_and_ignored_conditionals(
    tmp_path: Path,
) -> None:
    paths = write_configuration_overrides(tmp_path)
    ignored = frozenset(path.relative_to(tmp_path).as_posix() for path in paths)
    selected = tuple(Path(path) for path in runtime_token_files(tmp_path / "src"))
    violations = scan_paths(selected, ignore=ignored, repo_root=tmp_path)

    assert set(selected) == set(paths)
    assert [
        (violation.path, violation.line, violation.token) for violation in violations
    ] == [(path, line, path.parent.name) for path in paths for line in (2, 5)]


def test_literal_frontmatter_and_model_identifiers_are_reported_with_path_and_line(
    tmp_path: Path,
) -> None:
    written = write_literal_overrides(tmp_path)
    selected = tuple(Path(path) for path in runtime_token_files(tmp_path / "src"))
    violations = scan_paths(selected, ignore=frozenset(), repo_root=tmp_path)

    assert {item.path for item in written} == set(selected)
    assert sorted((str(item.path), item.line) for item in written) == sorted(
        (str(violation.path), violation.line) for violation in violations
    )


def test_profile_literals_report_profile_remediation() -> None:
    configuration = native_configuration_values(resolve_profile(Target.CODEX))
    model_field = next(
        field for field, value in configuration.items() if value in MODEL_IDENTIFIERS
    )
    observed = observe_source(f'{model_field} = "{configuration[model_field]}"')

    assert observed.violations
    assert PROFILE_CONFIGURATION_REMEDIATION in observed.output


def test_profile_requests_and_ordinary_prose_pass() -> None:
    configuration = native_configuration_values(resolve_profile(Target.CODEX))
    model_field = next(
        field for field, value in configuration.items() if value in MODEL_IDENTIFIERS
    )
    assert (
        find_profile_literals(
            f"Select a {model_field} with high effort.\n"
            f"{{{{! profile_config('{AgentProfile.STANDARD}') !}}}}\n"
            f"{PROFILE_FIELD}: {AgentProfile.STANDARD}"
        )
        == []
    )


def test_decision_follows_binding_form_in_every_surrounding_context() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for prefix, suffix in SURROUNDING_CONTEXTS:
            for binding in AUTHORED_BINDINGS:
                line = f"{prefix}{field} = {binding}{suffix}"
                assert find_profile_literals(line) == [(1, field)]
            for binding in READ_BINDINGS:
                line = f"{prefix}{field} = {binding}{suffix}"
                assert find_profile_literals(line) == []


def test_placeholder_bindings_are_no_assignment_in_every_surrounding_context() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for prefix, suffix in SURROUNDING_CONTEXTS:
            for binding in PLACEHOLDER_BINDINGS:
                line = f"{prefix}{field} = {binding}{suffix}"
                assert find_profile_literals(line) == []


def test_bare_name_bindings_are_assignments_in_every_surrounding_context() -> None:
    for field in NATIVE_CONFIGURATION_FIELDS:
        for prefix, suffix in SURROUNDING_CONTEXTS:
            for binding in BARE_NAME_BINDINGS:
                line = f"{prefix}{field} = {binding}{suffix}"
                assert find_profile_literals(line) == [(1, field)]
