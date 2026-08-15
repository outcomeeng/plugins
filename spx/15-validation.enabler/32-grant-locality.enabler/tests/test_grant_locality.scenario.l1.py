from outcomeeng_testing.harnesses.grant_locality import (
    observe_escaping_scan,
    observe_local_scan,
    observe_local_skill_files,
)


def test_escaping_grant_reports_file_line_reference_and_failure() -> None:
    observed = observe_escaping_scan()

    assert observed.exit_code != 0, (
        f"a skill granting a path outside its directory exited {observed.exit_code}"
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
        f"grant {violation.reference!r} missing from diagnostic: {observed.stdout!r}"
    )


def test_local_grants_report_nothing_and_succeed() -> None:
    observed = observe_local_scan()

    assert observed.exit_code == 0, (
        f"local grants exited {observed.exit_code}: {observed.stdout!r}"
    )
    assert observed.stdout == "", f"local grants reported {observed.stdout!r}"
    assert observed.violations == (), (
        f"local grants produced violations {observed.violations!r}"
    )


def test_a_body_declaration_is_not_read_as_a_grant() -> None:
    """A skill whose body writes the prohibited declaration still passes.

    Its frontmatter grants are local. A rule reading past the frontmatter fails
    the standard that documents the rule, and a documented prohibition is the
    one place the prohibited text is expected to appear.
    """
    for observed in observe_local_skill_files():
        assert observed.exit_code == 0, (
            f"{observed.path} exited {observed.exit_code}: {observed.stdout!r}"
        )
        assert observed.violations == (), (
            f"{observed.path} produced violations {observed.violations!r}"
        )
