"""Source-owned Spec Tree directory structure rules."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

SPEC_TREE_ROOT_DIRECTORY = "spx"
SPEC_FILE_SUFFIX = ".md"
NODE_KIND_ENABLER = "enabler"
NODE_KIND_OUTCOME = "outcome"
MIN_NODE_INDEX = 10
MAX_NODE_INDEX = 99

_SLUG_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
_NODE_DIRECTORY_PATTERN = re.compile(
    rf"^(?P<index>\d+)-(?P<slug>{_SLUG_PATTERN})\.(?P<kind>{NODE_KIND_ENABLER}|{NODE_KIND_OUTCOME})$"
)


@dataclass(frozen=True)
class NodeDirectoryName:
    index: int
    slug: str
    kind: str


def parse_node_directory_name(name: str) -> NodeDirectoryName | None:
    match = _NODE_DIRECTORY_PATTERN.fullmatch(name)
    if match is None:
        return None
    return NodeDirectoryName(
        index=int(match.group("index")),
        slug=match.group("slug"),
        kind=match.group("kind"),
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
    for path in spx_root.rglob("*"):
        if path.is_dir() and parse_node_directory_name(path.name) is not None:
            yield path


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
