"""Level-1 scenario evidence for `spx/32-distribution.enabler/21-bump.enabler/`.

Covers the scenario assertions in `bump.md`:

- Selective bump: a plugin with changes under a recognized
  distribution-surface root gets bumped; a plugin without changes does not.
- Lockstep dual manifests: a plugin owning both `.claude-plugin/plugin.json`
  and `.codex-plugin/plugin.json` writes the same new version to both.
- Segment selection: `patch` (default), `minor`, and `major` segment
  invocations produce the version values declared by the spec.
- No-change short-circuit: a base_ref with no changed plugins exits 0
  without invoking the manifest writer.

Behaviour is observed through recording doubles in
`outcomeeng_testing.harnesses.bump`. Manifest text and paths come from
`outcomeeng_testing.generators.bump`.
"""

from __future__ import annotations

import pathlib

import pytest

from outcomeeng.distribution.bump import (
    CLAUDE_MANIFEST,
    CODEX_MANIFEST,
    ChangedPath,
    FileStatus,
    ManifestRecord,
    Mode,
    Segment,
    _real_change_probe,
    bump,
)
from outcomeeng_testing.generators.bump import (
    manifest_relpath,
    manifest_text,
    minor_change,
    patch_changes,
    version_of,
)
from outcomeeng_testing.harnesses.bump import (
    RecordingManifestWriter,
    RecordingToolProbe,
    ScriptedChangeProbe,
    ScriptedContentProbe,
    ScriptedManifestReader,
    all_tools_available,
    base_ref,
    build_repo_with_untracked_new_skill,
)


