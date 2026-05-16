"""Manifest version-bumping orchestration.

Bumps the manifest version of every plugin whose `plugins/{name}/**` tree
has changes since a base reference (default `origin/main`). Each changed
plugin's version is incremented exactly once across every manifest it
owns (`.claude-plugin/plugin.json` always; `.codex-plugin/plugin.json`
when present). The increment segment defaults to `patch`; `minor` and
`major` are explicit opt-ins.

The module's contract:

- `PLUGINS_DIR`, `CLAUDE_MANIFEST`, `CODEX_MANIFEST` name the path prefix
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
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

REQUIRED_TOOLS: tuple[str, ...] = ("git",)
PLUGINS_DIR: str = "plugins"
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
    """Returns the set of plugin names with any path under
    `plugins/{name}/**` changed since `base_ref`."""

    def __call__(self, base_ref: str) -> frozenset[str]: ...


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
    """Filter diff paths to the set of plugin names changed.

    A path counts as a change for plugin `{name}` exactly when its first
    two segments are `plugins/{name}` with a non-empty `{name}`. Paths
    outside the `plugins/` prefix produce no entry.
    """
    plugins: set[str] = set()
    for path in paths:
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] == PLUGINS_DIR and parts[1]:
            plugins.add(parts[1])
    return frozenset(plugins)


def bump(
    base_ref: str,
    segment: Segment,
    *,
    mode: Mode = Mode.WRITE,
    change_probe: ChangeProbe,
    content_probe: ContentProbe,
    manifest_reader: ManifestReader,
    manifest_writer: ManifestWriter,
    tool_probe: ToolProbe,
) -> int:
    """Run the bump orchestration. Returns the process exit code."""
    for tool in REQUIRED_TOOLS:
        if not tool_probe(tool):
            print(f"Missing required tool: {tool}", file=sys.stderr)
            return 1

    changed = change_probe(base_ref)
    if not changed:
        return 0

    plans: list[tuple[str, ManifestRecord, Version]] = []
    already_bumped_plugins: list[str] = []
    unbumped_plugins: list[str] = []
    for plugin in sorted(changed):
        records = manifest_reader(plugin)
        if not records:
            continue
        plugin_already_bumped = False
        for record in records:
            working_tree_version = _version_from_manifest_text(record.content)
            base_ref_content = content_probe(base_ref, record.path)
            if base_ref_content is not None:
                base_ref_version = _version_from_manifest_text(base_ref_content)
                if working_tree_version != base_ref_version:
                    plugin_already_bumped = True
            plans.append((plugin, record, working_tree_version))
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

    if already_bumped_plugins:
        for plugin in already_bumped_plugins:
            print(
                f"Plugin {plugin} already has a version bump on this branch",
                file=sys.stderr,
            )
        return 1

    increment = _SEGMENT_DISPATCH[segment]
    for plugin, record, working_tree_version in plans:
        new_version = increment(working_tree_version)
        if mode is Mode.DRY_RUN:
            print(f"{plugin}: {record.path} {working_tree_version} -> {new_version}")
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
    return bump(
        args.base_ref,
        Segment(args.segment),
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


def _replace_version(content: str, new_version: str) -> str:
    data = json.loads(content)
    old_version = data["version"]
    pattern = re.compile(rf'("version"\s*:\s*"){re.escape(old_version)}(")')
    new_content, count = pattern.subn(rf"\g<1>{new_version}\g<2>", content, count=1)
    if count == 0:
        raise ValueError(f"could not locate version field {old_version!r} in manifest")
    return new_content


def _real_change_probe(base_ref: str) -> frozenset[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "--"],
        capture_output=True,
        text=True,
        check=True,
    )
    return changed_plugins_from_diff(result.stdout.splitlines())


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
        path_str = f"{PLUGINS_DIR}/{plugin}/{manifest}"
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
            "Bump the manifest version of every plugin whose `plugins/{name}/**` "
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
        default=Segment.PATCH.value,
        help="Semver segment to increment (default: patch).",
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
    "PLUGINS_DIR",
    "REQUIRED_TOOLS",
    "ChangeProbe",
    "ContentProbe",
    "ManifestReader",
    "ManifestRecord",
    "ManifestWriter",
    "Mode",
    "Segment",
    "ToolProbe",
    "Version",
    "bump",
    "changed_plugins_from_diff",
    "main",
]


if __name__ == "__main__":
    sys.exit(main())
