"""Canonical repository paths and byte snapshots for distribution evidence."""

from __future__ import annotations

from pathlib import Path

from outcomeeng.distribution.contracts import SOURCE_ROOT_NAME

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SOURCE_ROOT = REPOSITORY_ROOT / SOURCE_ROOT_NAME
type FileSnapshot = tuple[tuple[str, bytes], ...]


def snapshot_files(root: Path) -> FileSnapshot:
    """Return a stable relative-path and byte-content snapshot below ``root``."""
    return tuple(
        sorted(
            (str(path.relative_to(root)), path.read_bytes())
            for path in root.rglob("*")
            if path.is_file()
        )
    )
