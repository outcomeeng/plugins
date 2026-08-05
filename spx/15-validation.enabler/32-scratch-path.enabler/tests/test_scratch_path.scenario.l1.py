from outcomeeng_testing.harnesses.scratch_paths import (
    observe_portable_scan,
    observe_violation_scan,
)


def test_violation_reports_file_line_reference_and_failure() -> None:
    observed = observe_violation_scan()

    assert observed.exit_code != 0, (
        f"a file naming a fixed temporary path exited {observed.exit_code}"
    )
    (violation,) = observed.violations
    # Check the printed diagnostic literally carries each part the assertion
    # names, rather than comparing it to the formatter that produced it.
    assert str(observed.path) in observed.stdout, (
        f"file missing from diagnostic: {observed.stdout!r}"
    )
    assert f":{violation.line}:" in observed.stdout, (
        f"line {violation.line} missing from diagnostic: {observed.stdout!r}"
    )
    assert violation.reference in observed.stdout, (
        f"path {violation.reference!r} missing from diagnostic: {observed.stdout!r}"
    )


def test_portable_content_reports_nothing_and_succeeds() -> None:
    observed = observe_portable_scan()

    assert observed.exit_code == 0, (
        f"portable content exited {observed.exit_code}: {observed.stdout!r}"
    )
    assert observed.stdout == "", f"portable content reported {observed.stdout!r}"
    assert observed.violations == (), (
        f"portable content produced violations {observed.violations!r}"
    )
