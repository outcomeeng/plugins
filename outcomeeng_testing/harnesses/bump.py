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

- Stage 5 #2 (Interaction protocols): bump's correctness depends on the
  sequence and presence of probe calls, manifest reads, and manifest
  writes — the read-then-write phase split and the tool-first ordering
  are part of the contract.
- Stage 5 #4 (Safety): real bump mutates committed plugin manifests in
  the working tree; tests must not touch the repository's own manifests.
"""

from __future__ import annotations

import contextlib
import io
import os
import pathlib
import subprocess
from tempfile import TemporaryDirectory
from dataclasses import dataclass, field

from collections.abc import Callable, Mapping

from hypothesis import given, seed, settings
from hypothesis import strategies as st

from outcomeeng.distribution.bump import (
    ChangedPath,
    ChangeProbe,
    CODEX_MANIFEST,
    CLAUDE_MANIFEST,
    ContentProbe,
    DIST_CODEX_PLUGINS_DIR,
    FileStatus,
    ManifestReader,
    ManifestRecord,
    ManifestWriter,
    Mode,
    SOURCE_PLUGINS_DIR,
    ToolProbe,
    REQUIRED_TOOLS,
    Segment,
    _real_change_probe,
    bump,
    main,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    CODEX_PLUGIN_SUBDIR_NAME,
    MARKDOWN_FILE_SUFFIX,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
)
from outcomeeng_testing.generators.bump import (
    arbitrary_diff_paths,
    distribution_roots,
    manifest_fixture_path,
    manifest_relpath,
    manifest_text,
    malformed_manifest_cases,
    minor_change,
    patch_changes,
    plugin_names,
    relative_subpaths,
)

TOOL_EVENT_PREFIX = "tool:"
BUMP_PROPERTY_SEED = 20260704
BUMP_PROPERTY_EXAMPLES = 50
DIFF_PATH_LIST_MAX_SIZE = 12
BUMP_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/32-distribution.enabler/21-bump.enabler/tests/test_bump.property.l1.py"
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
            self.event_log.append(f"{TOOL_EVENT_PREFIX}{name}")
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


@dataclass(frozen=True)
class BumpOutcome:
    """Everything one bump invocation exposed to its caller."""

    exit_code: int
    writes: tuple[tuple[str, str], ...]
    written: dict[str, str]
    stdout: str
    stderr: str
    change_queries: tuple[str, ...]
    content_queries: tuple[tuple[str, str], ...]
    reader_queries: tuple[str, ...]
    tool_queries: tuple[str, ...]

    @property
    def diagnostics(self) -> str:
        """Return both captured streams for a diagnostic-content assertion."""
        return self.stderr + self.stdout


@dataclass(frozen=True)
class MissingToolOutcome:
    """One bump invocation run with a single required tool withheld."""

    missing_tool: str
    outcome: BumpOutcome


@dataclass(frozen=True)
class SingleManifestOutcome:
    """A single-manifest plugin's identity paired with its bump outcome."""

    plugin: str
    path: str
    outcome: BumpOutcome


@dataclass(frozen=True)
class DualManifestOutcome:
    """A dual-manifest plugin's identity paired with its bump outcome."""

    plugin: str
    claude_path: str
    codex_path: str
    outcome: BumpOutcome


@dataclass(frozen=True)
class TwoPluginOutcome:
    """Two changed plugins' identities paired with one shared bump outcome."""

    already_bumped_plugin: str
    already_bumped_path: str
    unbumped_plugin: str
    unbumped_path: str
    outcome: BumpOutcome


@dataclass(frozen=True)
class BumpRun:
    """Complete injected bump call with its recording boundaries."""

    change_probe: ScriptedChangeProbe
    content_probe: ScriptedContentProbe
    manifest_reader: ScriptedManifestReader
    manifest_writer: RecordingManifestWriter
    tool_probe: RecordingToolProbe

    def run(
        self, segment: Segment | None = Segment.PATCH, mode: Mode = Mode.WRITE
    ) -> int:
        return bump(
            base_ref(),
            segment,
            mode=mode,
            change_probe=self.change_probe,
            content_probe=self.content_probe,
            manifest_reader=self.manifest_reader,
            manifest_writer=self.manifest_writer,
            tool_probe=self.tool_probe,
        )

    def written(self) -> dict[str, str]:
        return dict(self.manifest_writer.writes)

    def capture(
        self, segment: Segment | None = Segment.PATCH, mode: Mode = Mode.WRITE
    ) -> BumpOutcome:
        """Run bump while capturing its streams and recorded boundary calls."""
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = self.run(segment, mode)
        return BumpOutcome(
            exit_code=exit_code,
            writes=tuple(self.manifest_writer.writes),
            written=dict(self.manifest_writer.writes),
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            change_queries=tuple(self.change_probe.queries),
            content_queries=tuple(self.content_probe.queries),
            reader_queries=tuple(self.manifest_reader.queries),
            tool_queries=tuple(self.tool_probe.queries),
        )


