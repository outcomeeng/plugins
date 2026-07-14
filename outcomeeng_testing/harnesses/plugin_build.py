"""Resource lifecycle and observations for whole-pipeline build evidence."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.build import build
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SOURCE_ROOT = REPO_ROOT / SOURCE_ROOT_NAME


def canonical_dist_files_trace_to_source_ancestors() -> bool:
    """Return whether every canonical build output traces to source."""
    with TemporaryDirectory() as temporary_directory:
        output_root = Path(temporary_directory)
        build(CANONICAL_SOURCE_ROOT, output_root / DIST_DIR_NAME)
        reader = DistTreeReader(output_root)
        return all(
            (CANONICAL_SOURCE_ROOT / PLUGINS_DIR_NAME / relative_path).is_file()
            for target in Target
            for relative_path in reader.list_all_files(target)
        )


def canonical_build_is_deterministic() -> bool:
    """Return whether independent canonical builds are byte-identical."""
    with (
        TemporaryDirectory() as first_directory,
        TemporaryDirectory() as second_directory,
    ):
        first_dist = Path(first_directory) / DIST_DIR_NAME
        second_dist = Path(second_directory) / DIST_DIR_NAME
        build(CANONICAL_SOURCE_ROOT, first_dist)
        build(CANONICAL_SOURCE_ROOT, second_dist)
        return _snapshot(first_dist) == _snapshot(second_dist)


def canonical_build_is_idempotent() -> bool:
    """Return whether a repeated canonical build leaves output unchanged."""
    with TemporaryDirectory() as temporary_directory:
        dist_root = Path(temporary_directory) / DIST_DIR_NAME
        build(CANONICAL_SOURCE_ROOT, dist_root)
        first_snapshot = _snapshot(dist_root)
        build(CANONICAL_SOURCE_ROOT, dist_root)
        return _snapshot(dist_root) == first_snapshot


def _snapshot(root: Path) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        sorted(
            (str(path.relative_to(root)), path.read_bytes())
            for path in root.rglob("*")
            if path.is_file()
        )
    )
