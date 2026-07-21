"""Resource lifecycle and observations for whole-pipeline build evidence."""

from __future__ import annotations

import shutil
import subprocess
from difflib import unified_diff
from os import utime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng.distribution.build import (
    FORMATTER_COMMAND_NAME,
    BuildError,
    IMPLEMENTED,
    SHARED_DIR_NAME,
    SHARED_FRAGMENT_FILENAME,
    IncludeDirective,
    FormatterProbe,
    build,
    format_directive,
    formatter_version_command,
    parse_directives,
)
from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    PLUGINS_DIR_NAME,
    PLUGIN_SUBDIRS,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    Target,
)
from outcomeeng_testing.generators.plugin_build import (
    PluginBuildSource,
    nonmatching_formatter_versions,
    plugin_build_sources,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property
from outcomeeng.distribution.build import TEMPLATES_DIR_NAME
from outcomeeng_testing.harnesses.distribution import (
    CANONICAL_SOURCE_ROOT,
    REPOSITORY_ROOT,
    snapshot_files,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder, src_tree

PLUGIN_BUILD_PROPERTY_EXAMPLES: Final = 8
PLUGIN_BUILD_PROPERTY_SEED: Final = 20260714
PLUGIN_BUILD_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/18-plugin-build.enabler/tests/test_plugin_build.property.l1.py"
)
FIRST_SOURCE_MTIME_NS: Final = 1_000_000_000
SECOND_SOURCE_MTIME_NS: Final = 2_000_000_000
FORMATTER_TEST_PATH: Final = f"/usr/local/bin/{FORMATTER_COMMAND_NAME}"


def canonical_dist_files_trace_to_source_ancestors() -> bool:
    """Return whether committed output equals the canonical source build."""
    _require_build_implementation()
    with TemporaryDirectory() as temporary_directory:
        generated_dist_root = Path(temporary_directory) / DIST_DIR_NAME
        build(CANONICAL_SOURCE_ROOT, generated_dist_root)
        _require_same_snapshot(
            actual=snapshot_files(generated_dist_root),
            expected=_committed_dist_snapshot(),
        )
        return all(
            _source_ancestor_for_dist_path(relative_path) is not None
            for relative_path, _content in _committed_dist_snapshot()
        )


def orphaned_dist_artifact_is_rejected() -> bool:
    """Return whether snapshot validation rejects an unbuilt dist artifact."""
    _require_build_implementation()
    with TemporaryDirectory() as temporary_directory:
        generated_dist_root = Path(temporary_directory) / DIST_DIR_NAME
        build(CANONICAL_SOURCE_ROOT, generated_dist_root)
        generated_snapshot = snapshot_files(generated_dist_root)
        orphaned_snapshot = (
            *generated_snapshot,
            (str(Path(DIST_DIR_NAME, SKILL_FILENAME)), b""),
        )
        try:
            _require_same_snapshot(
                actual=generated_snapshot,
                expected=orphaned_snapshot,
            )
        except AssertionError:
            return True
        return False


def canonical_build_is_deterministic() -> bool:
    """Run the generated determinism property and return its result."""
    _require_build_implementation()
    run_replayable_property(
        _generated_build_is_deterministic,
        seed_value=PLUGIN_BUILD_PROPERTY_SEED,
        replay_path=PLUGIN_BUILD_PROPERTY_REPLAY_PATH,
    )
    return True


def canonical_build_is_idempotent() -> bool:
    """Run the generated idempotence property and return its result."""
    _require_build_implementation()
    run_replayable_property(
        _generated_build_is_idempotent,
        seed_value=PLUGIN_BUILD_PROPERTY_SEED,
        replay_path=PLUGIN_BUILD_PROPERTY_REPLAY_PATH,
    )
    return True


def canonical_build_rejects_formatter_version_drift() -> bool:
    """Run the generated formatter-version drift property and return its result."""
    _require_build_implementation()
    run_replayable_property(
        _generated_build_rejects_formatter_version_drift,
        seed_value=PLUGIN_BUILD_PROPERTY_SEED,
        replay_path=PLUGIN_BUILD_PROPERTY_REPLAY_PATH,
    )
    return True


@seed(PLUGIN_BUILD_PROPERTY_SEED)
@settings(
    max_examples=PLUGIN_BUILD_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(source=plugin_build_sources())
def _generated_build_is_deterministic(source: PluginBuildSource) -> None:
    with src_tree() as first_builder, src_tree() as second_builder:
        _materialize_source(first_builder, source)
        _materialize_source(second_builder, source)
        _set_source_mtime(first_builder.src_root, FIRST_SOURCE_MTIME_NS)
        _set_source_mtime(second_builder.src_root, SECOND_SOURCE_MTIME_NS)
        first_dist = first_builder.root / DIST_DIR_NAME
        second_dist = second_builder.root / DIST_DIR_NAME
        build(
            first_builder.src_root,
            first_dist,
            formatter_probe=_formatter_probe(first_builder.root),
        )
        build(
            second_builder.src_root,
            second_dist,
            formatter_probe=_formatter_probe(second_builder.root),
        )
        assert snapshot_files(first_dist) == snapshot_files(second_dist)


@seed(PLUGIN_BUILD_PROPERTY_SEED)
@settings(
    max_examples=PLUGIN_BUILD_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(source=plugin_build_sources())
def _generated_build_is_idempotent(source: PluginBuildSource) -> None:
    with src_tree() as builder:
        _materialize_source(builder, source)
        dist_root = builder.root / DIST_DIR_NAME
        build(builder.src_root, dist_root)
        first_snapshot = snapshot_files(dist_root)
        build(builder.src_root, dist_root)
        assert snapshot_files(dist_root) == first_snapshot


@seed(PLUGIN_BUILD_PROPERTY_SEED)
@settings(
    max_examples=PLUGIN_BUILD_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(
    source=plugin_build_sources(),
    version_output=nonmatching_formatter_versions(),
)
def _generated_build_rejects_formatter_version_drift(
    source: PluginBuildSource,
    version_output: str,
) -> None:
    with src_tree() as builder:
        _materialize_source(builder, source)
        dist_root = builder.root / DIST_DIR_NAME
        for target in Target:
            existing_path = dist_root / target.value / SKILL_FILENAME
            existing_path.parent.mkdir(parents=True)
            existing_path.write_bytes(source.plugins[0].opaque_body)
        existing_snapshot = snapshot_files(dist_root)
        runner_calls: list[tuple[tuple[str, ...], Path]] = []

        def formatter_probe(command_name: str) -> str | None:
            if command_name != FORMATTER_COMMAND_NAME:
                raise AssertionError(command_name)
            return FORMATTER_TEST_PATH

        def version_runner(
            command: tuple[str, ...], cwd: Path
        ) -> subprocess.CompletedProcess[str]:
            runner_calls.append((command, cwd))
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=version_output,
                stderr="",
            )

        try:
            build(
                builder.src_root,
                dist_root,
                formatter_probe=formatter_probe,
                formatter_runner=version_runner,
            )
        except BuildError:
            pass
        else:
            raise AssertionError("formatter version drift was accepted")

        assert runner_calls == [
            (formatter_version_command(FORMATTER_TEST_PATH), builder.src_root)
        ]
        assert snapshot_files(dist_root) == existing_snapshot


def _committed_dist_snapshot() -> tuple[tuple[str, bytes], ...]:
    result = subprocess.run(
        ["git", "ls-files", "--", DIST_DIR_NAME],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        (
            str(Path(path).relative_to(DIST_DIR_NAME)),
            (REPOSITORY_ROOT / path).read_bytes(),
        )
        for path in result.stdout.splitlines()
    )


def _formatter_probe(host_root: Path) -> FormatterProbe:
    formatter = shutil.which(FORMATTER_COMMAND_NAME)
    if formatter is None:
        raise AssertionError(f"{FORMATTER_COMMAND_NAME} is unavailable")
    host_bin = host_root / "bin"
    host_bin.mkdir()
    formatter_alias = host_bin / FORMATTER_COMMAND_NAME
    formatter_alias.symlink_to(formatter)

    def probe(command_name: str) -> str | None:
        if command_name != FORMATTER_COMMAND_NAME:
            raise AssertionError(command_name)
        return str(formatter_alias)

    return probe


def _template_source_for(parts: tuple[str, ...]) -> Path | None:
    """Return the per-plugin template source behind a generated skill path.

    A template renders into the skill directory ``<plugin>-<template>``, and its
    converted agent artifacts and placement manifest live beneath that directory,
    so every one of them traces back to that template's own source files.
    """
    plugin, skill_dir = parts[0], parts[2]
    prefix = f"{plugin}-"
    if not skill_dir.startswith(prefix):
        return None
    template_root = (
        CANONICAL_SOURCE_ROOT / TEMPLATES_DIR_NAME / skill_dir[len(prefix) :]
    )
    if not template_root.is_dir():
        return None
    candidate = template_root / Path(*parts[3:])
    if candidate.is_file():
        return candidate
    # A converted agent or placement manifest is derived from the plugin's own
    # agent sources plus the template that carries them, so the template's
    # SKILL.md is the ancestor that put it in the tree.
    return template_root / SKILL_FILENAME


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

    template_source = _template_source_for(parts)
    if template_source is not None:
        return template_source
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


def _materialize_source(builder: SrcTreeBuilder, source: PluginBuildSource) -> None:
    for plugin_source in source.plugins:
        case = plugin_source.scenario
        reference_name = f"{case.outer_topic}{MARKDOWN_FILE_SUFFIX}"
        builder.add_shared_topic(
            case.scope,
            case.inner_topic,
            plugin_source.body,
            references={reference_name: plugin_source.body},
        )
        directive = format_directive(
            IncludeDirective(
                f"{case.scope}/{case.inner_topic}/{SHARED_FRAGMENT_FILENAME}"
            )
        )
        artifacts = {
            Path(subdir, case.cycle_topic): plugin_source.opaque_body
            for subdir in PLUGIN_SUBDIRS
        }
        builder.add_plugin(
            case.plugin,
            skills={case.skill: f"{directive}\n{plugin_source.body}"},
            agents={case.cycle_topic: plugin_source.body},
            artifacts=artifacts,
        )


def _set_source_mtime(root: Path, mtime_ns: int) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            utime(path, ns=(mtime_ns, mtime_ns))


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
