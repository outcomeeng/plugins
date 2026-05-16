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

Exception cases per `plugins/spec-tree/skills/testing/references/methodology.md`:

- Stage 5 #2 (Interaction protocols): bump's correctness depends on the
  sequence and presence of probe calls, manifest reads, and manifest
  writes — the read-then-write phase split and the tool-first ordering
  are part of the contract.
- Stage 5 #4 (Safety): real bump mutates committed plugin manifests in
  the working tree; tests must not touch the repository's own manifests.
"""

from __future__ import annotations

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


__all__ = [
    "RecordingManifestWriter",
    "RecordingToolProbe",
    "ScriptedChangeProbe",
    "ScriptedContentProbe",
    "ScriptedManifestReader",
]


_: type[ChangeProbe] = ScriptedChangeProbe
_2: type[ContentProbe] = ScriptedContentProbe
_3: type[ManifestReader] = ScriptedManifestReader
_4: type[ManifestWriter] = RecordingManifestWriter
_5: type[ToolProbe] = RecordingToolProbe
