from __future__ import annotations

from outcomeeng_testing.harnesses.link_conversion import (
    INPUT_TREE,
    OUTSIDE_SPEC_TREE_FIXTURE,
    UNTOUCHED_FILES_FILE,
    convert_product_root,
    converted_copy,
    copied_tree,
    load_link_conversion_module,
    tree_files,
)


def test_conversion_changes_only_markdown_files_beneath_the_spec_tree() -> None:
    conversion = load_link_conversion_module()
    input_files = tree_files(INPUT_TREE)
    outside_scope = [
        path
        for path in input_files
        if not (
            path.startswith(f"{conversion.SPEC_TREE_DIRECTORY}/")
            and path.endswith(conversion.MARKDOWN_SUFFIX)
        )
    ]

    with converted_copy(INPUT_TREE) as converted:
        converted_files = tree_files(converted.root)

    assert outside_scope
    for path in outside_scope:
        assert converted_files[path] == input_files[path], path


def test_forms_the_conversion_must_not_change_stay_as_written() -> None:
    untouched = UNTOUCHED_FILES_FILE.read_text(encoding="utf-8").splitlines()
    input_files = tree_files(INPUT_TREE)

    with converted_copy(INPUT_TREE) as converted:
        converted_files = tree_files(converted.root)
        observation = converted.observation
    reported_files = {citation.file for citation in observation.unconvertible}

    assert untouched
    for path in untouched:
        assert converted_files[path] == input_files[path], path
        assert path not in observation.rewritten, path
        assert path not in reported_files, path


def test_conversion_refuses_an_explicit_path_outside_the_spec_tree() -> None:
    conversion = load_link_conversion_module()

    with copied_tree(INPUT_TREE) as root:
        before = tree_files(root)
        observation = convert_product_root(root, OUTSIDE_SPEC_TREE_FIXTURE.name)
        after = tree_files(root)

    assert observation.exit_code == conversion.EXIT_ERROR
    assert after == before
