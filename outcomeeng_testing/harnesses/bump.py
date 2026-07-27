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
    auto_segment,
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
    version_of,
)

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


def missing_required_tool_fails_fast_with_diagnostic() -> bool:
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
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = run.run()

        if not (
            exit_code != 0
            and run.manifest_writer.writes == []
            and run.change_probe.queries == []
            and run.manifest_reader.queries == []
            and missing_tool in (stderr.getvalue() + stdout.getvalue())
        ):
            return False
    return True


def tool_availability_is_probed_before_any_other_probe_or_write() -> bool:
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
    first_non_tool_index = next(
        (i for i, event in enumerate(event_log) if not event.startswith("tool:")),
        len(event_log),
    )
    early_tools = {
        event.removeprefix("tool:") for event in event_log[:first_non_tool_index]
    }
    return exit_code == 0 and early_tools >= set(REQUIRED_TOOLS)


def already_bumped_plugin_is_skipped_not_rewritten() -> bool:
    case = single_manifest_case("foo", version="0.4.2", base_version="0.4.1")
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = case.run.run()

    return (
        exit_code == 0
        and case.run.manifest_writer.writes == []
        and case.plugin in stderr.getvalue()
    )


def already_bumped_plugin_skipped_while_other_changed_plugin_is_bumped() -> bool:
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
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = run.run()

    written = run.written()
    return (
        exit_code == 0
        and foo_path not in written
        and bar_path in written
        and version_of(written[bar_path]) == "0.4.2"
        and "foo" in stderr.getvalue()
    )


def mixed_dual_manifest_plugin_aligns_lagging_manifest_to_current_bump() -> bool:
    case = dual_manifest_case(
        "foo",
        claude_version="0.4.2",
        codex_version="0.4.1",
        claude_base_version="0.4.1",
        codex_base_version="0.4.1",
    )

    with contextlib.redirect_stderr(io.StringIO()):
        exit_code = case.run.run()

    written = case.run.written()
    return (
        exit_code == 0
        and set(written) == {case.claude_path, case.codex_path}
        and version_of(written[case.claude_path]) == "0.4.2"
        and version_of(written[case.codex_path]) == "0.4.2"
    )


def mixed_dual_manifest_plugin_aligns_every_owned_manifest_to_current_max() -> bool:
    case = dual_manifest_case(
        "foo",
        claude_version="0.4.3",
        codex_version="0.4.1",
        claude_base_version="0.4.1",
        codex_base_version="0.4.1",
    )

    with contextlib.redirect_stderr(io.StringIO()):
        exit_code = case.run.run()

    written = case.run.written()
    return (
        exit_code == 0
        and set(written) == {case.claude_path, case.codex_path}
        and version_of(written[case.claude_path]) == "0.4.3"
        and version_of(written[case.codex_path]) == "0.4.3"
    )


def mixed_dual_manifest_plugin_fails_check() -> bool:
    case = dual_manifest_case(
        "foo",
        claude_version="0.4.2",
        codex_version="0.4.1",
        claude_base_version="0.4.1",
        codex_base_version="0.4.1",
    )
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = case.run.run(mode=Mode.CHECK)

    return (
        exit_code == 1
        and case.run.manifest_writer.writes == []
        and case.plugin in stderr.getvalue()
        and "out of lockstep" in stderr.getvalue()
    )


def new_plugin_without_base_manifest_passes_check() -> bool:
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
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = run.run(segment=None, mode=Mode.CHECK)

    return (
        exit_code == 0 and run.manifest_writer.writes == [] and stderr.getvalue() == ""
    )


def already_bumped_plugin_skipped_in_dry_run() -> bool:
    case = single_manifest_case("foo", version="0.4.2", base_version="0.4.1")
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = case.run.run(mode=Mode.DRY_RUN)

    return (
        exit_code == 0
        and case.run.manifest_writer.writes == []
        and case.plugin in stderr.getvalue()
    )


def dry_run_skips_already_bumped_plugin_and_reports_the_other() -> bool:
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
    stdout = io.StringIO()
    stderr = io.StringIO()

    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = run.run(mode=Mode.DRY_RUN)

    return (
        exit_code == 0
        and run.manifest_writer.writes == []
        and "bar" in stdout.getvalue()
        and "0.4.1 -> 0.4.2" in stdout.getvalue()
        and "foo" in stderr.getvalue()
    )


