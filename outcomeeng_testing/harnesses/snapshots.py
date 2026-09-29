"""Filesystem observations for evidence about generated trees."""

from __future__ import annotations

from pathlib import Path

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
