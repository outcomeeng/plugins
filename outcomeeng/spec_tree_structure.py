"""Source-owned Spec Tree directory structure rules."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

SPEC_TREE_ROOT_DIRECTORY = "spx"
SPEC_FILE_SUFFIX = ".md"
NODE_DIRECTORY_INDEX_SEPARATOR = "-"
NODE_DIRECTORY_KIND_SEPARATOR = "."
MIN_NODE_INDEX = 10
MAX_NODE_INDEX = 99


class NodeKind(StrEnum):
    ENABLER = "enabler"
    OUTCOME = "outcome"


NODE_KIND_ENABLER = NodeKind.ENABLER
NODE_KIND_OUTCOME = NodeKind.OUTCOME

_SLUG_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
_NODE_DIRECTORY_PATTERN = re.compile(
    rf"^(?P<index>[1-9][0-9]){re.escape(NODE_DIRECTORY_INDEX_SEPARATOR)}"
    rf"(?P<slug>{_SLUG_PATTERN}){re.escape(NODE_DIRECTORY_KIND_SEPARATOR)}"
    rf"(?P<kind>{NODE_KIND_ENABLER.value}|{NODE_KIND_OUTCOME.value})$"
)


@dataclass(frozen=True)
class NodeDirectoryName:
    index: int
    slug: str
    kind: NodeKind


def format_node_directory_name(index: int, slug: str, kind: NodeKind) -> str:
    if not is_valid_node_index(index):
        msg = (
            f"Spec Tree node index must be between {MIN_NODE_INDEX} "
            f"and {MAX_NODE_INDEX}: {index}"
        )
        raise ValueError(msg)

    return (
        f"{index}{NODE_DIRECTORY_INDEX_SEPARATOR}"
        f"{slug}{NODE_DIRECTORY_KIND_SEPARATOR}{kind.value}"
    )


def parse_node_directory_name(name: str) -> NodeDirectoryName | None:
    match = _NODE_DIRECTORY_PATTERN.fullmatch(name)
    if match is None:
        return None
    return NodeDirectoryName(
        index=int(match.group("index")),
        slug=match.group("slug"),
        kind=NodeKind(match.group("kind")),
    )


def node_directory_name(node_directory: Path) -> NodeDirectoryName:
    parsed = parse_node_directory_name(node_directory.name)
    if parsed is None:
        msg = f"{node_directory.name!r} is not a Spec Tree node directory"
        raise ValueError(msg)
    return parsed


def is_valid_node_index(index: int) -> bool:
    return MIN_NODE_INDEX <= index <= MAX_NODE_INDEX


def iter_node_directories(spx_root: Path) -> Iterator[Path]:
    """Yield node directories from a prepared Spec Tree root, resolving symlinks."""
    node_directories: dict[Path, Path] = {}
    for path in spx_root.rglob("*"):
        if path.is_dir() and parse_node_directory_name(path.name) is not None:
            resolved_path = path.resolve()
            existing_path = node_directories.get(resolved_path)
            if existing_path is None or (
                existing_path.is_symlink() and not path.is_symlink()
            ):
                node_directories[resolved_path] = path
    yield from sorted(node_directories.values())


def iter_node_directories_from_tracked_paths(
    product_root: Path,
    tracked_paths: list[Path],
) -> Iterator[Path]:
    node_directories: set[Path] = set()
    for tracked_path in tracked_paths:
        for parent in tracked_path.parents:
            if parent == product_root:
                break
            if parse_node_directory_name(parent.name) is not None:
                node_directories.add(parent)
    yield from sorted(node_directories)


def node_spec_file(node_directory: Path) -> Path:
    parsed = node_directory_name(node_directory)
    return node_directory / f"{parsed.slug}{SPEC_FILE_SUFFIX}"