def unchanged_plugins_never_have_manifests_written() -> bool:
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

    exit_code = run.run()
    written_paths = [path for path, _ in run.manifest_writer.writes]
    return (
        exit_code == 0
        and written_paths == [foo_path]
        and run.manifest_reader.queries == ["foo"]
    )


def dual_manifest_plugin_writes_every_owned_manifest() -> bool:
    return dual_manifest_plugin_writes_both_with_same_new_version()


def non_version_content_is_preserved_character_for_character() -> bool:
    plugin = "fixture-plugin"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    original = manifest_fixture_path("representative_plugin.json").read_text()
    old_version = version_of(original)
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

    exit_code = run.run()
    written = run.written()
    new_content = written[claude_path]
    new_version = version_of(new_content)
    expected = original.replace(
        f'"version": "{old_version}"',
        f'"version": "{new_version}"',
        1,
    )
    return exit_code == 0 and new_content == expected


def read_only_modes_never_write_regardless_of_plugin_state() -> bool:
    for mode in (Mode.DRY_RUN, Mode.CHECK):
        for wt_version, base_version in (("0.4.1", "0.4.1"), ("0.4.2", "0.4.1")):
            case = single_manifest_case(
                "foo", version=wt_version, base_version=base_version
            )
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                case.run.run(mode=mode)
            if case.run.manifest_writer.writes != []:
                return False
    return True


def unparseable_manifest_returns_diagnostic_without_writes() -> bool:
    plugin = "foo"
    path = manifest_relpath(plugin, CLAUDE_MANIFEST)
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
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            exit_code = run.run()

        output = stderr.getvalue()
        if (
            exit_code != 1
            or run.manifest_writer.writes != []
            or path not in output
            or case.expected_diagnostic not in output
        ):
            return False
    return True


def dry_run_and_check_are_mutually_exclusive_at_the_cli_boundary() -> bool:
    stderr = io.StringIO()

    try:
        with contextlib.redirect_stderr(stderr):
            main(["--dry-run", "--check"])
    except SystemExit as exc:
        return exc.code != 0 and "not allowed with" in stderr.getvalue()
    return False


def auto_detection_never_writes_a_major_bump_through_the_orchestrator() -> bool:
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

    exit_code = run.run(segment=None)
    return exit_code == 0 and version_of(run.written()[claude_path]) == "0.5.0"


def only_changed_plugin_manifests_are_written() -> bool:
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

    exit_code = run.run()
    written = run.written()
    return (
        exit_code == 0
        and list(written) == [foo_claude]
        and version_of(written[foo_claude]) == "0.4.2"
        and "bar" not in run.manifest_reader.queries
    )


def dual_manifest_plugin_writes_both_with_same_new_version() -> bool:
    case = dual_manifest_case("foo", claude_version="0.4.1", codex_version="0.4.1")

    exit_code = case.run.run()
    written = case.run.written()
    written_versions = {version_of(content) for content in written.values()}
    return (
        exit_code == 0
        and set(written) == {case.claude_path, case.codex_path}
        and written_versions == {"0.4.2"}
    )


def mixed_dual_manifest_minor_change_uses_current_segment() -> bool:
    case = dual_manifest_case(
        "foo",
        claude_version="0.4.2",
        codex_version="0.4.1",
        claude_base_version="0.4.1",
        codex_base_version="0.4.1",
    )

    with contextlib.redirect_stderr(io.StringIO()):
        exit_code = case.run.run(segment=Segment.MINOR)
    written = case.run.written()
    return (
        exit_code == 0
        and set(written) == {case.claude_path, case.codex_path}
        and version_of(written[case.claude_path]) == "0.5.0"
        and version_of(written[case.codex_path]) == "0.5.0"
    )


def segment_selection_produces_expected_versions() -> bool:
    expected_by_segment = {
        Segment.PATCH: "0.4.2",
        Segment.MINOR: "0.5.0",
        Segment.MAJOR: "1.0.0",
    }
    for segment, expected_version in expected_by_segment.items():
        case = single_manifest_case("foo", version="0.4.1")
        exit_code = case.run.run(segment=segment)
        if (
            exit_code != 0
            or version_of(case.run.written()[case.path]) != expected_version
        ):
            return False
    return True


