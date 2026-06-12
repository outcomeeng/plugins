"""Level 1 installation scenarios for validate_install's feature-branch lag tolerance.

When a working-tree plugin manifest bumps to a new version on a feature branch but
the Codex marketplace clone (which tracks the marketplace's published branch) is
still on the prior version, the new version directory is absent from the Codex
cache by design. validate_install demotes that absence to a warning rather than
treating it as a hard error.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from outcomeeng.validation import install as validate_install

MARKETPLACE_NAME = "outcomeeng"
PLUGIN_NAME = "demo-plugin"
ORPHAN_PLUGIN_NAME = "removed-plugin"
WORKING_TREE_VERSION = "0.2.0"
PUBLISHED_VERSION = "0.1.0"


def _write_manifest(repo_root: Path, plugin: str, version: str) -> None:
    manifest = repo_root / "src" / "plugins" / plugin / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"name": plugin, "version": version}))


def _seed_cache(cache_root: Path, plugin: str, version: str) -> None:
    plugin_dir = cache_root / MARKETPLACE_NAME / plugin / version
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "marker.txt").write_text("seed")


def test_lagging_codex_marketplace_version_emits_warning_not_error(
    tmp_path: Path,
) -> None:
    """When the Codex marketplace clone publishes an older version than the working tree,
    the missing newer-version directory is reported as a warning that names the plugin
    and both versions; the validation result records zero errors."""
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    _write_manifest(repo_root, PLUGIN_NAME, WORKING_TREE_VERSION)
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)

    def published_version(plugin: str) -> str | None:
        return PUBLISHED_VERSION if plugin == PLUGIN_NAME else None

    result = validate_install.validate(
        MARKETPLACE_NAME,
        repo_root=repo_root,
        codex_cache_override=codex_cache,
        claude_cache_override=tmp_path / "empty_claude_cache",
        codex_marketplace_version=published_version,
    )

    assert result.errors == [], f"unexpected errors: {result.errors}"
    assert len(result.warnings) == 1, (
        f"expected one warning, got {len(result.warnings)}: {result.warnings}"
    )
    warning = result.warnings[0]
    assert PLUGIN_NAME in warning
    assert WORKING_TREE_VERSION in warning
    assert PUBLISHED_VERSION in warning


def test_codex_cache_missing_published_version_is_an_error(tmp_path: Path) -> None:
    """When the working-tree and marketplace-published versions agree yet the
    Codex cache lacks that version, the missing directory is an error — the
    ahead-only tolerance does not cover an in-sync version with an incomplete cache."""
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    _write_manifest(repo_root, PLUGIN_NAME, PUBLISHED_VERSION)
    _seed_cache(codex_cache, PLUGIN_NAME, "0.0.1")

    def published_version(plugin: str) -> str | None:
        return PUBLISHED_VERSION if plugin == PLUGIN_NAME else None

    result = validate_install.validate(
        MARKETPLACE_NAME,
        repo_root=repo_root,
        codex_cache_override=codex_cache,
        claude_cache_override=tmp_path / "empty_claude_cache",
        codex_marketplace_version=published_version,
    )

    assert result.warnings == [], f"unexpected warnings: {result.warnings}"
    assert len(result.errors) == 1
    assert PUBLISHED_VERSION in result.errors[0]


def test_missing_codex_marketplace_manifest_falls_back_to_strict_check(
    tmp_path: Path,
) -> None:
    """When the Codex marketplace clone has no manifest for the plugin (the lookup
    returns None), validate_install applies strict validation against the working-tree
    version — no warning, and a missing directory is an error."""
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    _write_manifest(repo_root, PLUGIN_NAME, WORKING_TREE_VERSION)
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)

    def no_published_version(plugin: str) -> str | None:
        return None

    result = validate_install.validate(
        MARKETPLACE_NAME,
        repo_root=repo_root,
        codex_cache_override=codex_cache,
        claude_cache_override=tmp_path / "empty_claude_cache",
        codex_marketplace_version=no_published_version,
    )

    assert result.warnings == [], f"unexpected warnings: {result.warnings}"
    assert len(result.errors) == 1
    assert WORKING_TREE_VERSION in result.errors[0]


def test_main_exits_zero_when_working_tree_ahead_of_marketplace_clone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """End-to-end through main(): when the working tree advances past the marketplace
    clone, the script exits zero and writes a warning to stderr naming the plugin and
    both versions."""
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    _write_manifest(repo, PLUGIN_NAME, WORKING_TREE_VERSION)
    codex_cache = home / ".codex" / "plugins" / "cache"
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)

    clone_manifest = (
        home
        / ".codex"
        / ".tmp"
        / "marketplaces"
        / MARKETPLACE_NAME
        / "dist"
        / "claude"
        / PLUGIN_NAME
        / ".claude-plugin"
        / "plugin.json"
    )
    clone_manifest.parent.mkdir(parents=True)
    clone_manifest.write_text(
        json.dumps({"name": PLUGIN_NAME, "version": PUBLISHED_VERSION})
    )

    exit_code = validate_install.main([MARKETPLACE_NAME])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert PLUGIN_NAME in captured.err
    assert WORKING_TREE_VERSION in captured.err
    assert PUBLISHED_VERSION in captured.err
    assert "warning:" in captured.err


def test_main_reads_legacy_plugins_marketplace_clone_during_layout_migration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When the installed Codex marketplace clone is still on the pre-dist layout,
    validate_install reads `plugins/<plugin>/.claude-plugin/plugin.json` and keeps
    feature-branch lag as a warning rather than an error.
    """
    home = tmp_path / "home"
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(repo)

    _write_manifest(repo, PLUGIN_NAME, WORKING_TREE_VERSION)
    codex_cache = home / ".codex" / "plugins" / "cache"
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)

    clone_manifest = (
        home
        / ".codex"
        / ".tmp"
        / "marketplaces"
        / MARKETPLACE_NAME
        / "plugins"
        / PLUGIN_NAME
        / ".claude-plugin"
        / "plugin.json"
    )
    clone_manifest.parent.mkdir(parents=True)
    clone_manifest.write_text(
        json.dumps({"name": PLUGIN_NAME, "version": PUBLISHED_VERSION})
    )

    exit_code = validate_install.main([MARKETPLACE_NAME])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert PLUGIN_NAME in captured.err
    assert WORKING_TREE_VERSION in captured.err
    assert PUBLISHED_VERSION in captured.err
    assert "warning:" in captured.err