@dataclass(frozen=True)
class DualManifestCase:
    """Harness case for a changed plugin owning Claude and Codex manifests."""

    plugin: str
    claude_path: str
    codex_path: str
    run: BumpRun


@dataclass(frozen=True)
class SingleManifestCase:
    """Harness case for a changed plugin owning one Claude manifest."""

    plugin: str
    path: str
    run: BumpRun


def base_ref() -> str:
    return "origin/main"


def all_tools_available() -> frozenset[str]:
    return frozenset(REQUIRED_TOOLS)


def dual_manifest_case(
    plugin: str,
    *,
    claude_version: str,
    codex_version: str,
    claude_base_version: str | None = None,
    codex_base_version: str | None = None,
) -> DualManifestCase:
    claude_base = (
        claude_base_version if claude_base_version is not None else claude_version
    )
    codex_base = codex_base_version if codex_base_version is not None else codex_version
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    codex_path = manifest_relpath(plugin, CODEX_MANIFEST)
    claude_content = manifest_text(plugin, claude_version)
    codex_content = manifest_text(plugin, codex_version)
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed=patch_changes(plugin)),
        content_probe=ScriptedContentProbe(
            content={
                (base_ref(), claude_path): manifest_text(plugin, claude_base),
                (base_ref(), codex_path): manifest_text(plugin, codex_base),
            },
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={
                plugin: (
                    ManifestRecord(path=claude_path, content=claude_content),
                    ManifestRecord(path=codex_path, content=codex_content),
                )
            },
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return DualManifestCase(
        plugin=plugin,
        claude_path=claude_path,
        codex_path=codex_path,
        run=run,
    )


def single_manifest_case(
    plugin: str,
    *,
    version: str,
    base_version: str | None = None,
) -> SingleManifestCase:
    base = base_version if base_version is not None else version
    path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, version)
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed=patch_changes(plugin)),
        content_probe=ScriptedContentProbe(
            content={(base_ref(), path): manifest_text(plugin, base)},
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={plugin: (ManifestRecord(path=path, content=content),)},
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return SingleManifestCase(plugin=plugin, path=path, run=run)


def observe_missing_required_tool_runs() -> tuple[MissingToolOutcome, ...]:
    """Run bump once per required tool, withholding that tool each time."""
    outcomes: list[MissingToolOutcome] = []
    for missing_tool in REQUIRED_TOOLS:
        run = BumpRun(
            change_probe=ScriptedChangeProbe(changed=patch_changes("foo")),
            content_probe=ScriptedContentProbe(content={}),
            manifest_reader=ScriptedManifestReader(manifests={}),
            manifest_writer=RecordingManifestWriter(),
            tool_probe=RecordingToolProbe(
                available=all_tools_available() - {missing_tool}
            ),
        )
        outcomes.append(
            MissingToolOutcome(missing_tool=missing_tool, outcome=run.capture())
        )
    return tuple(outcomes)


def observe_probe_ordering() -> tuple[int, tuple[str, ...]]:
    """Return the exit code and ordered boundary events of one bump run."""
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")
    event_log: list[str] = []
    run = BumpRun(
        change_probe=ScriptedChangeProbe(
            changed=patch_changes(plugin), event_log=event_log
        ),
        content_probe=ScriptedContentProbe(
            content={(base_ref(), claude_path): content}, event_log=event_log
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={plugin: (ManifestRecord(path=claude_path, content=content),)},
            event_log=event_log,
        ),
        manifest_writer=RecordingManifestWriter(event_log=event_log),
        tool_probe=RecordingToolProbe(
            available=all_tools_available(), event_log=event_log
        ),
    )

    exit_code = run.run()
    return exit_code, tuple(event_log)


def observe_already_bumped_plugin(mode: Mode = Mode.WRITE) -> SingleManifestOutcome:
    """Run bump against a plugin whose working tree is already ahead of base."""
    case = single_manifest_case("foo", version="0.4.2", base_version="0.4.1")
    return SingleManifestOutcome(
        plugin=case.plugin, path=case.path, outcome=case.run.capture(mode=mode)
    )


def observe_already_bumped_beside_unbumped_plugin(
    mode: Mode = Mode.WRITE,
) -> TwoPluginOutcome:
    """Run bump over one already-bumped and one unbumped changed plugin."""
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_path = manifest_relpath("bar", CLAUDE_MANIFEST)
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed=patch_changes("foo", "bar")),
        content_probe=ScriptedContentProbe(
            content={
                (base_ref(), foo_path): manifest_text("foo", "0.4.1"),
                (base_ref(), bar_path): manifest_text("bar", "0.4.1"),
            },
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={
                "foo": (
                    ManifestRecord(
                        path=foo_path, content=manifest_text("foo", "0.4.2")
                    ),
                ),
                "bar": (
                    ManifestRecord(
                        path=bar_path, content=manifest_text("bar", "0.4.1")
                    ),
                ),
            },
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return TwoPluginOutcome(
        already_bumped_plugin="foo",
        already_bumped_path=foo_path,
        unbumped_plugin="bar",
        unbumped_path=bar_path,
        outcome=run.capture(mode=mode),
    )


def observe_mixed_dual_manifest_plugin(
    *,
    claude_version: str,
    segment: Segment | None = Segment.PATCH,
    mode: Mode = Mode.WRITE,
) -> DualManifestOutcome:
    """Run bump against a dual-manifest plugin whose owned versions differ."""
    case = dual_manifest_case(
        "foo",
        claude_version=claude_version,
        codex_version="0.4.1",
        claude_base_version="0.4.1",
        codex_base_version="0.4.1",
    )
    return DualManifestOutcome(
        plugin=case.plugin,
        claude_path=case.claude_path,
        codex_path=case.codex_path,
        outcome=case.run.capture(segment=segment, mode=mode),
    )


def observe_new_plugin_without_base_manifest() -> BumpOutcome:
    """Run check mode for a changed plugin absent from the base reference."""
    plugin = "foo"
    path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed={plugin: minor_change(plugin)}),
        content_probe=ScriptedContentProbe(content={}),
        manifest_reader=ScriptedManifestReader(
            manifests={
                plugin: (
                    ManifestRecord(path=path, content=manifest_text(plugin, "0.1.0")),
                )
            },
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return run.capture(segment=None, mode=Mode.CHECK)


def observe_unchanged_plugins_run() -> tuple[str, BumpOutcome]:
    """Run bump where only one of three readable plugins has changes."""
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    foo_content = manifest_text("foo", "0.4.1")
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed=patch_changes("foo")),
        content_probe=ScriptedContentProbe(
            content={(base_ref(), foo_path): foo_content},
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={
                "foo": (ManifestRecord(path=foo_path, content=foo_content),),
                "bar": (
                    ManifestRecord(
                        path=manifest_relpath("bar", CLAUDE_MANIFEST),
                        content=manifest_text("bar", "0.4.1"),
                    ),
                ),
                "baz": (
                    ManifestRecord(
                        path=manifest_relpath("baz", CLAUDE_MANIFEST),
                        content=manifest_text("baz", "0.4.1"),
                    ),
                ),
            },
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return foo_path, run.capture()


def observe_fixture_manifest_rewrite() -> tuple[str, str, BumpOutcome]:
    """Bump a whole-payload manifest fixture and return its path and original."""
    plugin = "fixture-plugin"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    original = manifest_fixture_path("representative_plugin.json").read_text()
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed=patch_changes(plugin)),
        content_probe=ScriptedContentProbe(
            content={(base_ref(), claude_path): original},
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={plugin: (ManifestRecord(path=claude_path, content=original),)},
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return claude_path, original, run.capture()


def observe_read_only_mode_runs() -> tuple[BumpOutcome, ...]:
    """Run every read-only mode against bumped and unbumped plugin states."""
    outcomes: list[BumpOutcome] = []
    for mode in (Mode.DRY_RUN, Mode.CHECK):
        for wt_version, base_version in (("0.4.1", "0.4.1"), ("0.4.2", "0.4.1")):
            case = single_manifest_case(
                "foo", version=wt_version, base_version=base_version
            )
            outcomes.append(case.run.capture(mode=mode))
    return tuple(outcomes)


def observe_malformed_manifest_runs() -> tuple[tuple[str, str, BumpOutcome], ...]:
    """Bump each malformed manifest case and return path, expected text, outcome."""
    plugin = "foo"
    path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    outcomes: list[tuple[str, str, BumpOutcome]] = []
    for case in malformed_manifest_cases(plugin):
        run = BumpRun(
            change_probe=ScriptedChangeProbe(changed=patch_changes(plugin)),
            content_probe=ScriptedContentProbe(
                content={(base_ref(), path): manifest_text(plugin, "0.4.1")},
            ),
            manifest_reader=ScriptedManifestReader(
                manifests={plugin: (ManifestRecord(path=path, content=case.content),)},
            ),
            manifest_writer=RecordingManifestWriter(),
            tool_probe=RecordingToolProbe(available=all_tools_available()),
        )
        outcomes.append((path, case.expected_diagnostic, run.capture()))
    return tuple(outcomes)


def observe_cli_dry_run_check_combination() -> tuple[int | str | None, str]:
    """Invoke the CLI with both read-only flags and return its exit and stderr."""
    stderr = io.StringIO()
    try:
        with contextlib.redirect_stderr(stderr):
            main(["--dry-run", "--check"])
    except SystemExit as exc:
        return exc.code, stderr.getvalue()
    raise RuntimeError("the CLI accepted --dry-run together with --check")


def observe_all_minor_triggering_changes_run() -> tuple[str, BumpOutcome]:
    """Run auto-detected bump where every change triggers a minor segment."""
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")
    changes = (
        ChangedPath(
            FileStatus.ADDED,
            f"{SOURCE_PLUGINS_DIR}/{plugin}/{SKILLS_SUBDIR_NAME}/new/{SKILL_FILENAME}",
        ),
        ChangedPath(
            FileStatus.ADDED,
            f"{SOURCE_PLUGINS_DIR}/{plugin}/{AGENTS_SUBDIR_NAME}/new-agent{MARKDOWN_FILE_SUFFIX}",
        ),
        ChangedPath(
            FileStatus.ADDED,
            f"{SOURCE_PLUGINS_DIR}/{plugin}/{CODEX_PLUGIN_SUBDIR_NAME}/plugin.json",
        ),
    )
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed={plugin: changes}),
        content_probe=ScriptedContentProbe(
            content={(base_ref(), claude_path): content},
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={plugin: (ManifestRecord(path=claude_path, content=content),)},
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )

    return claude_path, run.capture(segment=None)