def no_changed_plugins_exits_zero_without_writing() -> bool:
    run = BumpRun(
        change_probe=ScriptedChangeProbe(changed={}),
        content_probe=ScriptedContentProbe(content={}),
        manifest_reader=ScriptedManifestReader(manifests={}),
        manifest_writer=RecordingManifestWriter(),
        tool_probe=RecordingToolProbe(available=all_tools_available()),
    )

    return (
        run.run() == 0
        and run.manifest_writer.writes == []
        and run.manifest_reader.queries == []
    )


def dry_run_reports_would_be_new_version_without_writing() -> bool:
    case = single_manifest_case("foo", version="0.4.1")
    stdout = io.StringIO()

    with contextlib.redirect_stdout(stdout):
        exit_code = case.run.run(mode=Mode.DRY_RUN)

    output = stdout.getvalue()
    return (
        exit_code == 0
        and case.run.manifest_writer.writes == []
        and "0.4.2" in output
        and case.plugin in output
    )


def check_passes_when_every_changed_plugin_is_already_bumped() -> bool:
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
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = run.run(segment=None, mode=Mode.CHECK)

    return (
        exit_code == 0 and run.manifest_writer.writes == [] and stderr.getvalue() == ""
    )


def write_bumps_from_base_when_working_tree_version_is_below_base() -> bool:
    case = single_manifest_case("foo", version="0.72.4", base_version="0.73.0")
    exit_code = case.run.run()
    return exit_code == 0 and version_of(case.run.written()[case.path]) == "0.73.1"


def check_fails_when_working_tree_version_is_below_base() -> bool:
    case = single_manifest_case("foo", version="0.72.4", base_version="0.73.0")
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = case.run.run(mode=Mode.CHECK)

    return (
        exit_code == 1
        and case.run.manifest_writer.writes == []
        and case.plugin in stderr.getvalue()
    )


def check_compares_added_manifest_to_base_source_path() -> bool:
    return _check_compares_manifest_to_base_source_path(FileStatus.ADDED)


def check_compares_copied_manifest_to_base_source_path() -> bool:
    return _check_compares_manifest_to_base_source_path(FileStatus.COPIED)


def check_fails_when_changed_plugin_is_not_yet_bumped() -> bool:
    case = single_manifest_case("foo", version="0.4.1")
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = case.run.run(mode=Mode.CHECK)

    return (
        exit_code != 0
        and case.run.manifest_writer.writes == []
        and case.plugin in stderr.getvalue()
    )


def check_fails_when_any_changed_plugin_is_not_yet_bumped() -> bool:
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
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = run.run(segment=None, mode=Mode.CHECK)

    output = stderr.getvalue()
    return (
        exit_code != 0
        and run.manifest_writer.writes == []
        and "foo" in output
        and "bar" not in output
    )


def auto_detected_segment_is_minor_for_new_skill_addition() -> bool:
    run = _single_manifest_run_for_changes("foo", changes=minor_change("foo"))

    exit_code = run.run(segment=None)

    return (
        exit_code == 0
        and version_of(run.written()[manifest_relpath("foo", CLAUDE_MANIFEST)])
        == "0.5.0"
    )


def auto_detected_segment_is_patch_for_modification_only_changes() -> bool:
    run = _single_manifest_run_for_changes("foo", changes=patch_changes("foo")["foo"])

    exit_code = run.run(segment=None)

    return (
        exit_code == 0
        and version_of(run.written()[manifest_relpath("foo", CLAUDE_MANIFEST)])
        == "0.4.2"
    )


def explicit_segment_patch_overrides_detected_minor_with_warning() -> bool:
    run = _single_manifest_run_for_changes("foo", changes=minor_change("foo"))
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = run.run(segment=Segment.PATCH)

    output = stderr.getvalue()
    return (
        exit_code == 0
        and version_of(run.written()[manifest_relpath("foo", CLAUDE_MANIFEST)])
        == "0.4.2"
        and "foo" in output
        and "minor" in output
    )


