from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.spec_tree_structure import (
    MAX_NODE_INDEX,
    MIN_NODE_INDEX,
    NODE_DIRECTORY_INDEX_SEPARATOR,
    NODE_DIRECTORY_KIND_SEPARATOR,
    NODE_KIND_ENABLER,
    SPEC_FILE_SUFFIX,
    SPEC_TREE_ROOT_DIRECTORY,
    NodeDirectoryName,
    format_node_directory_name,
    is_valid_node_index,
    iter_node_directories,
    node_spec_file,
    parse_node_directory_name,
)


def test_valid_node_directory_name_maps_to_parsed_parts() -> None:
    node_name = format_node_directory_name(
        MIN_NODE_INDEX,
        SPEC_TREE_ROOT_DIRECTORY,
        NODE_KIND_ENABLER,
    )

    assert parse_node_directory_name(node_name) == NodeDirectoryName(
        index=MIN_NODE_INDEX,
        slug=SPEC_TREE_ROOT_DIRECTORY,
        kind=NODE_KIND_ENABLER,
    )


def test_invalid_node_directory_name_shapes_map_to_absent_parse() -> None:
    valid_name = format_node_directory_name(
        MIN_NODE_INDEX,
        SPEC_TREE_ROOT_DIRECTORY,
        NODE_KIND_ENABLER,
    )
    invalid_names = [
        valid_name.upper(),
        format_node_directory_name(
            MIN_NODE_INDEX,
            f"{SPEC_TREE_ROOT_DIRECTORY}{NODE_DIRECTORY_INDEX_SEPARATOR}",
            NODE_KIND_ENABLER,
        ),
        valid_name.replace(NODE_DIRECTORY_INDEX_SEPARATOR, "", 1),
        valid_name.removesuffix(NODE_KIND_ENABLER.value)
        + SPEC_FILE_SUFFIX.removeprefix(NODE_DIRECTORY_KIND_SEPARATOR),
        f"0{valid_name}",
    ]

    assert all(parse_node_directory_name(name) is None for name in invalid_names)


def test_invalid_node_directory_index_maps_to_absent_parse() -> None:
    invalid_index = str(MIN_NODE_INDEX - 1).zfill(len(str(MIN_NODE_INDEX)))
    invalid_name = (
        f"{invalid_index}{NODE_DIRECTORY_INDEX_SEPARATOR}"
        f"{SPEC_TREE_ROOT_DIRECTORY}{NODE_DIRECTORY_KIND_SEPARATOR}"
        f"{NODE_KIND_ENABLER.value}"
    )

    assert parse_node_directory_name(invalid_name) is None


def test_format_node_directory_name_rejects_invalid_index() -> None:
    with pytest.raises(ValueError):
        format_node_directory_name(
            MIN_NODE_INDEX - 1,
            SPEC_TREE_ROOT_DIRECTORY,
            NODE_KIND_ENABLER,
        )


def test_node_index_boundaries_map_to_validity() -> None:
    assert not is_valid_node_index(MIN_NODE_INDEX - 1)
    assert is_valid_node_index(MIN_NODE_INDEX)
    assert is_valid_node_index(MAX_NODE_INDEX)
    assert not is_valid_node_index(MAX_NODE_INDEX + 1)


def test_node_directory_maps_to_slug_spec_file(tmp_path: Path) -> None:
    node_directory = tmp_path / format_node_directory_name(
        MIN_NODE_INDEX,
        SPEC_TREE_ROOT_DIRECTORY,
        NODE_KIND_ENABLER,
    )

    assert node_spec_file(node_directory) == (
        node_directory / f"{SPEC_TREE_ROOT_DIRECTORY}{SPEC_FILE_SUFFIX}"
    )


def test_prepared_tree_iteration_deduplicates_symlinked_node_directories(
    tmp_path: Path,
) -> None:
    node_directory = tmp_path / format_node_directory_name(
        MIN_NODE_INDEX,
        SPEC_TREE_ROOT_DIRECTORY,
        NODE_KIND_ENABLER,
    )
    node_directory.mkdir()
    symlink_directory = tmp_path / format_node_directory_name(
        MAX_NODE_INDEX,
        SPEC_TREE_ROOT_DIRECTORY,
        NODE_KIND_ENABLER,
    )
    symlink_directory.symlink_to(node_directory, target_is_directory=True)

    assert list(iter_node_directories(tmp_path)) == [node_directory]