def test_codex_cache_missing_when_working_tree_older_is_an_error(
    tmp_path: Path,
) -> None:
    """When the working-tree manifest is older than the marketplace clone (e.g., after
    reverting a version bump) and the cache lacks that version, the missing directory
    is an error — the ahead-only tolerance does not cover the inverse direction."""
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    older_version = "0.0.1"
    _write_manifest(repo_root, PLUGIN_NAME, older_version)
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)

    def published_version(plugin: str) -> str | None:
        return PUBLISHED_VERSION if plugin == PLUGIN_NAME else None

    result = validate_install.validate(
        MARKETPLACE_NAME,
        repo_root=repo_root,
        codex_cache_override=codex_cache,
        claude_cache_override=tmp_path / "empty_claude_cache",
        codex_marketplace_version=published_version,
    )

    assert result.warnings == [], f"unexpected warnings: {result.warnings}"
    assert len(result.errors) == 1
    assert older_version in result.errors[0]


def test_orphan_plugin_in_cache_emits_warning(tmp_path: Path) -> None:
    """When the cache contains a plugin directory absent from the working tree,
    the orphan is reported as a warning that names the plugin; errors are unchanged.
    """
    repo_root = tmp_path / "repo"
    codex_cache = tmp_path / "codex_cache"
    _write_manifest(repo_root, PLUGIN_NAME, PUBLISHED_VERSION)
    _seed_cache(codex_cache, PLUGIN_NAME, PUBLISHED_VERSION)
    _seed_cache(codex_cache, ORPHAN_PLUGIN_NAME, PUBLISHED_VERSION)

    def published_version(plugin: str) -> str | None:
        return PUBLISHED_VERSION if plugin == PLUGIN_NAME else None

    result = validate_install.validate(
        MARKETPLACE_NAME,
        repo_root=repo_root,
        codex_cache_override=codex_cache,
        claude_cache_override=tmp_path / "empty_claude_cache",
        codex_marketplace_version=published_version,
    )

    assert result.errors == [], f"unexpected errors: {result.errors}"
    orphan_warnings = [w for w in result.warnings if ORPHAN_PLUGIN_NAME in w]
    assert len(orphan_warnings) == 1, (
        f"expected one orphan warning naming {ORPHAN_PLUGIN_NAME}, "
        f"got: {result.warnings}"
    )


