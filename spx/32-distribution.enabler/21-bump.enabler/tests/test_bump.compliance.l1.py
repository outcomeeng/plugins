"""Level-1 compliance evidence for `spx/32-distribution.enabler/21-bump.enabler/`.

Covers the compliance assertions in `bump.md` whose evidence is
scenario-shaped (specific behaviours, ordering, or fixture-based
preservation):

- ALWAYS: every manifest a changed plugin owns is written in the same
  bump pass — both manifests receive the same new version in one
  invocation.
- ALWAYS: check availability of `git` before any orchestration step —
  the `tool_probe` records its calls into the shared `event_log` before
  any other probe records into it.
- NEVER: bump a plugin whose working-tree version differs from its
  base_ref version — that plugin is skipped with a diagnostic naming
  it, while every other changed-but-unbumped plugin is still bumped in
  the same pass.
- NEVER: write a manifest for a plugin with no changes since base_ref —
  unchanged plugins are not queried or written.
- NEVER: reformat manifest content beyond the version field — exercised
  against a real-shaped inert manifest fixture.
- NEVER: write any manifest when `--dry-run` or `--check` is selected —
  parametrized over both modes and both plugin states (clean vs already
  bumped).
- NEVER: combine `--dry-run` with `--check` — argparse rejects the
  combined flags at the CLI boundary before `bump()` is invoked.

The path-prefix allow-list ALWAYS is universally quantified and lives
in `test_bump.property.l1.py` as Hypothesis-based property evidence.

Behaviour is observed through recording doubles in
`outcomeeng_testing.harnesses.bump`. Manifest text and paths come from
`outcomeeng_testing.generators.bump`.
"""

from __future__ import annotations

import pytest

from outcomeeng.distribution.bump import (
    CLAUDE_MANIFEST,
    CODEX_MANIFEST,
    REQUIRED_TOOLS,
    ChangedPath,
    FileStatus,
    ManifestRecord,
    Mode,
    Segment,
    bump,
    main,
)
from outcomeeng_testing.generators.bump import (
    manifest_fixture_path,
    manifest_relpath,
    manifest_text,
    patch_changes,
    version_of,
)
from outcomeeng_testing.harnesses.bump import (
    RecordingManifestWriter,
    RecordingToolProbe,
    ScriptedChangeProbe,
    ScriptedContentProbe,
    ScriptedManifestReader,
)

BASE_REF = "origin/main"
ALL_TOOLS_AVAILABLE = frozenset(REQUIRED_TOOLS)


@pytest.mark.parametrize("missing_tool", REQUIRED_TOOLS)
def test_missing_required_tool_fails_fast_with_diagnostic(
    missing_tool: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    change_probe = ScriptedChangeProbe(changed=patch_changes("foo"))
    content_probe = ScriptedContentProbe(content={})
    manifest_reader = ScriptedManifestReader(manifests={})
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE - {missing_tool})

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert manifest_writer.writes == []
    assert change_probe.queries == []
    assert manifest_reader.queries == []
    assert missing_tool in (captured.err + captured.out)


def test_tool_availability_is_probed_before_any_other_probe_or_write() -> None:
    """A shared event log proves tool-probe calls precede any other call.

    The `event_log` records every Protocol invocation in invocation order
    across all doubles. The first events must be `tool:*` for every
    required tool; only after that may any `change:*`, `content:*`,
    `reader:*`, or `writer:*` event appear.
    """
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")

    event_log: list[str] = []
    change_probe = ScriptedChangeProbe(
        changed=patch_changes(plugin), event_log=event_log
    )
    content_probe = ScriptedContentProbe(
        content={(BASE_REF, claude_path): content}, event_log=event_log
    )
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=claude_path, content=content),)},
        event_log=event_log,
    )
    manifest_writer = RecordingManifestWriter(event_log=event_log)
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE, event_log=event_log)

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    assert exit_code == 0
    # Every event before the first non-tool event must be a `tool:*` event.
    first_non_tool_index = next(
        (i for i, ev in enumerate(event_log) if not ev.startswith("tool:")),
        len(event_log),
    )
    early_events = event_log[:first_non_tool_index]
    early_tools = {ev.removeprefix("tool:") for ev in early_events}
    assert early_tools >= set(REQUIRED_TOOLS), (
        f"every required tool must be probed before any other call, "
        f"but event_log = {event_log!r}"
    )


