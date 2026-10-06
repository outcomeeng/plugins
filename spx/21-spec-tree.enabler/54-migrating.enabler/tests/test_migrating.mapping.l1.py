from __future__ import annotations

from outcomeeng_testing.harnesses.link_conversion import (
    EXPECTED_REPORT_FILE,
    EXPECTED_REWRITTEN_FILE,
    EXPECTED_TREE,
    INPUT_TREE,
    UnconvertibleCitation,
    converted_copy,
    tree_files,
)


def expected_report() -> tuple[UnconvertibleCitation, ...]:
    rows = EXPECTED_REPORT_FILE.read_text(encoding="utf-8").splitlines()
    return tuple(
        UnconvertibleCitation(file, int(line), form, target)
        for file, line, form, target in (row.split("\t") for row in rows)
    )


def test_every_fixture_file_maps_to_its_expected_counterpart() -> None:
    with converted_copy(INPUT_TREE) as converted:
        converted_files = tree_files(converted.root)
    expected_files = tree_files(EXPECTED_TREE)

    assert converted_files.keys() == expected_files.keys()
    for path, expected_content in expected_files.items():
        assert converted_files[path] == expected_content, path


def test_the_conversion_lists_each_file_it_changes_and_no_other() -> None:
    expected = tuple(EXPECTED_REWRITTEN_FILE.read_text(encoding="utf-8").splitlines())

    with converted_copy(INPUT_TREE) as converted:
        assert converted.observation.rewritten == expected


def test_each_citation_the_conversion_cannot_convert_maps_to_a_report_line() -> None:
    with converted_copy(INPUT_TREE) as converted:
        assert converted.observation.unconvertible == expected_report()


def test_a_converted_fixture_file_maps_to_itself() -> None:
    with converted_copy(EXPECTED_TREE) as converted:
        converted_files = tree_files(converted.root)
        observation = converted.observation

    assert converted_files == tree_files(EXPECTED_TREE)
    assert observation.rewritten == ()
    assert observation.unconvertible == expected_report()