@pytest.mark.parametrize(
    ("working_tree", "published", "expected"),
    [
        ("0.2.0", "0.1.0", True),
        ("0.1.0", "0.1.0", False),
        ("0.0.1", "0.1.0", False),
        ("1.0.0", "0.99.99", True),
        # Tuple-prefix semantics: shorter tuples compare component-by-component,
        # so ("1", "0") is strictly greater than ("0", "9", "0").
        ("1.0", "0.9.0", True),
        # ("0", "9") and ("0", "9", "0") compare as () == () then 0==0 then
        # 9==9 then StopIteration on the shorter — Python returns False.
        ("0.9", "0.9.0", False),
        # Non-numeric component (pre-release, build metadata) is undefined ordering;
        # falls back to False so the caller applies strict validation.
        ("0.2.0-alpha", "0.1.0", False),
        ("0.2.0", "abc", False),
        ("", "0.1.0", False),
    ],
)
def test_is_strictly_ahead_compares_dotted_integer_versions(
    working_tree: str, published: str, expected: bool
) -> None:
    """is_strictly_ahead returns True only when working_tree's dotted-integer tuple
    compares strictly greater than published's. Non-numeric components yield False
    (callers fall back to strict validation)."""
    assert validate_install.is_strictly_ahead(working_tree, published) is expected


def test_cached_entries_orders_versions_numerically_not_lexicographically(
    tmp_path: Path,
) -> None:
    """cached_entries returns version directories ordered by parsed numeric
    components, not by string comparison. A lexicographic sort places "0.17.6"
    after "0.17.10"/"0.17.12" (because "6" > "1") and "0.10.0" before "0.9.0"
    (because "1" < "9"); the numeric order is 0.9.0 < 0.10.0 < 0.17.6 < 0.17.10
    < 0.17.12."""
    cache_root = tmp_path / "claude_cache"
    for version in ("0.17.10", "0.17.6", "0.17.12", "0.9.0", "0.10.0"):
        _seed_cache(cache_root, PLUGIN_NAME, version)

    entries = validate_install.cached_entries(
        cache_root, MARKETPLACE_NAME, PLUGIN_NAME, current_version="0.17.12"
    )

    assert [entry.version for entry in entries] == [
        "0.9.0",
        "0.10.0",
        "0.17.6",
        "0.17.10",
        "0.17.12",
    ]


def test_cached_entries_sorts_non_numeric_entries_after_numeric_versions(
    tmp_path: Path,
) -> None:
    """A cache entry whose name does not parse as dotted integers (a stray
    directory such as 'snapshot') sorts after every numeric version, so the
    listing tolerates it rather than raising on the int() conversion."""
    cache_root = tmp_path / "claude_cache"
    for version in ("0.10.0", "0.9.0", "snapshot"):
        _seed_cache(cache_root, PLUGIN_NAME, version)

    entries = validate_install.cached_entries(
        cache_root, MARKETPLACE_NAME, PLUGIN_NAME, current_version="0.10.0"
    )

    assert [entry.version for entry in entries] == ["0.9.0", "0.10.0", "snapshot"]