def test_already_bumped_plugin_is_skipped_not_rewritten(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A changed plugin already bumped on this branch is skipped, not re-bumped.

    Its working-tree version already differs from base_ref, so bump leaves the
    manifest untouched and names the skip in a diagnostic. With no other changed
    plugin to bump, the run still succeeds (idempotent re-run).
    """
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    working_tree_content = manifest_text(plugin, "0.4.2")
    base_ref_content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(
        content={(BASE_REF, claude_path): base_ref_content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            plugin: (ManifestRecord(path=claude_path, content=working_tree_content),)
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert manifest_writer.writes == []
    assert plugin in captured.err


def test_already_bumped_plugin_skipped_while_other_changed_plugin_is_bumped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per-plugin refusal: an already-bumped plugin is skipped while every other
    changed-but-unbumped plugin is still bumped in the same pass.

    `foo` is already ahead of base_ref (skipped); `bar` is changed but still at
    its base_ref version (bumped to 0.4.2). The run succeeds.
    """
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_path = manifest_relpath("bar", CLAUDE_MANIFEST)
    foo_wt = manifest_text("foo", "0.4.2")
    foo_base = manifest_text("foo", "0.4.1")
    bar_wt = manifest_text("bar", "0.4.1")
    bar_base = manifest_text("bar", "0.4.1")

    change_probe = ScriptedChangeProbe(changed=patch_changes("foo", "bar"))
    content_probe = ScriptedContentProbe(
        content={
            (BASE_REF, foo_path): foo_base,
            (BASE_REF, bar_path): bar_base,
        },
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            "foo": (ManifestRecord(path=foo_path, content=foo_wt),),
            "bar": (ManifestRecord(path=bar_path, content=bar_wt),),
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    written = dict(manifest_writer.writes)
    # foo is already bumped → skipped (not rewritten).
    assert foo_path not in written
    # bar is changed but unbumped → bumped to 0.4.2 in the same pass.
    assert bar_path in written
    assert '"version": "0.4.2"' in written[bar_path]
    assert "foo" in captured.err


def test_already_bumped_plugin_skipped_in_dry_run(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DRY_RUN also skips an already-bumped plugin with a diagnostic, writing nothing."""
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(
        content={(BASE_REF, claude_path): manifest_text(plugin, "0.4.1")},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            plugin: (
                ManifestRecord(
                    path=claude_path, content=manifest_text(plugin, "0.4.2")
                ),
            )
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        mode=Mode.DRY_RUN,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert manifest_writer.writes == []
    assert plugin in captured.err


def test_dry_run_skips_already_bumped_plugin_and_reports_the_other(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DRY_RUN, two plugins: the already-bumped plugin is skipped with a stderr
    diagnostic, the changed-but-unbumped plugin's would-be bump is reported on
    stdout, and nothing is written.
    """
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_path = manifest_relpath("bar", CLAUDE_MANIFEST)

    change_probe = ScriptedChangeProbe(changed=patch_changes("foo", "bar"))
    content_probe = ScriptedContentProbe(
        content={
            (BASE_REF, foo_path): manifest_text("foo", "0.4.1"),
            (BASE_REF, bar_path): manifest_text("bar", "0.4.1"),
        },
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            "foo": (
                ManifestRecord(path=foo_path, content=manifest_text("foo", "0.4.2")),
            ),
            "bar": (
                ManifestRecord(path=bar_path, content=manifest_text("bar", "0.4.1")),
            ),
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        mode=Mode.DRY_RUN,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert manifest_writer.writes == []
    # bar's would-be bump is reported on stdout; foo is skipped via stderr.
    assert "bar" in captured.out
    assert "0.4.1 -> 0.4.2" in captured.out
    assert "foo" in captured.err


def test_unchanged_plugins_never_have_manifests_written() -> None:
    """Plugins outside the ChangeProbe's returned set are never written."""
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    foo_content = manifest_text("foo", "0.4.1")

    change_probe = ScriptedChangeProbe(changed=patch_changes("foo"))
    content_probe = ScriptedContentProbe(
        content={(BASE_REF, foo_path): foo_content},
    )
    # `bar` and `baz` exist in the reader's domain but are not in the
    # change set; they must not be queried or written.
    manifest_reader = ScriptedManifestReader(
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
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written_paths = [path for path, _ in manifest_writer.writes]
    assert exit_code == 0
    assert written_paths == [foo_path]
    assert manifest_reader.queries == ["foo"]


def test_dual_manifest_plugin_writes_every_owned_manifest() -> None:
    """Both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`
    receive the same new version in one bump pass when a plugin owns both.
    """
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    codex_path = manifest_relpath(plugin, CODEX_MANIFEST)
    claude_content = manifest_text(plugin, "0.4.1")
    codex_content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(
        content={
            (BASE_REF, claude_path): claude_content,
            (BASE_REF, codex_path): codex_content,
        },
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            plugin: (
                ManifestRecord(path=claude_path, content=claude_content),
                ManifestRecord(path=codex_path, content=codex_content),
            ),
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written = dict(manifest_writer.writes)
    written_versions = {version_of(content) for content in written.values()}
    assert exit_code == 0
    assert set(written) == {claude_path, codex_path}
    # Asserting the exact post-bump value (not just equality across writes)
    # rejects the mutant that wrote `0.4.1` to both manifests without bumping.
    assert written_versions == {"0.4.2"}


def test_non_version_content_is_preserved_character_for_character() -> None:
    """The NEVER-reformat rule, exercised against a real-shaped manifest fixture.

    The fixture under `outcomeeng_testing/fixtures/bump/` carries the
    formatting choices real plugin manifests in this repo make: compact
    single-line arrays, mixed-case description prose mentioning the
    version string inline, nested author object, trailing newline.

    The independent oracle for "only the version field changed" is the
    same property restated as a string operation on the original payload:
    `original.replace('"version": "<old>"', '"version": "<new>"', 1)`.
    The bump output must equal that string byte-for-byte. This rejects
    any implementation that round-trips through `json.loads`/`json.dumps`
    (which would reflow the compact arrays) and any implementation that
    edits other fields incidentally.
    """
    plugin = "fixture-plugin"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    original = manifest_fixture_path("representative_plugin.json").read_text()
    old_version = version_of(original)

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(
        content={(BASE_REF, claude_path): original},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=claude_path, content=original),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

    exit_code = bump(
        BASE_REF,
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written = dict(manifest_writer.writes)
    assert exit_code == 0
    new_content = written[claude_path]
    new_version = version_of(new_content)
    # The independent oracle: substituting the single `"version": "<old>"`
    # literal in the original payload must reproduce the bump output exactly.
    expected = original.replace(
        f'"version": "{old_version}"',
        f'"version": "{new_version}"',
        1,
    )
    assert new_content == expected


@pytest.mark.parametrize("mode", [Mode.DRY_RUN, Mode.CHECK])
def test_read_only_modes_never_write_regardless_of_plugin_state(
    mode: Mode,
) -> None:
    """Neither `--dry-run` nor `--check` ever calls the manifest writer,
    no matter whether the changed plugin is clean (WT == base) or already
    bumped (WT != base). Exercises both states across both modes.
    """
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)

    for wt_version, base_version in [("0.4.1", "0.4.1"), ("0.4.2", "0.4.1")]:
        change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
        content_probe = ScriptedContentProbe(
            content={(BASE_REF, claude_path): manifest_text(plugin, base_version)},
        )
        manifest_reader = ScriptedManifestReader(
            manifests={
                plugin: (
                    ManifestRecord(
                        path=claude_path,
                        content=manifest_text(plugin, wt_version),
                    ),
                ),
            },
        )
        manifest_writer = RecordingManifestWriter()
        tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

        bump(
            BASE_REF,
            Segment.PATCH,
            mode=mode,
            change_probe=change_probe,
            content_probe=content_probe,
            manifest_reader=manifest_reader,
            manifest_writer=manifest_writer,
            tool_probe=tool_probe,
        )

        assert manifest_writer.writes == [], (
            f"writer called in {mode} mode with WT={wt_version}, base={base_version}"
        )


def test_dry_run_and_check_are_mutually_exclusive_at_the_cli_boundary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`main(["--dry-run", "--check"])` exits non-zero with an argparse
    diagnostic — the mutual exclusion is enforced at the parser before
    `bump()` is called.
    """
    with pytest.raises(SystemExit) as excinfo:
        main(["--dry-run", "--check"])

    captured = capsys.readouterr()
    assert excinfo.value.code != 0
    assert "not allowed with" in captured.err


def test_auto_detection_never_writes_a_major_bump_through_the_orchestrator() -> None:
    """End-to-end NEVER rule: even when changes include every minor-triggering
    pattern, auto-detection (segment=None) writes at most a `minor` bump.
    Major requires explicit `--segment major`.

    Mutants this kills: an `auto_segment` that returns `Segment.MAJOR` on
    any input, or a `bump()` that interprets None-segment as MAJOR.
    """
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")

    # Throw the kitchen sink of minor-triggering patterns at it.
    changes = (
        ChangedPath(FileStatus.ADDED, f"src/plugins/{plugin}/skills/new/SKILL.md"),
        ChangedPath(FileStatus.ADDED, f"src/plugins/{plugin}/commands/new-command.md"),
        ChangedPath(FileStatus.ADDED, f"src/plugins/{plugin}/agents/new-agent.md"),
        ChangedPath(
            FileStatus.ADDED, f"src/plugins/{plugin}/.codex-plugin/plugin.json"
        ),
    )

    change_probe = ScriptedChangeProbe(changed={plugin: changes})
    content_probe = ScriptedContentProbe(
        content={(BASE_REF, claude_path): content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=claude_path, content=content),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=ALL_TOOLS_AVAILABLE)

    exit_code = bump(
        BASE_REF,
        segment=None,  # auto-detect
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written = dict(manifest_writer.writes)
    assert exit_code == 0
    new_version = version_of(written[claude_path])
    # Minor (0.5.0), never major (1.0.0), even with every minor-triggering pattern present.
    assert new_version == "0.5.0"
