"""Level 1 compliance evidence for skill-reference validation.

Each test exercises a rule of [skill-reference.md](../skill-reference.md)
against real violating files and conforming files that show no false positive.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.skill_reference import (
    EXEMPTED_REFERENCES,
    HARNESS_COMMANDS,
    INERT_FIXTURE_ROOT,
    SCAN_ROOTS,
)
from outcomeeng_testing.harnesses.skill_reference import (
    build_marketplace,
    fixture_path,
    run_validator,
    scan_references,
    scan_text_references,
    write_file,
)


def test_unshipped_reference_fails_in_every_recognized_form(tmp_path: Path) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    qualified = write_file(
        tmp_path, "src/plugins/alpha/qualified.md", "Run alpha:audit-gadget.\n"
    )
    slash = write_file(
        tmp_path, "src/plugins/alpha/slash.md", "Run /audit-gadget now.\n"
    )
    placeholder = write_file(
        tmp_path, "src/plugins/alpha/placeholder.md", "Run /review-{type} now.\n"
    )

    for path, reference in (
        (qualified, "alpha:audit-gadget"),
        (slash, "/audit-gadget"),
        (placeholder, "/review-{type}"),
    ):
        run = run_validator(tmp_path, [path])
        assert run.exit_code != 0
        (report,) = run.lines
        assert str(path) in report
        assert reference in report


def test_exemption_mapping_passes_only_the_references_it_names(
    tmp_path: Path,
) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    payload = fixture_path("unshipped_references.md")
    change = next(iter(EXEMPTED_REFERENCES.values()))

    omitting = scan_references(tmp_path, [payload], {})
    naming_qualified = scan_references(
        tmp_path, [payload], {"alpha:audit-gadget": change}
    )
    naming_slash = scan_references(tmp_path, [payload], {"/audit-gizmo": change})
    naming_both = scan_references(
        tmp_path,
        [payload],
        {"alpha:audit-gadget": change, "/audit-gizmo": change},
    )
    naming_other = scan_references(tmp_path, [payload], {"/audit-widget": change})

    assert omitting == ("alpha:audit-gadget", "/audit-gizmo")
    assert naming_qualified == ("/audit-gizmo",)
    assert naming_slash == ("alpha:audit-gadget",)
    assert naming_both == ()
    assert naming_other == omitting


def test_exemption_names_the_exact_reference_only(tmp_path: Path) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    change = next(iter(EXEMPTED_REFERENCES.values()))

    references = scan_text_references(
        tmp_path,
        "Run /audit-gadget and /audit-gadget-extra and alpha:audit-gadget.\n",
        {"/audit-gadget": change},
    )

    assert references == ("/audit-gadget-extra", "alpha:audit-gadget")


def test_unshipped_name_as_path_segment_is_not_a_slash_invocation(
    tmp_path: Path,
) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    content = write_file(
        tmp_path,
        "src/plugins/alpha/path.md",
        "See docs/audit-gadget/notes.md for details.\n",
    )

    run = run_validator(tmp_path, [content])

    assert run.lines == ()
    assert run.exit_code == 0


def test_alternation_expands_each_member_and_placeholders_need_a_matching_name(
    tmp_path: Path,
) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-code", "audit-tests"]})
    alternation = write_file(
        tmp_path,
        "src/plugins/alpha/alternation.md",
        "Run /audit-{code|tests|architecture}.\n",
    )
    complete = write_file(
        tmp_path, "src/plugins/alpha/complete.md", "Run /audit-{code|tests}.\n"
    )
    matching = write_file(
        tmp_path, "src/plugins/alpha/matching.md", "Run /audit-{type}.\n"
    )
    unmatched = write_file(
        tmp_path, "src/plugins/alpha/unmatched.md", "Run /review-{type}.\n"
    )
    empty_stand_in = write_file(
        tmp_path, "src/plugins/alpha/empty.md", "Run /audit-code{type}.\n"
    )

    missing_member = run_validator(tmp_path, [alternation])
    assert missing_member.exit_code != 0
    (missing_member_report,) = missing_member.lines
    assert "/audit-{code|tests|architecture}" in missing_member_report
    assert "audit-architecture" in missing_member_report

    for passing in (complete, matching):
        run = run_validator(tmp_path, [passing])
        assert run.lines == ()
        assert run.exit_code == 0

    for failing in (unmatched, empty_stand_in):
        run = run_validator(tmp_path, [failing])
        assert run.exit_code != 0
        assert len(run.lines) == 1


def test_shipped_set_follows_skill_directories_and_catalog(tmp_path: Path) -> None:
    content_text = "Run ghost:audit-widget and /audit-widget.\n"
    uncataloged = tmp_path / "uncataloged"
    cataloged = tmp_path / "cataloged"
    renamed = tmp_path / "renamed"
    build_marketplace(
        uncataloged, {"alpha": ["audit-widget"], "ghost": ["audit-widget"]}, ["alpha"]
    )
    build_marketplace(cataloged, {"alpha": ["audit-widget"], "ghost": ["audit-widget"]})
    build_marketplace(renamed, {"alpha": ["audit-gizmo"]})

    uncataloged_run = run_validator(
        uncataloged,
        [write_file(uncataloged, "src/plugins/alpha/notes.md", content_text)],
    )
    cataloged_run = run_validator(
        cataloged, [write_file(cataloged, "src/plugins/alpha/notes.md", content_text)]
    )
    renamed_run = run_validator(
        renamed, [write_file(renamed, "src/plugins/alpha/notes.md", content_text)]
    )

    assert uncataloged_run.exit_code != 0
    assert any("ghost:audit-widget" in line for line in uncataloged_run.lines)
    assert cataloged_run.lines == ()
    assert cataloged_run.exit_code == 0
    assert renamed_run.exit_code != 0
    assert any("/audit-widget" in line for line in renamed_run.lines)


def test_scan_covers_every_declared_root_and_excludes_changelogs(
    tmp_path: Path,
) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    violating = [
        write_file(tmp_path, f"{root}/violation.md", "Run /audit-gadget now.\n")
        for root in SCAN_ROOTS
    ]
    write_file(
        tmp_path,
        "src/plugins/alpha/CHANGELOG.md",
        "Renamed /audit-gadget to /audit-widget.\n",
    )
    write_file(tmp_path, "docs/outside.md", "Run /audit-gadget now.\n")

    run = run_validator(tmp_path)

    assert run.exit_code != 0
    assert len(run.lines) == len(violating)
    for path in violating:
        assert sum(str(path) in line for line in run.lines) == 1


def test_inert_fixtures_are_excluded_from_the_scan(tmp_path: Path) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    fixture = write_file(
        tmp_path, f"{INERT_FIXTURE_ROOT}/violation.md", "Run /audit-gadget now.\n"
    )
    scanned = write_file(
        tmp_path, f"{SCAN_ROOTS[0]}/violation.md", "Run /audit-gadget now.\n"
    )

    run = run_validator(tmp_path)
    explicit_run = run_validator(tmp_path, [fixture])

    assert run.exit_code != 0
    assert len(run.lines) == 1
    assert str(scanned) in run.lines[0]
    assert str(fixture) not in "".join(run.lines)
    assert explicit_run.lines == ()
    assert explicit_run.exit_code == 0


def test_harness_command_invocations_are_not_skill_references(
    tmp_path: Path,
) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    commands = write_file(
        tmp_path,
        "src/plugins/alpha/commands.md",
        "".join(f"Run /{command} now.\n" for command in sorted(HARNESS_COMMANDS)),
    )
    unlisted = write_file(
        tmp_path, "src/plugins/alpha/unlisted.md", "Run /audit-gadget now.\n"
    )

    commands_run = run_validator(tmp_path, [commands])
    unlisted_run = run_validator(tmp_path, [unlisted])

    assert commands_run.lines == ()
    assert commands_run.exit_code == 0
    assert unlisted_run.exit_code != 0
