from outcomeeng_testing.harnesses.scratch_paths import (
    portable_content_reports_nothing_and_succeeds,
    violation_reports_file_line_reference_and_failure,
)


def test_violation_reports_file_line_reference_and_failure() -> None:
    assert violation_reports_file_line_reference_and_failure()


def test_portable_content_reports_nothing_and_succeeds() -> None:
    assert portable_content_reports_nothing_and_succeeds()