def observe_single_changed_plugin_run() -> tuple[str, str, BumpOutcome]:
    """Run bump where only one of two readable plugins has changes."""
    foo_claude = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_claude = manifest_relpath("bar", CLAUDE_MANIFEST)
    foo_content = manifest_text("foo", "0.4.1")
    bar_content = manifest_text("bar", "0.4.1")
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed=patch_changes("foo")),
        content_probe=ScriptedContentProbe(
            content={
                (base_ref(), foo_claude): foo_content,
                (base_ref(), bar_claude): bar_content,
            },
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={
                "foo": (ManifestRecord(path=foo_claude, content=foo_content),),
                "bar": (ManifestRecord(path=bar_claude, content=bar_content),),
            },
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )

    return foo_claude, "bar", run.capture()


def observe_dual_manifest_plugin(
    segment: Segment | None = Segment.PATCH,
) -> DualManifestOutcome:
    """Run bump against a dual-manifest plugin whose owned versions agree."""
    case = dual_manifest_case("foo", claude_version="0.4.1", codex_version="0.4.1")
    return DualManifestOutcome(
        plugin=case.plugin,
        claude_path=case.claude_path,
        codex_path=case.codex_path,
        outcome=case.run.capture(segment=segment),
    )


def observe_segment_selection_runs() -> tuple[
    tuple[Segment, SingleManifestOutcome], ...
]:
    """Run bump once per explicit segment against the same starting version."""
    runs: list[tuple[Segment, SingleManifestOutcome]] = []
    for segment in Segment:
        case = single_manifest_case("foo", version="0.4.1")
        runs.append(
            (
                segment,
                SingleManifestOutcome(
                    plugin=case.plugin,
                    path=case.path,
                    outcome=case.run.capture(segment=segment),
                ),
            )
        )
    return tuple(runs)


