from outcomeeng_testing.harnesses.grant_locality import (
    observe_escaping_scan,
    observe_local_scan,
    observe_local_skill_files,
)


def test_escaping_grant_reports_file_line_reference_and_failure() -> None:
    observed, expected = observe_escaping_scan()

    assert observed.exit_code != 0, (
        f"a skill granting a path outside its directory exited {observed.exit_code}"
    )
    assert len(observed.violations) == 1, (
        f"one escaping grant produced {observed.violations!r}"
    )
    # Every expectation comes from the generator's own composition of the file,
    # never from the scan that produced the diagnostic: a line count or a
    # captured reference the validator gets wrong would otherwise satisfy the
    # check by being wrong in both places at once.
    assert str(observed.path) in observed.stdout, (
        f"file missing from diagnostic: {observed.stdout!r}"
    )
    assert f":{expected.declaration_line}:" in observed.stdout, (
        f"line {expected.declaration_line} missing from diagnostic: {observed.stdout!r}"
    )
    assert expected.variable in observed.stdout, (
        f"variable {expected.variable!r} missing from diagnostic: {observed.stdout!r}"
    )
    assert expected.parent_segment in observed.stdout, (
        f"escaping segment missing from diagnostic: {observed.stdout!r}"
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
