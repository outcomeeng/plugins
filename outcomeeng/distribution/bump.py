"""Manifest version-bumping orchestration.

Bumps the manifest version of every plugin whose authored source tree,
generated runtime tree, or included shared fragment has changes since a
base reference (default `origin/main`). Each changed plugin's version is incremented exactly once
across every manifest it owns (`.claude-plugin/plugin.json` always;
`.codex-plugin/plugin.json` when present). The increment segment is
auto-detected per plugin unless the caller explicitly selects `patch`,
`minor`, or `major`.

The module's contract:

- `SOURCE_PLUGINS_DIR`, `DIST_CLAUDE_PLUGINS_DIR`,
  `DIST_CODEX_PLUGINS_DIR`, `CLAUDE_MANIFEST`, and `CODEX_MANIFEST` name
  the path prefixes and manifest filenames the orchestration recognizes.
- `REQUIRED_TOOLS` names the external binaries `main()` shells out to.
- `Version`, `Segment`, and `ManifestRecord` are the domain dataclasses.
- `ChangeProbe`, `ContentProbe`, `IncludeIndexProbe`, `ManifestReader`,
  `ManifestWriter`, `ToolProbe` Protocols describe the injected
  side-effecting boundaries.
- `bump()` runs the orchestration; tests substitute controlled Protocol
  implementations.
- `changed_plugins_from_diff()` is the pure path-prefix filter the
  production `_real_change_probe` adapter delegates to, and
  `plugins_from_shared_change()` resolves a change under
  `SHARED_SOURCE_DIR` through the include index.
- `main()` wires real `git diff` / `git show` / `Path` adapters.
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    BUILD_BLOCK_DELIMITER_END,
    BUILD_BLOCK_DELIMITER_START,
    CLAUDE_PLUGIN_SUBDIR_NAME,
    CODEX_PLUGIN_SUBDIR_NAME,
    DIST_CODEX_PLUGINS_DIR as DIST_CODEX_PLUGINS_PATH,
    MARKDOWN_FILE_SUFFIX,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
)

REQUIRED_TOOLS: tuple[str, ...] = ("git",)
SOURCE_PLUGINS_DIR: str = "src/plugins"
DIST_CLAUDE_PLUGINS_DIR: str = "dist/claude"
DIST_CODEX_PLUGINS_DIR: str = DIST_CODEX_PLUGINS_PATH.as_posix()
CLAUDE_MANIFEST: str = f"{CLAUDE_PLUGIN_SUBDIR_NAME}/plugin.json"
CODEX_MANIFEST: str = f"{CODEX_PLUGIN_SUBDIR_NAME}/plugin.json"

SHARED_SOURCE_DIR: str = "src/_shared"

_PLUGIN_CHANGE_ROOTS: tuple[str, ...] = (
    SOURCE_PLUGINS_DIR,
    DIST_CLAUDE_PLUGINS_DIR,
    DIST_CODEX_PLUGINS_DIR,
)
_IGNORED_SOURCE_DIRECTORIES: frozenset[str] = frozenset({"__pycache__"})
_IGNORED_SOURCE_SUFFIXES: tuple[str, ...] = (".pyc",)
# Accepts either quote style, matching the literal `format_directive` emits
# through `repr()`. The authoritative grammar lives in
# `outcomeeng.distribution.build`, which this module cannot import without
# taking that module's third-party dependency; extracting the grammar into
# the shared stdlib-only contracts module is recorded at this node.
_INCLUDE_DIRECTIVE = re.compile(
    re.escape(BUILD_BLOCK_DELIMITER_START)
    + r"\s*include\s+(?:'([^']+)'|\"([^\"]+)\")\s*"
    + re.escape(BUILD_BLOCK_DELIMITER_END)
)
_KNOWN_MANIFESTS: tuple[str, ...] = (CLAUDE_MANIFEST, CODEX_MANIFEST)
_DEFAULT_BASE_REF: str = "origin/main"


class Segment(StrEnum):
    """Semver segment to increment in a bump pass."""

    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


class Mode(StrEnum):
    """Bump invocation mode.

    `WRITE` mutates manifests; `DRY_RUN` reports without mutating;
    `CHECK` exits non-zero when any changed plugin still needs a bump.
    All three share the same read phase.
    """

    WRITE = "write"
    DRY_RUN = "dry-run"
    CHECK = "check"


class FileStatus(StrEnum):
    """Git file-status tokens emitted by the change-detection diff."""

    ADDED = "A"
    COPIED = "C"
    DELETED = "D"
    MODIFIED = "M"
    RENAMED = "R"


@dataclass(frozen=True)
class ChangedPath:
    """One repository-relative path changed since `base_ref` with its status.

    For copies and renames, `path` is the destination path in the working tree
    and `old_path` is the source path that exists at `base_ref`.
    """

    status: FileStatus
    path: str
    old_path: str | None = None


@dataclass(frozen=True, order=True)
class Version:
    """A `MAJOR.MINOR.PATCH` semver triple with segment-specific bumps."""

    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, text: str) -> Version:
        parts = text.strip().split(".")
        if len(parts) != 3:
            raise ValueError(f"invalid version: {text!r}")
        return cls(major=int(parts[0]), minor=int(parts[1]), patch=int(parts[2]))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def bump_patch(self) -> Version:
        return Version(major=self.major, minor=self.minor, patch=self.patch + 1)

    def bump_minor(self) -> Version:
        return Version(major=self.major, minor=self.minor + 1, patch=0)

    def bump_major(self) -> Version:
        return Version(major=self.major + 1, minor=0, patch=0)


_SEGMENT_DISPATCH: dict[Segment, Callable[[Version], Version]] = {
    Segment.PATCH: Version.bump_patch,
    Segment.MINOR: Version.bump_minor,
    Segment.MAJOR: Version.bump_major,
}


def bump_version(version: Version, segment: Segment) -> Version:
    """Return ``version`` incremented according to the selected segment."""
    return _SEGMENT_DISPATCH[segment](version)


@dataclass(frozen=True)
class ManifestRecord:
    """Working-tree state of one manifest a plugin owns."""

    path: str
    content: str


class ChangeProbe(Protocol):
    """Returns a mapping from plugin name to the file-status-tagged paths
    that changed under a recognized distribution-surface root since `base_ref`."""

    def __call__(self, base_ref: str) -> Mapping[str, tuple[ChangedPath, ...]]: ...


class ContentProbe(Protocol):
    """Returns the content of `path` at `base_ref`, or None when the path
    does not exist at that ref."""

    def __call__(self, base_ref: str, path: str) -> str | None: ...


class ManifestReader(Protocol):
    """Returns the working-tree manifest records the plugin owns."""

    def __call__(self, plugin: str) -> tuple[ManifestRecord, ...]: ...


class ManifestWriter(Protocol):
    """Writes `new_content` to `path` in the working tree."""

    def __call__(self, path: str, new_content: str) -> None: ...


class ToolProbe(Protocol):
    """Returns True when `name` resolves to an executable on PATH."""

    def __call__(self, name: str) -> bool: ...


class IncludeIndexProbe(Protocol):
    """Returns a mapping from a shared fragment's include target to the
    plugins whose authored sources name it in an include directive."""

    def __call__(self) -> Mapping[str, frozenset[str]]: ...


class ManifestVersionError(ValueError):
    """Raised when a manifest does not expose a parseable string version."""


def changed_plugins_from_diff(paths: Iterable[str]) -> frozenset[str]:
    """Filter diff paths to the set of plugin names changed."""
    plugins: set[str] = set()
    for path in paths:
        if plugin := _plugin_from_changed_path(path):
            plugins.add(plugin)
    return frozenset(plugins)


def _plugin_from_changed_path(path: str) -> str | None:
    parts = path.split("/")
    for root in _PLUGIN_CHANGE_ROOTS:
        root_parts = root.split("/")
        if (
            len(parts) > len(root_parts)
            and parts[: len(root_parts)] == root_parts
            and parts[len(root_parts)]
        ):
            return parts[len(root_parts)]
    return None


def auto_segment(changes: Iterable[ChangedPath]) -> Segment:
    """Resolve the warranted semver segment from a plugin's changed paths.

    An `A`/`C`/`D`/`R` change to a structural path inside the plugin yields
    `MINOR`; every other pattern yields `PATCH`. Auto-detection never
    selects `MAJOR`; major bumps require explicit human opt-in.

    Structural paths (relative to any recognized distribution-surface root):

    - `skills/{slug}/SKILL.md`
    - `agents/{slug}.md`
    - `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`
    """
    for change in changes:
        if change.status is FileStatus.MODIFIED:
            continue
        if _change_has_minor_triggering_path(change):
            return Segment.MINOR
    return Segment.PATCH


def _change_has_minor_triggering_path(change: ChangedPath) -> bool:
    """Whether one change reaches a declared surface from either of its ends.

    The source path counts only for a rename, matching `plugins_from_change`.
    Git populates `old_path` for a copy too, but a copy leaves its source
    byte-identical at `base_ref`, so that plugin lost nothing: reading it would
    classify MINOR from a surface no change touched, and copy detection reports
    a copy whenever a new file resembles an existing one.
    """
    if _is_minor_triggering_path(change.path):
        return True
    return (
        change.status is FileStatus.RENAMED
        and change.old_path is not None
        and _is_minor_triggering_path(change.old_path)
    )


def _is_minor_triggering_path(path: str) -> bool:
    parts = path.split("/")
    rest: list[str] | None = None
    for root in _PLUGIN_CHANGE_ROOTS:
        root_parts = root.split("/")
        if (
            len(parts) >= len(root_parts) + 3
            and parts[: len(root_parts)] == root_parts
            and parts[len(root_parts)]
        ):
            rest = parts[len(root_parts) + 1 :]
            break
    if rest is None:
        return False
    if len(rest) == 3 and rest[0] == SKILLS_SUBDIR_NAME and rest[2] == SKILL_FILENAME:
        return True
    if (
        len(rest) == 2
        and rest[0] == AGENTS_SUBDIR_NAME
        and rest[1].endswith(MARKDOWN_FILE_SUFFIX)
    ):
        return True
    if (
        len(rest) == 2
        and rest[0] in (CLAUDE_PLUGIN_SUBDIR_NAME, CODEX_PLUGIN_SUBDIR_NAME)
        and rest[1] == "plugin.json"
    ):
        return True
    return False


def bump(
    base_ref: str,
    segment: Segment | None = None,
    *,
    mode: Mode = Mode.WRITE,
    change_probe: ChangeProbe,
    content_probe: ContentProbe,
    manifest_reader: ManifestReader,
    manifest_writer: ManifestWriter,
    tool_probe: ToolProbe,
) -> int:
    """Run the bump orchestration. Returns the process exit code.

    When `segment` is `None`, the segment is auto-detected per plugin via
    `auto_segment(changes)` over the `ChangeProbe`'s reported changes.
    When `segment` is a concrete value, it overrides per-plugin detection
    and a stderr warning names any plugin whose detected segment differs.
    """
    for tool in REQUIRED_TOOLS:
        if not tool_probe(tool):
            print(f"Missing required tool: {tool}", file=sys.stderr)
            return 1

    changed = change_probe(base_ref)
    if not changed:
        return 0

    plans: list[tuple[str, ManifestRecord, Version]] = []
    plugin_targets: dict[str, tuple[Version, Segment]] = {}
    already_bumped_plugins: list[str] = []
    unbumped_plugins: list[str] = []
    out_of_lockstep_plugins: set[str] = set()
    for plugin in sorted(changed):
        records = manifest_reader(plugin)
        if not records:
            continue
        plugin_changes = changed[plugin]
        detected = auto_segment(plugin_changes)
        if segment is not None and segment is not detected:
            print(
                f"Plugin {plugin}: explicit --segment {segment} overrides "
                f"detected {detected}",
                file=sys.stderr,
            )
        resolved = segment if segment is not None else detected
        working_tree_versions: list[Version] = []
        base_ref_versions: list[Version] = []
        lagging_manifest = False
        for record in records:
            try:
                working_tree_version = _version_from_manifest_text(
                    record.path, record.content
                )
            except ManifestVersionError as error:
                print(str(error), file=sys.stderr)
                return 1
            working_tree_versions.append(working_tree_version)
            base_ref_content = _base_manifest_content_for_record(
                content_probe, base_ref, record.path, plugin_changes
            )
            if base_ref_content is not None:
                try:
                    base_ref_version = _version_from_manifest_text(
                        record.path, base_ref_content
                    )
                except ManifestVersionError as error:
                    print(str(error), file=sys.stderr)
                    return 1
                if working_tree_version <= base_ref_version:
                    lagging_manifest = True
                base_ref_versions.append(base_ref_version)
            else:
                base_ref_versions.append(working_tree_version)
            plans.append((plugin, record, working_tree_version))
        plugin_versions_agree = len(set(working_tree_versions)) == 1
        if not lagging_manifest and plugin_versions_agree:
            already_bumped_plugins.append(plugin)
        else:
            if not plugin_versions_agree:
                out_of_lockstep_plugins.add(plugin)
            segment_target = bump_version(max(base_ref_versions), resolved)
            plugin_target = max(segment_target, max(working_tree_versions))
            plugin_targets[plugin] = (plugin_target, resolved)
            unbumped_plugins.append(plugin)

    if mode is Mode.CHECK:
        if unbumped_plugins:
            for plugin in unbumped_plugins:
                reason = (
                    "its owned manifests are out of lockstep"
                    if plugin in out_of_lockstep_plugins
                    else f"its working-tree version is not ahead of its {base_ref} version"
                )
                print(
                    f"Plugin {plugin} needs a version bump because {reason}",
                    file=sys.stderr,
                )
            return 1
        return 0

    # WRITE / DRY_RUN: skip plugins already bumped on this branch — never
    # re-bump one (the spec NEVER clause) — while still bumping every other
    # changed-but-unbumped plugin in the same pass.
    for plugin in already_bumped_plugins:
        print(
            f"Plugin {plugin} already has a version bump on this branch; skipping",
            file=sys.stderr,
        )

    skip = set(already_bumped_plugins)
    for plugin, record, working_tree_version in plans:
        if plugin in skip:
            continue
        new_version, resolved = plugin_targets[plugin]
        if mode is Mode.DRY_RUN:
            print(
                f"{plugin}: {record.path} {working_tree_version} -> "
                f"{new_version} ({resolved})"
            )
            continue
        manifest_writer(record.path, _replace_version(record.content, str(new_version)))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Wires real `git` and filesystem adapters."""
    args = _build_parser().parse_args(argv)
    if args.dry_run:
        mode = Mode.DRY_RUN
    elif args.check:
        mode = Mode.CHECK
    else:
        mode = Mode.WRITE
    segment = Segment(args.segment) if args.segment is not None else None
    return bump(
        args.base_ref,
        segment,
        mode=mode,
        change_probe=functools.partial(
            _real_change_probe, include_index_probe=_real_include_index_probe
        ),
        content_probe=_real_content_probe,
        manifest_reader=_real_manifest_reader,
        manifest_writer=_real_manifest_writer,
        tool_probe=_real_tool_probe,
    )