def test_only_changed_plugin_manifests_are_written() -> None:
    foo_claude = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_claude = manifest_relpath("bar", CLAUDE_MANIFEST)
    foo_content = manifest_text("foo", "0.4.1")
    bar_content = manifest_text("bar", "0.4.1")

    change_probe = ScriptedChangeProbe(changed=patch_changes("foo"))
    content_probe = ScriptedContentProbe(
        content={
            (base_ref(), foo_claude): foo_content,
            (base_ref(), bar_claude): bar_content,
        },
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            "foo": (ManifestRecord(path=foo_claude, content=foo_content),),
            "bar": (ManifestRecord(path=bar_claude, content=bar_content),),
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written = dict(manifest_writer.writes)
    assert exit_code == 0
    assert list(written) == [foo_claude]
    assert version_of(written[foo_claude]) == "0.4.2"
    assert "bar" not in manifest_reader.queries


def test_dual_manifest_plugin_writes_both_with_same_new_version() -> None:
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    codex_path = manifest_relpath(plugin, CODEX_MANIFEST)
    claude_content = manifest_text(plugin, "0.4.1")
    codex_content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(
        content={
            (base_ref(), claude_path): claude_content,
            (base_ref(), codex_path): codex_content,
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
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
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
    # Asserting the exact post-bump value (not just equality) rejects the
    # mutant that wrote `0.4.1` to both manifests without bumping.
    assert written_versions == {"0.4.2"}


@pytest.mark.parametrize(
    ("segment", "old_version", "expected_version"),
    [
        (Segment.PATCH, "0.4.1", "0.4.2"),
        (Segment.MINOR, "0.4.1", "0.5.0"),
        (Segment.MAJOR, "0.4.1", "1.0.0"),
    ],
)
def test_segment_selection_produces_expected_version(
    segment: Segment,
    old_version: str,
    expected_version: str,
) -> None:
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    claude_content = manifest_text(plugin, old_version)

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(
        content={(base_ref(), claude_path): claude_content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=claude_path, content=claude_content),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        segment,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written = dict(manifest_writer.writes)
    assert exit_code == 0
    assert version_of(written[claude_path]) == expected_version


def test_no_changed_plugins_exits_zero_without_writing() -> None:
    change_probe = ScriptedChangeProbe(changed={})
    content_probe = ScriptedContentProbe(content={})
    manifest_reader = ScriptedManifestReader(manifests={})
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    assert exit_code == 0
    assert manifest_writer.writes == []
    assert manifest_reader.queries == []


def test_dry_run_reports_would_be_new_version_without_writing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(
        content={(base_ref(), claude_path): content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=claude_path, content=content),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
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
    # The would-be new version appears on stdout so a maintainer can preview.
    assert "0.4.2" in captured.out
    assert plugin in captured.out


def test_check_passes_when_every_changed_plugin_is_already_bumped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_path = manifest_relpath("bar", CLAUDE_MANIFEST)
    # Both plugins' WT versions are ahead of their base_ref versions.
    foo_wt = manifest_text("foo", "0.4.2")
    foo_base = manifest_text("foo", "0.4.1")
    bar_wt = manifest_text("bar", "0.5.0")
    bar_base = manifest_text("bar", "0.4.7")

    change_probe = ScriptedChangeProbe(changed=patch_changes("foo", "bar"))
    content_probe = ScriptedContentProbe(
        content={
            (base_ref(), foo_path): foo_base,
            (base_ref(), bar_path): bar_base,
        },
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            "foo": (ManifestRecord(path=foo_path, content=foo_wt),),
            "bar": (ManifestRecord(path=bar_path, content=bar_wt),),
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        mode=Mode.CHECK,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert manifest_writer.writes == []
    # No diagnostic when every changed plugin is already bumped.
    assert captured.err == ""


def test_write_bumps_from_base_when_working_tree_version_is_below_base() -> None:
    plugin = "foo"
    path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    working_tree_content = manifest_text(plugin, "0.72.4")
    base_content = manifest_text(plugin, "0.73.0")

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(content={(base_ref(), path): base_content})
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=path, content=working_tree_content),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        Segment.PATCH,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written = dict(manifest_writer.writes)
    assert exit_code == 0
    assert version_of(written[path]) == "0.73.1"


def test_check_fails_when_working_tree_version_is_below_base(
    capsys: pytest.CaptureFixture[str],
) -> None:
    plugin = "foo"
    path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    working_tree_content = manifest_text(plugin, "0.72.4")
    base_content = manifest_text(plugin, "0.73.0")

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(content={(base_ref(), path): base_content})
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=path, content=working_tree_content),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        mode=Mode.CHECK,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert manifest_writer.writes == []
    assert plugin in captured.err


def test_check_compares_added_manifest_to_base_source_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An added manifest compares against its recorded base source path."""
    plugin = "foo"
    src_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    base_path = src_path.removeprefix("src/")
    working_tree_content = manifest_text(plugin, "0.5.0")
    base_content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(
        changed={
            plugin: (
                ChangedPath(
                    status=FileStatus.ADDED,
                    path=src_path,
                    old_path=base_path,
                ),
            ),
        },
    )
    content_probe = ScriptedContentProbe(
        content={(base_ref(), base_path): base_content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            plugin: (ManifestRecord(path=src_path, content=working_tree_content),)
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        mode=Mode.CHECK,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert manifest_writer.writes == []
    assert captured.err == ""
    assert content_probe.queries == [(base_ref(), src_path), (base_ref(), base_path)]


def test_check_compares_copied_manifest_to_base_source_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A copied manifest compares against its recorded base source path."""
    plugin = "foo"
    src_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    base_path = src_path.removeprefix("src/")
    working_tree_content = manifest_text(plugin, "0.5.0")
    base_content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(
        changed={
            plugin: (
                ChangedPath(
                    status=FileStatus.COPIED,
                    path=src_path,
                    old_path=base_path,
                ),
            ),
        },
    )
    content_probe = ScriptedContentProbe(
        content={(base_ref(), base_path): base_content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            plugin: (ManifestRecord(path=src_path, content=working_tree_content),)
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        mode=Mode.CHECK,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert manifest_writer.writes == []
    assert captured.err == ""
    assert content_probe.queries == [(base_ref(), src_path), (base_ref(), base_path)]


def test_check_fails_when_any_changed_plugin_is_not_yet_bumped(
    capsys: pytest.CaptureFixture[str],
) -> None:
    foo_path = manifest_relpath("foo", CLAUDE_MANIFEST)
    bar_path = manifest_relpath("bar", CLAUDE_MANIFEST)
    # foo: clean (WT == base); bar: already bumped.
    foo_unchanged = manifest_text("foo", "0.4.1")
    bar_wt = manifest_text("bar", "0.5.0")
    bar_base = manifest_text("bar", "0.4.7")

    change_probe = ScriptedChangeProbe(changed=patch_changes("foo", "bar"))
    content_probe = ScriptedContentProbe(
        content={
            (base_ref(), foo_path): foo_unchanged,
            (base_ref(), bar_path): bar_base,
        },
    )
    manifest_reader = ScriptedManifestReader(
        manifests={
            "foo": (ManifestRecord(path=foo_path, content=foo_unchanged),),
            "bar": (ManifestRecord(path=bar_path, content=bar_wt),),
        },
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        Segment.PATCH,
        mode=Mode.CHECK,
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    assert manifest_writer.writes == []
    # Diagnostic names the unbumped plugin but not the already-bumped one.
    assert "foo" in captured.err
    assert "bar" not in captured.err


def test_auto_detected_segment_is_minor_for_new_skill_addition() -> None:
    """No explicit --segment + an ADDED SKILL.md → minor bump for that plugin."""
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(changed={plugin: minor_change(plugin)})
    content_probe = ScriptedContentProbe(
        content={(base_ref(), claude_path): content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=claude_path, content=content),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        segment=None,  # auto-detect
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written = dict(manifest_writer.writes)
    assert exit_code == 0
    # 0.4.1 + auto-detected minor → 0.5.0 (not 0.4.2 which would be patch).
    assert version_of(written[claude_path]) == "0.5.0"


def test_auto_detected_segment_is_patch_for_modification_only_changes() -> None:
    """No explicit --segment + only MODIFIED changes → patch bump."""
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(changed=patch_changes(plugin))
    content_probe = ScriptedContentProbe(
        content={(base_ref(), claude_path): content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=claude_path, content=content),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        segment=None,  # auto-detect
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    written = dict(manifest_writer.writes)
    assert exit_code == 0
    assert version_of(written[claude_path]) == "0.4.2"


def test_explicit_segment_patch_overrides_detected_minor_with_warning(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--segment patch` against an auto-detected `minor` writes patch
    and warns on stderr naming the plugin and the detected segment.
    """
    plugin = "foo"
    claude_path = manifest_relpath(plugin, CLAUDE_MANIFEST)
    content = manifest_text(plugin, "0.4.1")

    change_probe = ScriptedChangeProbe(changed={plugin: minor_change(plugin)})
    content_probe = ScriptedContentProbe(
        content={(base_ref(), claude_path): content},
    )
    manifest_reader = ScriptedManifestReader(
        manifests={plugin: (ManifestRecord(path=claude_path, content=content),)},
    )
    manifest_writer = RecordingManifestWriter()
    tool_probe = RecordingToolProbe(available=all_tools_available())

    exit_code = bump(
        base_ref(),
        Segment.PATCH,  # explicit override
        change_probe=change_probe,
        content_probe=content_probe,
        manifest_reader=manifest_reader,
        manifest_writer=manifest_writer,
        tool_probe=tool_probe,
    )

    captured = capsys.readouterr()
    written = dict(manifest_writer.writes)
    assert exit_code == 0
    # Explicit patch wins → 0.4.2 (not 0.5.0).
    assert version_of(written[claude_path]) == "0.4.2"
    # Warning surfaces the discrepancy on stderr.
    assert plugin in captured.err
    assert "minor" in captured.err


def test_real_change_probe_detects_untracked_new_skill_as_added(
    tmp_path: pathlib.Path,
) -> None:
    handle = build_repo_with_untracked_new_skill(tmp_path / "repo")

    changes = _real_change_probe(handle.base_ref, cwd=handle.repo)

    by_path = {change.path: change for change in changes.get(handle.plugin, ())}
    # The tracked modification is detected, as it always was...
    assert by_path[handle.tracked_modified_path].status is FileStatus.MODIFIED
    # ...and the untracked new skill is now detected, tagged Added, rather than
    # missed by the diff against the base.
    assert by_path[handle.untracked_added_path].status is FileStatus.ADDED
    assert by_path[handle.untracked_codex_added_path].status is FileStatus.ADDED
