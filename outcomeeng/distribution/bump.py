"""Manifest version-bumping orchestration.

Bumps the manifest version of every plugin whose `src/plugins/{name}/**` tree
has changes since a base reference (default `origin/main`). Each changed
plugin's version is incremented exactly once across every manifest it
owns (`.claude-plugin/plugin.json` always; `.codex-plugin/plugin.json`
when present). The increment segment defaults to `patch`; `minor` and
`major` are explicit opt-ins.

The module's contract:

- `SOURCE_PLUGINS_DIR`, `CLAUDE_MANIFEST`, `CODEX_MANIFEST` name the path prefix
  and manifest filenames the orchestration recognizes.
- `REQUIRED_TOOLS` names the external binaries `main()` shells out to.
- `Version`, `Segment`, and `ManifestRecord` are the domain dataclasses.
- `ChangeProbe`, `ContentProbe`, `ManifestReader`, `ManifestWriter`,
  `ToolProbe` Protocols describe the injected side-effecting boundaries.
- `bump()` runs the orchestration; tests substitute controlled Protocol
  implementations.
- `changed_plugins_from_diff()` is the pure path-prefix filter the
  production `_real_change_probe` adapter delegates to.
- `main()` wires real `git diff` / `git show` / `Path` adapters.
"""

from __future__ import annotations

import argparse
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

REQUIRED_TOOLS: tuple[str, ...] = ("git",)
SOURCE_PLUGINS_DIR: str = "src/plugins"
CLAUDE_MANIFEST: str = ".claude-plugin/plugin.json"
CODEX_MANIFEST: str = ".codex-plugin/plugin.json"

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


@dataclass(frozen=True)
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


@dataclass(frozen=True)
class ManifestRecord:
    """Working-tree state of one manifest a plugin owns."""

    path: str
    content: str


class ChangeProbe(Protocol):
    """Returns a mapping from plugin name to the file-status-tagged paths
    that changed under `src/plugins/{name}/**` since `base_ref`."""

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


def changed_plugins_from_diff(paths: Iterable[str]) -> frozenset[str]:
    """Filter diff paths to the set of plugin names changed."""
    plugins: set[str] = set()
    source_parts = SOURCE_PLUGINS_DIR.split("/")
    for path in paths:
        parts = path.split("/")
        if (
            len(parts) > len(source_parts)
            and parts[: len(source_parts)] == source_parts
            and parts[len(source_parts)]
        ):
            plugins.add(parts[len(source_parts)])
    return frozenset(plugins)


def auto_segment(changes: Iterable[ChangedPath]) -> Segment:
    """Resolve the warranted semver segment from a plugin's changed paths.

    An `A`/`C`/`D`/`R` change to a structural path inside the plugin yields
    `MINOR`; every other pattern yields `PATCH`. Auto-detection never
    selects `MAJOR`; major bumps require explicit human opt-in.

    Structural paths (relative to `src/plugins/{name}/`):

    - `skills/{slug}/SKILL.md`
    - `commands/{slug}.md`
    - `agents/{slug}.md`
    - `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`
    """
    for change in changes:
        if change.status is FileStatus.MODIFIED:
            continue
        if _is_minor_triggering_path(change.path):
            return Segment.MINOR
    return Segment.PATCH


def _is_minor_triggering_path(path: str) -> bool:
    parts = path.split("/")
    source_parts = SOURCE_PLUGINS_DIR.split("/")
    if (
        len(parts) < len(source_parts) + 3
        or parts[: len(source_parts)] != source_parts
        or not parts[len(source_parts)]
    ):
        return False
    rest = parts[len(source_parts) + 1 :]
    if len(rest) == 3 and rest[0] == "skills" and rest[2] == "SKILL.md":
        return True
    if len(rest) == 2 and rest[0] in ("commands", "agents") and rest[1].endswith(".md"):
        return True
    if (
        len(rest) == 2
        and rest[0] in (".claude-plugin", ".codex-plugin")
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

    plans: list[tuple[str, ManifestRecord, Version, Segment]] = []
    already_bumped_plugins: list[str] = []
    unbumped_plugins: list[str] = []
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
        plugin_already_bumped = False
        for record in records:
            working_tree_version = _version_from_manifest_text(record.content)
            base_ref_content = _base_manifest_content_for_record(
                content_probe, base_ref, record.path, plugin_changes
            )
            if base_ref_content is not None:
                base_ref_version = _version_from_manifest_text(base_ref_content)
                if working_tree_version != base_ref_version:
                    plugin_already_bumped = True
            plans.append((plugin, record, working_tree_version, resolved))
        if plugin_already_bumped:
            already_bumped_plugins.append(plugin)
        else:
            unbumped_plugins.append(plugin)

    if mode is Mode.CHECK:
        if unbumped_plugins:
            for plugin in unbumped_plugins:
                print(
                    f"Plugin {plugin} needs a version bump but its "
                    f"working-tree version still equals its {base_ref} version",
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
    for plugin, record, working_tree_version, resolved in plans:
        if plugin in skip:
            continue
        increment = _SEGMENT_DISPATCH[resolved]
        new_version = increment(working_tree_version)
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
        change_probe=_real_change_probe,
        content_probe=_real_content_probe,
        manifest_reader=_real_manifest_reader,
        manifest_writer=_real_manifest_writer,
        tool_probe=_real_tool_probe,
    )


def _version_from_manifest_text(content: str) -> Version:
    data = json.loads(content)
    return Version.parse(data["version"])


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


def _real_change_probe(base_ref: str) -> Mapping[str, tuple[ChangedPath, ...]]:
    result = subprocess.run(
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
        capture_output=True,
        text=True,
        check=True,
    )
    changes: dict[str, list[ChangedPath]] = {}
    parsed_changes = tuple(
        change
        for line in result.stdout.splitlines()
        if (change := _parse_diff_line(line)) is not None
    )
    for parsed_change in parsed_changes:
        parts = parsed_change.path.split("/")
        source_parts = SOURCE_PLUGINS_DIR.split("/")
        if (
            len(parts) <= len(source_parts)
            or parts[: len(source_parts)] != source_parts
            or not parts[len(source_parts)]
        ):
            continue
        changes.setdefault(parts[len(source_parts)], []).append(parsed_change)
    return {plugin: tuple(paths) for plugin, paths in changes.items()}


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
            "Bump the manifest version of every plugin whose `src/plugins/{name}/**` "
            "tree has changes since base_ref. Each changed plugin's version is "
            "incremented exactly once across every manifest it owns."
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
            "changes under src/plugins/<name>/**. When provided, overrides "
            "auto-detection for every changed plugin and emits a stderr "
            "warning naming any plugin whose detected segment differs."
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
            "still equals its base_ref version. Useful in CI."
        ),
    )
    return parser


__all__ = [
    "CLAUDE_MANIFEST",
    "CODEX_MANIFEST",
    "SOURCE_PLUGINS_DIR",
    "REQUIRED_TOOLS",
    "ChangeProbe",
    "ChangedPath",
    "ContentProbe",
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
]


if __name__ == "__main__":
    sys.exit(main())
