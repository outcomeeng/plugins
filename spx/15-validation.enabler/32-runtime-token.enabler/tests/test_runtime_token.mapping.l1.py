"""The linked evidence owns verdicts over every source-owned token case."""

from pathlib import Path

from outcomeeng.distribution.contracts import format_runtime_token
from outcomeeng.validation.runtime_tokens import (
    RUNTIME_TOKEN_IGNORE,
    VIOLATION_REPORT_TEMPLATE,
    forbidden_names,
)
from outcomeeng_testing.generators.runtime_tokens import (
    empty_enforcement_registry,
    inverted_enforcement_registry_probe,
    lint_enforced_runtime_names,
    raw_token_source,
    runtime_conditional_cases,
)
from outcomeeng_testing.harnesses.runtime_tokens import observe_source


def test_raw_tokens_report_file_line_name_and_failure() -> None:
    cases = lint_enforced_runtime_names()

    assert cases
    for case in cases:
        observed = observe_source(raw_token_source(case))
        expected_line = observed.source.splitlines().index(case.name) + 1
        assert [(v.path, v.line, v.token) for v in observed.violations] == [
            (observed.path, expected_line, case.name)
        ]
        assert observed.exit_code != 0
        for violation in observed.violations:
            assert (
                VIOLATION_REPORT_TEMPLATE.format(
                    path=violation.path,
                    line=violation.line,
                    token=violation.token,
                    remediation=violation.remediation,
                )
                in observed.output
            )


def test_token_expressions_and_matching_conditionals_pass() -> None:
    cases = lint_enforced_runtime_names()
    conditional_cases = runtime_conditional_cases()

    assert cases
    assert conditional_cases
    assert all(case.matching_sources for case in conditional_cases)
    assert any(case.mismatching_sources for case in conditional_cases)
    for case in cases:
        observed = observe_source(format_runtime_token(case.kind, case.capability))
        assert observed.violations == ()
        assert observed.exit_code == 0
        assert observed.output == ""
    for conditional_case in conditional_cases:
        for source in conditional_case.matching_sources:
            observed = observe_source(source)
            assert observed.violations == ()
            assert observed.exit_code == 0
            assert observed.output == ""
        for source in conditional_case.mismatching_sources:
            observed = observe_source(source)
            assert observed.violations
            assert observed.exit_code != 0
            assert conditional_case.name in observed.output


def test_every_declared_exemption_applies_only_when_enabled() -> None:
    cases = lint_enforced_runtime_names()

    assert cases
    assert RUNTIME_TOKEN_IGNORE
    for case in cases:
        for relative in RUNTIME_TOKEN_IGNORE:
            observed = observe_source(
                raw_token_source(case), relative_path=Path(relative)
            )
            assert observed.ignored
            assert observed.violations == ()
            assert observed.exit_code == 0
            assert observed.output == ""
            assert [v.token for v in observed.unignored_violations] == [case.name]


def test_registry_injection_changes_every_scanner_layer() -> None:
    probe = inverted_enforcement_registry_probe()
    assert probe.enforced_names
    assert probe.excluded_names
    source = "\n".join((*probe.enforced_names, *probe.excluded_names))
    observed = observe_source(source, registry=probe.registry)
    assert frozenset(forbidden_names(registry=probe.registry)) == frozenset(
        probe.enforced_names
    )
    assert {v.token for v in observed.violations} == set(probe.enforced_names)
    assert observed.exit_code != 0
    assert all(name in observed.output for name in probe.enforced_names)
    empty = observe_source(source, registry=empty_enforcement_registry())
    assert empty.violations == ()
    assert empty.exit_code == 0
    assert empty.output == ""
