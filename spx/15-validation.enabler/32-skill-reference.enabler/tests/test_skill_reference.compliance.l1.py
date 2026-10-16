"""Level 1 compliance evidence for skill-reference validation.

Each test exercises a rule of [skill-reference.md](../skill-reference.md)
against real violating files and conforming files that show no false positive.
"""

from __future__ import annotations

from pathlib import Path

from outcomeeng.validation.skill_reference import (
    CHANGELOG_FILENAME,
    EXEMPTED_REFERENCES,
    HARNESS_COMMANDS,
    INERT_FIXTURE_ROOT,
    SCAN_ROOTS,
)
from outcomeeng_testing.harnesses.skill_reference import (
    build_marketplace,
    run_validator,
    scan_references,
    scan_text_references,
    unshipped_references_fixture,
    write_file,
    write_outside_scan_roots,
    write_plugin_file,
)


def test_unshipped_reference_fails_in_every_recognized_form(tmp_path: Path) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    qualified = write_plugin_file(tmp_path, "alpha", "Run alpha:audit-gadget.\n")
    slash = write_plugin_file(tmp_path, "alpha", "Run /audit-gadget now.\n")
    placeholder = write_plugin_file(tmp_path, "alpha", "Run /review-{type} now.\n")

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
    payload = unshipped_references_fixture()
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
    content = write_plugin_file(
        tmp_path,
        "alpha",
        "See docs/audit-gadget/notes.md for details.\n",
    )

    run = run_validator(tmp_path, [content])

    assert run.lines == ()
    assert run.exit_code == 0


def test_alternation_expands_each_member_and_placeholders_need_a_matching_name(
    tmp_path: Path,
) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-code", "audit-tests"]})
    alternation = write_plugin_file(
        tmp_path,
        "alpha",
        "Run /audit-{code|tests|architecture}.\n",
    )
    complete = write_plugin_file(tmp_path, "alpha", "Run /audit-{code|tests}.\n")
    matching = write_plugin_file(tmp_path, "alpha", "Run /audit-{type}.\n")
    unmatched = write_plugin_file(tmp_path, "alpha", "Run /review-{type}.\n")
    empty_stand_in = write_plugin_file(tmp_path, "alpha", "Run /audit-code{type}.\n")

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
        [write_plugin_file(uncataloged, "alpha", content_text)],
    )
    cataloged_run = run_validator(
        cataloged, [write_plugin_file(cataloged, "alpha", content_text)]
    )
    renamed_run = run_validator(
        renamed, [write_plugin_file(renamed, "alpha", content_text)]
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
        write_file(tmp_path, root, "Run /audit-gadget now.\n") for root in SCAN_ROOTS
    ]
    write_plugin_file(
        tmp_path,
        "alpha",
        "Renamed /audit-gadget to /audit-widget.\n",
        CHANGELOG_FILENAME,
    )
    write_outside_scan_roots(tmp_path, "Run /audit-gadget now.\n")

    run = run_validator(tmp_path)

    assert run.exit_code != 0
    assert len(run.lines) == len(violating)
    for path in violating:
        assert sum(str(path) in line for line in run.lines) == 1


def test_inert_fixtures_are_excluded_from_the_scan(tmp_path: Path) -> None:
    build_marketplace(tmp_path, {"alpha": ["audit-widget"]})
    fixture = write_file(tmp_path, INERT_FIXTURE_ROOT, "Run /audit-gadget now.\n")
    scanned = write_file(tmp_path, SCAN_ROOTS[0], "Run /audit-gadget now.\n")

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
    commands = write_plugin_file(
        tmp_path,
        "alpha",
        "".join(f"Run /{command} now.\n" for command in sorted(HARNESS_COMMANDS)),
    )
    unlisted = write_plugin_file(tmp_path, "alpha", "Run /audit-gadget now.\n")

    commands_run = run_validator(tmp_path, [commands])
    unlisted_run = run_validator(tmp_path, [unlisted])

    assert commands_run.lines == ()
    assert commands_run.exit_code == 0
    assert unlisted_run.exit_code != 0