def _version_from_manifest_text(path: str, content: str) -> Version:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as error:
        raise ManifestVersionError(
            f"Manifest {path} has invalid JSON: {error.msg}"
        ) from error
    if not isinstance(data, dict):
        raise ManifestVersionError(
            f"Manifest {path} must contain a JSON object with a string version"
        )
    version = data.get("version")
    if not isinstance(version, str):
        raise ManifestVersionError(f"Manifest {path} must contain a string version")
    try:
        return Version.parse(version)
    except ValueError as error:
        raise ManifestVersionError(
            f"Manifest {path} has invalid version {version!r}"
        ) from error


def _base_manifest_content_for_record(
    content_probe: ContentProbe,
    base_ref: str,
    path: str,
    changes: Iterable[ChangedPath],
) -> str | None:
    content = content_probe(base_ref, path)
    if content is not None:
        return content
    for change in changes:
        if change.path == path and change.old_path is not None:
            return content_probe(base_ref, change.old_path)
    return None


def _replace_version(content: str, new_version: str) -> str:
    data = json.loads(content)
    old_version = data["version"]
    pattern = re.compile(rf'("version"\s*:\s*"){re.escape(old_version)}(")')
    new_content, count = pattern.subn(rf"\g<1>{new_version}\g<2>", content, count=1)
    if count == 0:
        raise ValueError(f"could not locate version field {old_version!r} in manifest")
    return new_content


