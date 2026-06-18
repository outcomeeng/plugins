"""Recording doubles for the bump orchestrator.

Implements the `ChangeProbe`, `ContentProbe`, `ManifestReader`,
`ManifestWriter`, and `ToolProbe` Protocols declared in
`outcomeeng.distribution.bump`.

The doubles are spies (recording calls) and stubs (returning scripted
content), used by `l1` tests to verify bump's orchestration without
shelling out to `git` or mutating any manifest on disk.

Every double accepts an optional shared `event_log`. When supplied,
each call appends a `"{kind}:{payload}"` string in invocation order.
The shared log is the only observable ordering channel across distinct
Protocol boundaries (per-probe `queries`/`writes` lists are local).

Exception cases per `plugins/spec-tree/skills/test/references/methodology.md`:

- Stage 5 #2 (Interaction protocols): bump's correctness depends on the
  sequence and presence of probe calls, manifest reads, and manifest
  writes — the read-then-write phase split and the tool-first ordering
  are part of the contract.
- Stage 5 #4 (Safety): real bump mutates committed plugin manifests in
  the working tree; tests must not touch the repository's own manifests.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
from dataclasses import dataclass, field

from collections.abc import Mapping

from outcomeeng.distribution.bump import (
    ChangedPath,
    ChangeProbe,
    ContentProbe,
    ManifestReader,
    ManifestRecord,
    ManifestWriter,
    ToolProbe,
)


@dataclass
class RecordingToolProbe:
    """ToolProbe that returns True only for tools in `available`."""

    available: frozenset[str]
    queries: list[str] = field(default_factory=list)
    event_log: list[str] | None = None

    def __call__(self, name: str) -> bool:
        self.queries.append(name)
        if self.event_log is not None:
            self.event_log.append(f"tool:{name}")
        return name in self.available


@dataclass
class ScriptedChangeProbe:
    """ChangeProbe that returns a scripted plugin→changed-paths mapping.

    `changed` maps plugin name → tuple of `ChangedPath` values; the probe
    returns the mapping unchanged for any `base_ref` query.
    """

    changed: Mapping[str, tuple[ChangedPath, ...]]
    queries: list[str] = field(default_factory=list)
    event_log: list[str] | None = None

    def __call__(self, base_ref: str) -> Mapping[str, tuple[ChangedPath, ...]]:
        self.queries.append(base_ref)
        if self.event_log is not None:
            self.event_log.append(f"change:{base_ref}")
        return self.changed


@dataclass
class ScriptedContentProbe:
    """ContentProbe that returns scripted content for `(base_ref, path)` keys.

    Unknown keys return None, modelling a path that does not exist at the
    given ref. `queries` records every `(base_ref, path)` lookup in order.
    """

    content: dict[tuple[str, str], str]
    queries: list[tuple[str, str]] = field(default_factory=list)
    event_log: list[str] | None = None

    def __call__(self, base_ref: str, path: str) -> str | None:
        self.queries.append((base_ref, path))
        if self.event_log is not None:
            self.event_log.append(f"content:{base_ref}:{path}")
        return self.content.get((base_ref, path))


@dataclass
class ScriptedManifestReader:
    """ManifestReader that returns scripted manifests per plugin name.

    `manifests` maps plugin name → tuple of `ManifestRecord` values. An
    unmapped plugin name returns an empty tuple, modelling a plugin
    directory with no recognized manifests.
    """

    manifests: dict[str, tuple[ManifestRecord, ...]]
    queries: list[str] = field(default_factory=list)
    event_log: list[str] | None = None

    def __call__(self, plugin: str) -> tuple[ManifestRecord, ...]:
        self.queries.append(plugin)
        if self.event_log is not None:
            self.event_log.append(f"reader:{plugin}")
        return self.manifests.get(plugin, ())


@dataclass
class RecordingManifestWriter:
    """ManifestWriter that records every `(path, new_content)` write."""

    writes: list[tuple[str, str]] = field(default_factory=list)
    event_log: list[str] | None = None

    def __call__(self, path: str, new_content: str) -> None:
        self.writes.append((path, new_content))
        if self.event_log is not None:
            self.event_log.append(f"writer:{path}")


CHANGE_DETECT_PLUGIN = "demo"
_PLUGIN_ROOT = f"src/plugins/{CHANGE_DETECT_PLUGIN}"
TRACKED_MODIFIED_PATH = f"{_PLUGIN_ROOT}/skills/existing/SKILL.md"
MANIFEST_PATH = f"{_PLUGIN_ROOT}/.claude-plugin/plugin.json"
UNTRACKED_ADDED_PATH = f"{_PLUGIN_ROOT}/skills/new-skill/SKILL.md"


@dataclass(frozen=True)
class UntrackedSkillRepo:
    """A real git repo whose working tree carries a tracked edit plus an
    untracked new skill under a plugin directory.

    ``base_ref`` is the committed base. ``tracked_modified_path`` was committed
    at the base and then modified (an unstaged ``M`` against the base);
    ``untracked_added_path`` is a brand-new structural file that was never
    committed or staged — invisible to ``git diff`` against the base.
    """

    repo: pathlib.Path
    base_ref: str
    plugin: str
    tracked_modified_path: str
    untracked_added_path: str


def _run_git(repo: pathlib.Path, *args: str) -> None:
    """Run a git command with isolated config and a fixed identity."""
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    subprocess.run(  # noqa: S603 — fixed argv, no shell, args from the harness
        ["git", *args],  # noqa: S607
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def _write(repo: pathlib.Path, rel: str, content: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_repo_with_untracked_new_skill(repo: pathlib.Path) -> UntrackedSkillRepo:
    """Commit a plugin base, then leave a tracked edit and an untracked new skill.

    Sequence: initialise the repo; commit a plugin manifest and one existing
    skill as the base; modify the existing skill (tracked, unstaged); add a new
    skill file without staging it (untracked). A ``git diff`` against the base
    sees only the modification; the untracked new skill is recoverable only
    through ``git ls-files --others``.
    """
    repo.mkdir(parents=True, exist_ok=True)
    _run_git(repo, "init", "-q", "-b", "main")
    _run_git(repo, "config", "commit.gpgsign", "false")
    _write(repo, MANIFEST_PATH, '{\n  "name": "demo",\n  "version": "0.1.0"\n}\n')
    _write(repo, TRACKED_MODIFIED_PATH, "---\nname: existing\n---\n\nv1\n")
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "base")
    base_ref = "HEAD"

    (repo / TRACKED_MODIFIED_PATH).write_text(
        "---\nname: existing\n---\n\nv2\n", encoding="utf-8"
    )
    _write(repo, UNTRACKED_ADDED_PATH, "---\nname: new-skill\n---\n\nnew\n")

    return UntrackedSkillRepo(
        repo=repo,
        base_ref=base_ref,
        plugin=CHANGE_DETECT_PLUGIN,
        tracked_modified_path=TRACKED_MODIFIED_PATH,
        untracked_added_path=UNTRACKED_ADDED_PATH,
    )


__all__ = [
    "RecordingManifestWriter",
    "RecordingToolProbe",
    "ScriptedChangeProbe",
    "ScriptedContentProbe",
    "ScriptedManifestReader",
    "UntrackedSkillRepo",
    "build_repo_with_untracked_new_skill",
]


_: type[ChangeProbe] = ScriptedChangeProbe
_2: type[ContentProbe] = ScriptedContentProbe
_3: type[ManifestReader] = ScriptedManifestReader
_4: type[ManifestWriter] = RecordingManifestWriter
_5: type[ToolProbe] = RecordingToolProbe