def real_change_probe_detects_untracked_new_skill_as_added() -> bool:
    with TemporaryDirectory() as directory:
        return _real_change_probe_detects_untracked_new_skill_as_added(
            pathlib.Path(directory) / "repo"
        )


def _real_change_probe_detects_untracked_new_skill_as_added(
    repo: pathlib.Path,
) -> bool:
    handle = build_repo_with_untracked_new_skill(repo)

    changes = _real_change_probe(handle.base_ref, cwd=handle.repo)
    by_path = {change.path: change for change in changes.get(handle.plugin, ())}
    return (
        by_path[handle.tracked_modified_path].status is FileStatus.MODIFIED
        and by_path[handle.untracked_added_path].status is FileStatus.ADDED
        and by_path[handle.untracked_codex_added_path].status is FileStatus.ADDED
    )


def real_change_probe_detects_rename_away_from_structural_path() -> bool:
    with TemporaryDirectory() as directory:
        return _real_change_probe_detects_rename_away_from_structural_path(
            pathlib.Path(directory) / "repo"
        )


def _real_change_probe_detects_rename_away_from_structural_path(
    repo: pathlib.Path,
) -> bool:
    handle = build_repo_with_renamed_structural_path(repo)

    changes = _real_change_probe(handle.base_ref, cwd=handle.repo)
    by_path = {change.path: change for change in changes.get(handle.plugin, ())}
    change = by_path.get(handle.renamed_path)
    return (
        change is not None
        and change.status is FileStatus.RENAMED
        and change.old_path == handle.structural_path
        and auto_segment(changes[handle.plugin]) is Segment.MINOR
    )


def real_change_probe_detects_cross_plugin_structural_rename() -> bool:
    with TemporaryDirectory() as directory:
        return _real_change_probe_detects_cross_plugin_structural_rename(
            pathlib.Path(directory) / "repo"
        )


def _real_change_probe_detects_cross_plugin_structural_rename(
    repo: pathlib.Path,
) -> bool:
    handle = build_repo_with_cross_plugin_structural_rename(repo)

    changes = _real_change_probe(handle.base_ref, cwd=handle.repo)
    source_changes = {change.path: change for change in changes[handle.source_plugin]}
    target_changes = {change.path: change for change in changes[handle.target_plugin]}
    return (
        source_changes.keys() == target_changes.keys() == {handle.target_path}
        and source_changes[handle.target_path].old_path == handle.source_path
        and target_changes[handle.target_path].old_path == handle.source_path
        and auto_segment(changes[handle.source_plugin]) is Segment.MINOR
        and auto_segment(changes[handle.target_plugin]) is Segment.MINOR
    )


def _check_compares_manifest_to_base_source_path(status: FileStatus) -> bool:
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
    stderr = io.StringIO()

    with contextlib.redirect_stderr(stderr):
        exit_code = run.run(segment=None, mode=Mode.CHECK)

    return (
        exit_code == 0
        and run.manifest_writer.writes == []
        and stderr.getvalue() == ""
        and run.content_probe.queries
        == [(base_ref(), src_path), (base_ref(), base_path)]
    )


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
    "CrossPluginRenameRepo",
    "RecordingManifestWriter",
    "RecordingToolProbe",
    "ScriptedChangeProbe",
    "ScriptedContentProbe",
    "ScriptedManifestReader",
    "RenamedStructuralRepo",
    "SingleManifestCase",
    "UntrackedSkillRepo",
    "all_tools_available",
    "base_ref",
    "observe_property_failure_notes",
    "build_repo_with_cross_plugin_structural_rename",
    "build_repo_with_renamed_structural_path",
    "build_repo_with_untracked_new_skill",
    "run_distribution_path_property",
    "run_diff_path_list_property",
    "run_single_diff_path_property",
    "new_plugin_without_base_manifest_passes_check",
    "real_change_probe_detects_cross_plugin_structural_rename",
    "real_change_probe_detects_rename_away_from_structural_path",
    "single_manifest_case",
]


_: type[ChangeProbe] = ScriptedChangeProbe
_2: type[ContentProbe] = ScriptedContentProbe
_3: type[ManifestReader] = ScriptedManifestReader
_4: type[ManifestWriter] = RecordingManifestWriter
_5: type[ToolProbe] = RecordingToolProbe