def test_cached_entries_synthesizes_current_when_working_tree_ahead(
    tmp_path: Path,
) -> None:
    """When synthesize_current is set and every real cached directory is below the
    current (working-tree) version, a non-materialized current entry is appended at
    its numeric position so the listing still marks the resolved version."""
    cache_root = tmp_path / "claude_cache"
    for version in ("0.56.1", "0.56.3"):
        _seed_cache(cache_root, PLUGIN_NAME, version)

    entries = validate_install.cached_entries(
        cache_root, MARKETPLACE_NAME, PLUGIN_NAME, "0.56.5", synthesize_current=True
    )

    assert [e.version for e in entries] == ["0.56.1", "0.56.3", "0.56.5"]
    synth = entries[-1]
    assert synth.is_current and not synth.materialized
    assert not entries[0].is_current and not entries[1].is_current


def test_cached_entries_synthesizes_current_into_mid_numeric_position(
    tmp_path: Path,
) -> None:
    """The synthesized current row sorts into numeric position, not merely appended:
    a current version between two cached versions lands between them, proving the
    sort positions the synthetic entry rather than tacking it onto the end."""
    cache_root = tmp_path / "claude_cache"
    for version in ("0.56.1", "0.56.5"):
        _seed_cache(cache_root, PLUGIN_NAME, version)

    entries = validate_install.cached_entries(
        cache_root, MARKETPLACE_NAME, PLUGIN_NAME, "0.56.3", synthesize_current=True
    )

    assert [e.version for e in entries] == ["0.56.1", "0.56.3", "0.56.5"]
    assert entries[1].version == "0.56.3"
    assert entries[1].is_current and not entries[1].materialized


def test_cached_entries_marks_real_current_without_synthesizing(
    tmp_path: Path,
) -> None:
    """When the current version matches a real cached directory, that directory is
    marked current and no synthetic row is added even with synthesize_current set."""
    cache_root = tmp_path / "claude_cache"
    for version in ("0.56.1", "0.56.3"):
        _seed_cache(cache_root, PLUGIN_NAME, version)

    entries = validate_install.cached_entries(
        cache_root, MARKETPLACE_NAME, PLUGIN_NAME, "0.56.3", synthesize_current=True
    )

    assert [e.version for e in entries] == ["0.56.1", "0.56.3"]
    assert all(e.materialized for e in entries)
    assert entries[1].is_current and not entries[0].is_current


def test_cached_entries_no_synthesis_when_plugin_absent_from_cache(
    tmp_path: Path,
) -> None:
    """A plugin with no cached directories gets no synthetic current row — synthesis
    applies only when the working tree is ahead of existing directories."""
    cache_root = tmp_path / "claude_cache"

    entries = validate_install.cached_entries(
        cache_root, MARKETPLACE_NAME, PLUGIN_NAME, "0.56.5", synthesize_current=True
    )

    assert entries == []