def observe_no_changed_plugins_run() -> BumpOutcome:
    """Run bump where the change probe reports no changed plugin at all."""
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed={}),
        content_probe=ScriptedContentProbe(content={}),
        manifest_reader=ScriptedManifestReader(manifests={}),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return run.capture()


def observe_dry_run_report() -> SingleManifestOutcome:
    """Run bump in dry-run mode against an unbumped changed plugin."""
    case = single_manifest_case("foo", version="0.4.1")
    return SingleManifestOutcome(
        plugin=case.plugin, path=case.path, outcome=case.run.capture(mode=Mode.DRY_RUN)
    )


def observe_check_all_plugins_bumped() -> BumpOutcome:
    """Run check mode where every changed plugin already carries a bump."""
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_path = manifest_relpath("bar", CLAUDE_MANIFEST)
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed=patch_changes("foo", "bar")),
        content_probe=ScriptedContentProbe(
            content={
                (base_ref(), foo_path): manifest_text("foo", "0.4.1"),
                (base_ref(), bar_path): manifest_text("bar", "0.4.7"),
            },
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={
                "foo": (
                    ManifestRecord(
                        path=foo_path, content=manifest_text("foo", "0.4.2")
                    ),
                ),
                "bar": (
                    ManifestRecord(
                        path=bar_path, content=manifest_text("bar", "0.5.0")
                    ),
                ),
            },
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return run.capture(segment=None, mode=Mode.CHECK)


def observe_below_base_plugin(mode: Mode = Mode.WRITE) -> SingleManifestOutcome:
    """Run bump where the working-tree version trails the base version."""
    case = single_manifest_case("foo", version="0.72.4", base_version="0.73.0")
    return SingleManifestOutcome(
        plugin=case.plugin, path=case.path, outcome=case.run.capture(mode=mode)
    )


def observe_base_source_path_comparison(
    status: FileStatus,
) -> tuple[str, str, BumpOutcome]:
    """Run check mode for a manifest whose base content lives at its old path."""
    return _observe_manifest_against_base_source_path(status)


def observe_check_unbumped_plugin() -> SingleManifestOutcome:
    """Run check mode against a changed plugin that carries no bump yet."""
    case = single_manifest_case("foo", version="0.4.1")
    return SingleManifestOutcome(
        plugin=case.plugin, path=case.path, outcome=case.run.capture(mode=Mode.CHECK)
    )


def observe_check_one_plugin_unbumped() -> TwoPluginOutcome:
    """Run check mode where one changed plugin is bumped and one is not."""
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_path = manifest_relpath("bar", CLAUDE_MANIFEST)
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed=patch_changes("foo", "bar")),
        content_probe=ScriptedContentProbe(
            content={
                (base_ref(), foo_path): manifest_text("foo", "0.4.1"),
                (base_ref(), bar_path): manifest_text("bar", "0.4.7"),
            },
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={
                "foo": (
                    ManifestRecord(
                        path=foo_path, content=manifest_text("foo", "0.4.1")
                    ),
                ),
                "bar": (
                    ManifestRecord(
                        path=bar_path, content=manifest_text("bar", "0.5.0")
                    ),
                ),
            },
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    return TwoPluginOutcome(
        already_bumped_plugin="bar",
        already_bumped_path=bar_path,
        unbumped_plugin="foo",
        unbumped_path=foo_path,
        outcome=run.capture(segment=None, mode=Mode.CHECK),
    )


def observe_new_skill_addition_run() -> tuple[str, BumpOutcome]:
    """Run auto-detected bump where a change adds a new skill file."""
    run = _single_manifest_run_for_changes("foo", changes=minor_change("foo"))
    return manifest_relpath("foo", CLAUDE_MANIFEST), run.capture(segment=None)


def observe_modification_only_changes_run() -> tuple[str, BumpOutcome]:
    """Run auto-detected bump where every change is a plain modification."""
    run = _single_manifest_run_for_changes("foo", changes=patch_changes("foo")["foo"])
    return manifest_relpath("foo", CLAUDE_MANIFEST), run.capture(segment=None)


def observe_explicit_segment_override_run() -> tuple[str, str, BumpOutcome]:
    """Force a patch segment over minor-triggering changes for one plugin."""
    plugin = "foo"
    run = _single_manifest_run_for_changes(plugin, changes=minor_change(plugin))
    return (
        plugin,
        manifest_relpath(plugin, CLAUDE_MANIFEST),
        run.capture(segment=Segment.PATCH),
    )


def observe_untracked_new_skill_changes() -> tuple[
    UntrackedSkillRepo, Mapping[str, tuple[ChangedPath, ...]]
]:
    """Build a real repo with an untracked new skill and probe its changes."""
    with TemporaryDirectory() as directory:
        handle = build_repo_with_untracked_new_skill(pathlib.Path(directory) / "repo")
        return handle, _real_change_probe(handle.base_ref, cwd=handle.repo)


def observe_renamed_structural_path_changes() -> tuple[
    RenamedStructuralRepo, Mapping[str, tuple[ChangedPath, ...]]
]:
    """Build a real repo with a structural rename and probe its changes."""
    with TemporaryDirectory() as directory:
        handle = build_repo_with_renamed_structural_path(
            pathlib.Path(directory) / "repo"
        )
        return handle, _real_change_probe(handle.base_ref, cwd=handle.repo)


def observe_cross_plugin_rename_changes() -> tuple[
    CrossPluginRenameRepo, Mapping[str, tuple[ChangedPath, ...]]
]:
    """Build a real repo with a cross-plugin structural rename and probe it."""
    with TemporaryDirectory() as directory:
        handle = build_repo_with_cross_plugin_structural_rename(
            pathlib.Path(directory) / "repo"
        )
        return handle, _real_change_probe(handle.base_ref, cwd=handle.repo)


def _observe_manifest_against_base_source_path(
    status: FileStatus,
) -> tuple[str, str, BumpOutcome]:
    src_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    base_path = src_path.removeprefix("src/")
    run = BumpRun(
        change_probe=ScriptedChangeProbe(
            changed={
                "foo": (ChangedPath(status=status, path=src_path, old_path=base_path),),
            },
        ),
        content_probe=ScriptedContentProbe(
            content={(base_ref(), base_path): manifest_text("foo", "0.4.1")},
        ),
        manifest_reader=ScriptedManifestReader(
            manifests={
                "foo": (
                    ManifestRecord(
                        path=src_path, content=manifest_text("foo", "0.5.0")
                    ),
                )
            },
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )
    outcome = run.capture(segment=None, mode=Mode.CHECK)
    return src_path, base_path, outcome


def _single_manifest_run_for_changes(
    plugin: str,
    *,
    changes: tuple[ChangedPath, ...],
) -> BumpRun:
    path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")
    return BumpRun(
        change_probe=ScriptedChangeProbe(changed={plugin: changes}),
        content_probe=ScriptedContentProbe(content={(base_ref(), path): content}),
        manifest_reader=ScriptedManifestReader(
            manifests={plugin: (ManifestRecord(path=path, content=content),)},
        ),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )


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
    untracked_codex_added_path: str


@dataclass(frozen=True)
class RenamedStructuralRepo:
    """A real git repo whose working tree renames a structural plugin path away."""

    repo: pathlib.Path
    base_ref: str
    plugin: str
    structural_path: str
    renamed_path: str


@dataclass(frozen=True)
class CrossPluginRenameRepo:
    """A real git repo whose working tree moves a structural path across plugins."""

    repo: pathlib.Path
    base_ref: str
    source_plugin: str
    target_plugin: str
    source_path: str
    target_path: str


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
    skill file without staging it (untracked), plus a generated Codex skill
    file under the same plugin. A ``git diff`` against the base sees only the
    modification; the untracked new skills are recoverable only through
    ``git ls-files --others``.
    """
    plugin = "demo"
    plugin_root = f"{SOURCE_PLUGINS_DIR}/{plugin}"
    codex_plugin_root = f"{DIST_CODEX_PLUGINS_DIR}/{plugin}"
    tracked_modified_path = f"{plugin_root}/skills/existing/SKILL.md"
    manifest_path = f"{plugin_root}/.claude-plugin/plugin.json"
    untracked_added_path = f"{plugin_root}/skills/new-skill/SKILL.md"
    untracked_codex_added_path = f"{codex_plugin_root}/skills/new-skill/SKILL.md"
    repo.mkdir(parents=True, exist_ok=True)
    _run_git(repo, "init", "-q", "-b", "main")
    _run_git(repo, "config", "commit.gpgsign", "false")
    _write(repo, manifest_path, '{\n  "name": "demo",\n  "version": "0.1.0"\n}\n')
    _write(repo, tracked_modified_path, "---\nname: existing\n---\n\nv1\n")
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "base")
    base_ref = "HEAD"

    (repo / tracked_modified_path).write_text(
        "---\nname: existing\n---\n\nv2\n", encoding="utf-8"
    )
    _write(repo, untracked_added_path, "---\nname: new-skill\n---\n\nnew\n")
    _write(repo, untracked_codex_added_path, "---\nname: new-skill\n---\n\nnew\n")

    return UntrackedSkillRepo(
        repo=repo,
        base_ref=base_ref,
        plugin=plugin,
        tracked_modified_path=tracked_modified_path,
        untracked_added_path=untracked_added_path,
        untracked_codex_added_path=untracked_codex_added_path,
    )


def build_repo_with_renamed_structural_path(
    repo: pathlib.Path,
) -> RenamedStructuralRepo:
    """Commit a structural plugin path, then rename it outside plugin roots."""
    plugin = "demo"
    plugin_root = f"{SOURCE_PLUGINS_DIR}/{plugin}"
    structural_path = f"{plugin_root}/skills/removed/SKILL.md"
    renamed_path = "archived/removed-skill.md"
    manifest_path = f"{plugin_root}/.claude-plugin/plugin.json"
    repo.mkdir(parents=True, exist_ok=True)
    _run_git(repo, "init", "-q", "-b", "main")
    _run_git(repo, "config", "commit.gpgsign", "false")
    _write(repo, manifest_path, '{\n  "name": "demo",\n  "version": "0.1.0"\n}\n')
    _write(repo, structural_path, "---\nname: removed\n---\n\nv1\n")
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "base")
    base_ref = "HEAD"

    (repo / renamed_path).parent.mkdir(parents=True, exist_ok=True)
    _run_git(repo, "mv", structural_path, renamed_path)

    return RenamedStructuralRepo(
        repo=repo,
        base_ref=base_ref,
        plugin=plugin,
        structural_path=structural_path,
        renamed_path=renamed_path,
    )


def build_repo_with_cross_plugin_structural_rename(
    repo: pathlib.Path,
) -> CrossPluginRenameRepo:
    """Commit one plugin's structural path, then move it under another plugin."""
    source_plugin = "source"
    target_plugin = "target"
    source_root = f"{SOURCE_PLUGINS_DIR}/{source_plugin}"
    target_root = f"{SOURCE_PLUGINS_DIR}/{target_plugin}"
    source_path = f"{source_root}/skills/moved/SKILL.md"
    target_path = f"{target_root}/skills/moved/SKILL.md"
    repo.mkdir(parents=True, exist_ok=True)
    _run_git(repo, "init", "-q", "-b", "main")
    _run_git(repo, "config", "commit.gpgsign", "false")
    _write(
        repo,
        f"{source_root}/.claude-plugin/plugin.json",
        '{\n  "name": "source",\n  "version": "0.1.0"\n}\n',
    )
    _write(
        repo,
        f"{target_root}/.claude-plugin/plugin.json",
        '{\n  "name": "target",\n  "version": "0.1.0"\n}\n',
    )
    _write(repo, source_path, "---\nname: moved\n---\n\nv1\n")
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-q", "-m", "base")
    base_ref = "HEAD"

    (repo / target_path).parent.mkdir(parents=True, exist_ok=True)
    _run_git(repo, "mv", source_path, target_path)

    return CrossPluginRenameRepo(
        repo=repo,
        base_ref=base_ref,
        source_plugin=source_plugin,
        target_plugin=target_plugin,
        source_path=source_path,
        target_path=target_path,
    )


def bump_property(test_func: Callable[..., None]) -> Callable[[], None]:
    configured = seed(BUMP_PROPERTY_SEED)(
        settings(max_examples=BUMP_PROPERTY_EXAMPLES)(test_func)
    )

    def wrapper() -> None:
        try:
            configured()
        except AssertionError as error:
            error.add_note(f"Hypothesis seed: {BUMP_PROPERTY_SEED}")
            error.add_note(f"Replay path: {BUMP_PROPERTY_REPLAY_PATH}")
            raise

    return wrapper


def observe_property_failure_notes() -> tuple[str, ...]:
    """Run a deliberately failing property and return its attached notes."""

    @bump_property
    @given(path=arbitrary_diff_paths())
    def always_fails(path: str) -> None:
        raise AssertionError(path)

    try:
        always_fails()
    except AssertionError as error:
        return tuple(getattr(error, "__notes__", ()))
    raise RuntimeError("the failing property completed without raising")


def run_distribution_path_property(check: Callable[[str, str, str], None]) -> None:
    """Drive `check` over generated distribution root, plugin, and subpath triples."""

    @bump_property
    @given(
        root=st.sampled_from(distribution_roots()),
        plugin=plugin_names(),
        subpath=relative_subpaths(),
    )
    def run(root: str, plugin: str, subpath: str) -> None:
        check(root, plugin, subpath)

    run()


def run_single_diff_path_property(check: Callable[[str], None]) -> None:
    """Drive `check` over one generated arbitrary diff path per example."""

    @bump_property
    @given(path=arbitrary_diff_paths())
    def run(path: str) -> None:
        check(path)

    run()


def run_diff_path_list_property(check: Callable[[list[str]], None]) -> None:
    """Drive `check` over generated lists of arbitrary diff paths."""

    @bump_property
    @given(paths=st.lists(arbitrary_diff_paths(), max_size=DIFF_PATH_LIST_MAX_SIZE))
    def run(paths: list[str]) -> None:
        check(paths)

    run()


__all__ = [
    "BUMP_PROPERTY_EXAMPLES",
    "BUMP_PROPERTY_REPLAY_PATH",
    "BUMP_PROPERTY_SEED",
    "BumpOutcome",
    "BumpRun",
    "CrossPluginRenameRepo",
    "DIFF_PATH_LIST_MAX_SIZE",
    "DualManifestCase",
    "DualManifestOutcome",
    "MissingToolOutcome",
    "RecordingManifestWriter",
    "RecordingToolProbe",
    "RenamedStructuralRepo",
    "ScriptedChangeProbe",
    "ScriptedContentProbe",
    "ScriptedManifestReader",
    "SingleManifestCase",
    "SingleManifestOutcome",
    "TOOL_EVENT_PREFIX",
    "TwoPluginOutcome",
    "UntrackedSkillRepo",
    "all_tools_available",
    "base_ref",
    "build_repo_with_cross_plugin_structural_rename",
    "build_repo_with_renamed_structural_path",
    "build_repo_with_untracked_new_skill",
    "bump_property",
    "dual_manifest_case",
    "observe_all_minor_triggering_changes_run",
    "observe_already_bumped_beside_unbumped_plugin",
    "observe_already_bumped_plugin",
    "observe_base_source_path_comparison",
    "observe_below_base_plugin",
    "observe_check_all_plugins_bumped",
    "observe_check_one_plugin_unbumped",
    "observe_check_unbumped_plugin",
    "observe_cli_dry_run_check_combination",
    "observe_cross_plugin_rename_changes",
    "observe_dry_run_report",
    "observe_dual_manifest_plugin",
    "observe_explicit_segment_override_run",
    "observe_fixture_manifest_rewrite",
    "observe_malformed_manifest_runs",
    "observe_missing_required_tool_runs",
    "observe_mixed_dual_manifest_plugin",
    "observe_modification_only_changes_run",
    "observe_new_plugin_without_base_manifest",
    "observe_new_skill_addition_run",
    "observe_no_changed_plugins_run",
    "observe_probe_ordering",
    "observe_property_failure_notes",
    "observe_read_only_mode_runs",
    "observe_renamed_structural_path_changes",
    "observe_segment_selection_runs",
    "observe_single_changed_plugin_run",
    "observe_unchanged_plugins_run",
    "observe_untracked_new_skill_changes",
    "run_diff_path_list_property",
    "run_distribution_path_property",
    "run_single_diff_path_property",
    "single_manifest_case",
]


_: type[ChangeProbe] = ScriptedChangeProbe
_2: type[ContentProbe] = ScriptedContentProbe
_3: type[ManifestReader] = ScriptedManifestReader
_4: type[ManifestWriter] = RecordingManifestWriter
_5: type[ToolProbe] = RecordingToolProbe