def _real_include_index_probe(
    *,
    cwd: Path | None = None,
) -> Mapping[str, frozenset[str]]:
    """Map each include target to the plugins whose authored sources name it.

    The relation is read through the build's own `plugin_source_files` and
    `parse_directives`, so the index names exactly the plugins the build
    renders each fragment into. Re-deriving either the authored-source filter
    or the directive grammar here would drift from the build the moment it
    changed, which is the drift this probe exists to avoid.
    """
    root = (cwd or Path.cwd()) / SOURCE_PLUGINS_DIR
    if not root.is_dir():
        return {}
    index: dict[str, set[str]] = {}
    for plugin_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for source in sorted(plugin_dir.rglob("*")):
            if not source.is_file() or source.suffix in _IGNORED_SOURCE_SUFFIXES:
                continue
            if _IGNORED_SOURCE_DIRECTORIES.intersection(source.parts):
                continue
            try:
                text = source.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for single, double in _INCLUDE_DIRECTIVE.findall(text):
                index.setdefault(single or double, set()).add(plugin_dir.name)
    return {target: frozenset(plugins) for target, plugins in index.items()}


def _real_change_probe(
    base_ref: str,
    *,
    cwd: Path | None = None,
    include_index_probe: IncludeIndexProbe,
) -> Mapping[str, tuple[ChangedPath, ...]]:
    diff = subprocess.run(
        [
            "git",
            "diff",
            "--name-status",
            "-M",
            "-C",
            "--find-copies-harder",
            base_ref,
            "--",
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = tuple(
        change
        for line in diff.stdout.splitlines()
        if (change := _parse_diff_line(line)) is not None
    )
    # `git diff` against the base sees only tracked changes; a new skill,
    # command, or agent that is not yet committed is untracked and invisible to
    # it. Enumerate untracked, non-ignored files under every distribution root
    # and tag each Added, so the segment reflects the change the branch will
    # commit.
    others = subprocess.run(
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            *_PLUGIN_CHANGE_ROOTS,
            SHARED_SOURCE_DIR,
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    untracked = tuple(
        ChangedPath(status=FileStatus.ADDED, path=path)
        for line in others.stdout.splitlines()
        if (path := line.strip())
    )
    parsed = (*tracked, *untracked)
    shared_prefix = f"{SHARED_SOURCE_DIR}/"
    touches_shared = any(
        (change.path.startswith(shared_prefix))
        or (change.old_path or "").startswith(shared_prefix)
        for change in parsed
    )
    include_index = include_index_probe() if touches_shared else {}
    changes: dict[str, list[ChangedPath]] = {}
    for parsed_change in parsed:
        plugins = plugins_from_change(parsed_change) | plugins_from_shared_change(
            parsed_change, include_index
        )
        if not plugins:
            continue
        for plugin in plugins:
            changes.setdefault(plugin, []).append(parsed_change)
    return {plugin: tuple(paths) for plugin, paths in changes.items()}


def plugins_from_shared_change(
    change: ChangedPath, include_index: Mapping[str, frozenset[str]]
) -> frozenset[str]:
    """Plugins a shared-root change alters, resolved through `include_index`.

    A shared fragment renders into the shipped surface of every plugin whose
    authored source includes it, so the change alters those plugins even though
    no path yet carries their name. The index is supplied rather than derived
    here: this function reads no repository content, so its resolution is
    verifiable against an in-memory index.

    A rename resolves both its destination and its source include target — the
    fragment left one address and arrived at another, and both addresses reach
    the plugins that named them. A copy resolves its destination alone, because
    its source is byte-identical at `base_ref` and nothing there changed —
    matching the source attribution `plugins_from_change` performs.
    """
    paths = [change.path]
    if change.status is FileStatus.RENAMED and change.old_path is not None:
        paths.append(change.old_path)
    plugins: set[str] = set()
    for path in paths:
        if (target := _include_target_from_shared_path(path)) is None:
            continue
        plugins |= include_index.get(target, frozenset())
    return frozenset(plugins)


def _include_target_from_shared_path(path: str) -> str | None:
    """The include target a shared-root path is named by, or None."""
    prefix = f"{SHARED_SOURCE_DIR}/"
    if not path.startswith(prefix):
        return None
    target = path.removeprefix(prefix)
    return target or None


def plugins_from_change(change: ChangedPath) -> frozenset[str]:
    """Plugins one change alters, from its destination and its source path.

    A rename alters both plugins: its source path is gone at the destination's
    expense. A copy alters only the destination, because the source is
    byte-identical at `base_ref` and nothing under its prefix changed. Copy
    detection reports a copy whenever a new file resembles an existing one, and
    the build emits near-identical per-plugin lifecycle files, so attributing a
    copy's source would bump every plugin a new plugin's generated files
    happen to resemble.
    """
    plugins: set[str] = set()
    if plugin := _plugin_from_changed_path(change.path):
        plugins.add(plugin)
    if (
        change.status is FileStatus.RENAMED
        and change.old_path is not None
        and (plugin := _plugin_from_changed_path(change.old_path))
    ):
        plugins.add(plugin)
    return frozenset(plugins)


def _parse_diff_line(line: str) -> ChangedPath | None:
    if not line:
        return None
    fields = line.split("\t")
    if not fields:
        return None
    raw_status = fields[0]
    status_letter = raw_status[0] if raw_status else ""
    try:
        status = FileStatus(status_letter)
    except ValueError:
        return None
    if status in {FileStatus.COPIED, FileStatus.RENAMED}:
        if len(fields) < 3:
            return None
        return ChangedPath(status=status, path=fields[2], old_path=fields[1])
    if len(fields) < 2:
        return None
    return ChangedPath(status=status, path=fields[1])


def _real_content_probe(base_ref: str, path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{base_ref}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _real_manifest_reader(plugin: str) -> tuple[ManifestRecord, ...]:
    records: list[ManifestRecord] = []
    for manifest in _KNOWN_MANIFESTS:
        path_str = f"{SOURCE_PLUGINS_DIR}/{plugin}/{manifest}"
        path = Path(path_str)
        if path.is_file():
            records.append(ManifestRecord(path=path_str, content=path.read_text()))
    return tuple(records)


def _real_manifest_writer(path: str, new_content: str) -> None:
    Path(path).write_text(new_content)


def _real_tool_probe(name: str) -> bool:
    return shutil.which(name) is not None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outcomeeng.distribution.bump",
        description=(
            "Bump the manifest version of every plugin whose authored source or "
            "generated runtime tree has changes since base_ref. Each changed "
            "plugin's version is incremented exactly once across every manifest "
            "it owns."
        ),
    )
    parser.add_argument(
        "base_ref",
        nargs="?",
        default=_DEFAULT_BASE_REF,
        help=f"Git ref to compare against the working tree (default: {_DEFAULT_BASE_REF}).",
    )
    parser.add_argument(
        "--segment",
        choices=[s.value for s in Segment],
        default=None,
        help=(
            "Semver segment to increment. When omitted, the segment is "
            "auto-detected per plugin from the file-status pattern of "
            "changes under src/plugins/<name>/**, dist/claude/<name>/**, "
            "or dist/codex/<name>/**. When provided, overrides auto-detection "
            "for every changed plugin and emits a stderr warning naming any "
            "plugin whose detected segment differs."
        ),
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be written without touching any manifest.",
    )
    mode_group.add_argument(
        "--check",
        action="store_true",
        help=(
            "Exit non-zero if any changed plugin's working-tree version "
            "is not ahead of its base_ref version. Useful in CI."
        ),
    )
    return parser


__all__ = [
    "CLAUDE_MANIFEST",
    "CODEX_MANIFEST",
    "DIST_CLAUDE_PLUGINS_DIR",
    "DIST_CODEX_PLUGINS_DIR",
    "SHARED_SOURCE_DIR",
    "SOURCE_PLUGINS_DIR",
    "REQUIRED_TOOLS",
    "ChangeProbe",
    "ChangedPath",
    "ContentProbe",
    "IncludeIndexProbe",
    "FileStatus",
    "ManifestReader",
    "ManifestRecord",
    "ManifestWriter",
    "Mode",
    "Segment",
    "ToolProbe",
    "Version",
    "auto_segment",
    "bump",
    "changed_plugins_from_diff",
    "main",
    "plugins_from_change",
    "plugins_from_shared_change",
]


if __name__ == "__main__":
    sys.exit(main())