def test_print_cache_claude_marks_synthesized_working_tree_current(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The Claude listing renders the working-tree version as the current row,
    annotated as resolving from the working tree, when the cache lags behind it."""
    cache_root = tmp_path / "claude_cache"
    for version in ("0.56.1", "0.56.3"):
        _seed_cache(cache_root, PLUGIN_NAME, version)

    validate_install.print_cache(
        cache_root,
        "Claude Code",
        MARKETPLACE_NAME,
        {PLUGIN_NAME: "0.56.5"},
        working_tree_pinned=True,
    )

    current_lines = [
        line
        for line in capsys.readouterr().out.splitlines()
        if validate_install.CURRENT_MARKER in line
    ]
    assert len(current_lines) == 1, f"expected one current row, got {current_lines}"
    assert "0.56.5" in current_lines[0]
    assert validate_install.WORKING_TREE_KIND in current_lines[0]


def test_parse_codex_reported_versions_maps_installed_name_to_version() -> None:
    """parse_codex_reported_versions returns name → version for installed entries
    scoped to the marketplace; entries naming another marketplace are excluded."""
    payload = json.dumps(
        {
            "installed": [
                {
                    "name": "spec-tree",
                    "version": "0.56.3",
                    "marketplaceName": MARKETPLACE_NAME,
                },
                {
                    "name": "prose",
                    "version": "0.4.0",
                    "marketplaceName": MARKETPLACE_NAME,
                },
                {"name": "foreign", "version": "9.9.9", "marketplaceName": "elsewhere"},
            ],
            "available": [],
        }
    )

    versions = validate_install.parse_codex_reported_versions(payload, MARKETPLACE_NAME)

    assert versions == {"spec-tree": "0.56.3", "prose": "0.4.0"}


def test_parse_codex_reported_versions_empty_on_unrecognized_payload() -> None:
    """An unparseable, non-object, or installed-less payload degrades to an empty map
    rather than raising — the listing must not crash on a malformed CLI response."""
    assert (
        validate_install.parse_codex_reported_versions("not json", MARKETPLACE_NAME)
        == {}
    )
    assert (
        validate_install.parse_codex_reported_versions(json.dumps([]), MARKETPLACE_NAME)
        == {}
    )
    assert (
        validate_install.parse_codex_reported_versions(
            json.dumps({"available": []}), MARKETPLACE_NAME
        )
        == {}
    )


def test_codex_reported_versions_empty_on_nonzero_exit() -> None:
    """A non-zero exit from the Codex CLI degrades to an empty map; the informational
    listing tolerates a failing CLI."""

    def failing_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, stdout="")

    assert (
        validate_install.codex_reported_versions(
            MARKETPLACE_NAME, runner=failing_runner
        )
        == {}
    )


def test_codex_reported_versions_empty_when_cli_absent() -> None:
    """When the Codex binary is absent the runner raises OSError, and the query
    degrades to an empty map rather than propagating — the most common 'CLI
    unavailable' case on a fresh install or in CI, distinct from a non-zero exit."""

    def absent_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        raise FileNotFoundError("codex: command not found")

    assert (
        validate_install.codex_reported_versions(MARKETPLACE_NAME, runner=absent_runner)
        == {}
    )


def test_codex_reported_versions_forwards_the_marketplace_to_the_cli() -> None:
    """The query invokes `codex plugin list --json --marketplace <marketplace>`: the
    marketplace token is forwarded so the listing is scoped to the right marketplace,
    and a wrong subcommand or missing flag is caught here rather than at runtime."""
    captured: list[list[str]] = []

    def recording_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        captured.append(command)
        return subprocess.CompletedProcess(
            command, 0, stdout=json.dumps({"installed": [], "available": []})
        )

    validate_install.codex_reported_versions(MARKETPLACE_NAME, runner=recording_runner)

    assert captured == [[*validate_install.CODEX_LIST_COMMAND, MARKETPLACE_NAME]]


def test_print_cache_codex_marks_reported_version_not_working_tree(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The Codex listing marks current against the version Codex reports (via
    current_override), not the local working-tree version — a feature-branch working
    tree ahead of what Codex resolves does not move the marker."""
    cache_root = tmp_path / "codex_cache"
    for version in ("0.4.0", "0.5.0"):
        _seed_cache(cache_root, PLUGIN_NAME, version)

    validate_install.print_cache(
        cache_root,
        "Codex",
        MARKETPLACE_NAME,
        {PLUGIN_NAME: "0.5.0"},
        current_override={PLUGIN_NAME: "0.4.0"},
    )

    current_lines = [
        line
        for line in capsys.readouterr().out.splitlines()
        if validate_install.CURRENT_MARKER in line
    ]
    assert len(current_lines) == 1, f"expected one current row, got {current_lines}"
    assert "0.4.0" in current_lines[0]
    assert "0.5.0" not in current_lines[0]


def test_print_cache_codex_no_marker_when_reported_version_absent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When the version Codex reports has no cache directory, the Codex listing shows
    no current marker — the Codex listing does not synthesize a row the way the
    working-tree-pinned Claude listing does. validate_install surfaces the absent
    version separately."""
    cache_root = tmp_path / "codex_cache"
    _seed_cache(cache_root, PLUGIN_NAME, "0.5.0")

    validate_install.print_cache(
        cache_root,
        "Codex",
        MARKETPLACE_NAME,
        {PLUGIN_NAME: "0.5.0"},
        current_override={PLUGIN_NAME: "0.4.0"},
    )

    out = capsys.readouterr().out
    assert "0.5.0" in out, "the materialized version is still listed"
    assert validate_install.CURRENT_MARKER not in out, (
        "Codex does not synthesize a current row for a reported version absent from "
        "the cache"
    )
