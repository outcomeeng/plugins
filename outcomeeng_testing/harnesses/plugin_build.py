"""Resource lifecycle and observations for whole-pipeline build evidence."""

from __future__ import annotations

import subprocess
from difflib import unified_diff
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Final

from hypothesis import given, settings

from outcomeeng.distribution.build import (
    IMPLEMENTED,
    SHARED_DIR_NAME,
    SHARED_FRAGMENT_FILENAME,
    SKILL_FILENAME,
    IncludeDirective,
    build,
    parse_directives,
)
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    PLUGINS_DIR_NAME,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng_testing.generators.plugin_build import (
    PluginBuildSource,
    plugin_build_sources,
)
from outcomeeng_testing.harnesses.src_tree import src_tree

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SOURCE_ROOT = REPO_ROOT / SOURCE_ROOT_NAME
COMMITTED_DIST_ROOT = REPO_ROOT / DIST_DIR_NAME
PLUGIN_BUILD_PROPERTY_EXAMPLES: Final = 8
PLUGIN_BUILD_PROPERTY_REPLAY: Final = (
    "just test spx/18-plugin-build.enabler/tests/test_plugin_build.property.l1.py"
)


def canonical_dist_files_trace_to_source_ancestors() -> bool:
    """Return whether committed output equals the canonical source build."""
    _require_build_implementation()
    with TemporaryDirectory() as temporary_directory:
        generated_dist_root = Path(temporary_directory) / DIST_DIR_NAME
        build(CANONICAL_SOURCE_ROOT, generated_dist_root)
        _require_same_snapshot(
            actual=_snapshot(generated_dist_root),
            expected=_committed_dist_snapshot(),
        )
        return all(
            _source_ancestor_for_dist_path(relative_path) is not None
            for relative_path, _content in _committed_dist_snapshot()
        )


def canonical_build_is_deterministic() -> bool:
    """Run the generated determinism property and return its result."""
    _require_build_implementation()
    _run_replayable_property(_generated_build_is_deterministic)
    return True


def canonical_build_is_idempotent() -> bool:
    """Run the generated idempotence property and return its result."""
    _require_build_implementation()
    _run_replayable_property(_generated_build_is_idempotent)
    return True


@settings(
    max_examples=PLUGIN_BUILD_PROPERTY_EXAMPLES,
    deadline=None,
    derandomize=True,
    database=None,
)
@given(source=plugin_build_sources())
def _generated_build_is_deterministic(source: PluginBuildSource) -> None:
    with src_tree() as first_builder, src_tree() as second_builder:
        first_builder.add_plugin(
            source.plugin,
            skills={source.skill: source.body},
        )
        second_builder.add_plugin(
            source.plugin,
            skills={source.skill: source.body},
        )
        first_dist = first_builder.root / DIST_DIR_NAME
        second_dist = second_builder.root / DIST_DIR_NAME
        build(first_builder.src_root, first_dist)
        build(second_builder.src_root, second_dist)
        assert _snapshot(first_dist) == _snapshot(second_dist)


@settings(
    max_examples=PLUGIN_BUILD_PROPERTY_EXAMPLES,
    deadline=None,
    derandomize=True,
    database=None,
)
@given(source=plugin_build_sources())
def _generated_build_is_idempotent(source: PluginBuildSource) -> None:
    with src_tree() as builder:
        builder.add_plugin(
            source.plugin,
            skills={source.skill: source.body},
        )
        dist_root = builder.root / DIST_DIR_NAME
        build(builder.src_root, dist_root)
        first_snapshot = _snapshot(dist_root)
        build(builder.src_root, dist_root)
        assert _snapshot(dist_root) == first_snapshot


def _snapshot(root: Path) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        sorted(
            (str(path.relative_to(root)), path.read_bytes())
            for path in root.rglob("*")
            if path.is_file()
        )
    )


def _committed_dist_snapshot() -> tuple[tuple[str, bytes], ...]:
    result = subprocess.run(
        ["git", "ls-files", "--", DIST_DIR_NAME],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        (
            str(Path(path).relative_to(DIST_DIR_NAME)),
            (REPO_ROOT / path).read_bytes(),
        )
        for path in result.stdout.splitlines()
    )


def _source_ancestor_for_dist_path(relative_path: str) -> Path | None:
    path = Path(relative_path)
    if not path.parts or path.parts[0] not in {target.value for target in Target}:
        return None

    plugin_relative = Path(*path.parts[1:])
    direct_source = CANONICAL_SOURCE_ROOT / PLUGINS_DIR_NAME / plugin_relative
    if direct_source.is_file():
        return direct_source

    parts = plugin_relative.parts
    if len(parts) < 4 or parts[1] != SKILLS_SUBDIR_NAME:
        return None
    source_skill = (
        CANONICAL_SOURCE_ROOT
        / PLUGINS_DIR_NAME
        / parts[0]
        / SKILLS_SUBDIR_NAME
        / parts[2]
        / SKILL_FILENAME
    )
    if not source_skill.is_file():
        return None

    fanned_relative = Path(*parts[3:])
    shared_root = CANONICAL_SOURCE_ROOT / SHARED_DIR_NAME
    for directive in parse_directives(source_skill.read_text(encoding="utf-8")):
        if not isinstance(directive, IncludeDirective):
            continue
        topic_root = (shared_root / directive.path).parent
        candidate = topic_root / fanned_relative
        if candidate.is_file() and candidate.name != SHARED_FRAGMENT_FILENAME:
            return candidate
    return None


def _run_replayable_property(property_run: Callable[[], None]) -> None:
    try:
        property_run()
    except AssertionError as error:
        raise AssertionError(
            "deterministic property failure; replay with "
            f"`{PLUGIN_BUILD_PROPERTY_REPLAY}`"
        ) from error


def _require_same_snapshot(
    *,
    actual: tuple[tuple[str, bytes], ...],
    expected: tuple[tuple[str, bytes], ...],
) -> None:
    if actual == expected:
        return

    actual_files = dict(actual)
    expected_files = dict(expected)
    actual_paths = set(actual_files)
    expected_paths = set(expected_files)
    missing = sorted(expected_paths - actual_paths)
    unexpected = sorted(actual_paths - expected_paths)
    changed = sorted(
        path
        for path in actual_paths & expected_paths
        if actual_files[path] != expected_files[path]
    )
    first_changed_diff = ""
    if changed:
        first_changed_path = changed[0]
        first_changed_diff = "".join(
            unified_diff(
                expected_files[first_changed_path]
                .decode(errors="replace")
                .splitlines(keepends=True),
                actual_files[first_changed_path]
                .decode(errors="replace")
                .splitlines(keepends=True),
                fromfile=f"committed/{first_changed_path}",
                tofile=f"generated/{first_changed_path}",
            )
        )
    raise AssertionError(
        "distribution snapshot mismatch: "
        f"{missing=}, {unexpected=}, {changed=}\n{first_changed_diff}"
    )


def _require_build_implementation() -> None:
    if not IMPLEMENTED:
        raise AssertionError("the distribution build implementation is unavailable")
