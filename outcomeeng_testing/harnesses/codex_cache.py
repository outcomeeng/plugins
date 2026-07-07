"""Harnesses for Codex cache reconciliation tests."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from hypothesis import given, seed, settings

from outcomeeng.distribution import codex_cache as preserve_codex_plugin_cache
from outcomeeng.distribution.codex_cache import CODEX_PLUGIN_ADD_COMMAND
from outcomeeng.distribution.marketplace_sources import (
    CODEX_PLUGIN_MANIFEST,
    DEFAULT_MARKETPLACE,
    DIST_CODEX_PLUGINS_DIR,
    MARKETPLACE_FIELD_NAME,
    PLUGIN_MANIFEST_FIELD_VERSION,
    available_codex_plugins,
)
from outcomeeng_testing.generators.codex_cache import (
    AddableCodexPluginSet,
    StaleAfterSuccessfulRefresh,
    addable_codex_plugin_sets,
    stale_after_successful_refreshes,
)

CODEX_CACHE_PROPERTY_SEED = 20260704
CODEX_CACHE_PROPERTY_EXAMPLES = 40
CODEX_CACHE_COMPLIANCE_SEED = 20260706
CODEX_CACHE_COMPLIANCE_EXAMPLES = 40
CODEX_CACHE_PROPERTY_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/32-installation.enabler/tests/"
    "test_codex_plugin_cache.property.l1.py"
)
CODEX_CACHE_COMPLIANCE_REPLAY_PATH = (
    "just test "
    "spx/13-infrastructure.enabler/32-installation.enabler/tests/"
    "test_codex_plugin_cache.compliance.l1.py"
)


@dataclass(frozen=True)
class CodexCacheWorkspace:
    repo_root: Path
    cache_root: Path


@dataclass
class MaterializingAddRunner:
    """Runner stub that materializes cache roots for local Codex plugin adds.

    Stage 5 exception 2 (interaction-protocol DI): the production path invokes
    `codex plugin add <plugin>@<marketplace>` and observes Codex's filesystem
    side effect. The L1 test records the command sequence and materializes the
    same side effect deterministically.
    """

    cache_root: Path
    versions: dict[str, str]
    calls: list[tuple[str, ...]] = field(default_factory=list)

    @classmethod
    def from_dist_manifests(
        cls, *, cache_root: Path, repo_root: Path
    ) -> "MaterializingAddRunner":
        return cls(
            cache_root=cache_root,
            versions={
                plugin.name: plugin.version
                for plugin in available_codex_plugins(repo_root)
            },
        )

    def __call__(
        self, command: list[str], *, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        command_tuple = tuple(command)
        self.calls.append(command_tuple)
        if command_tuple[: len(CODEX_PLUGIN_ADD_COMMAND)] == CODEX_PLUGIN_ADD_COMMAND:
            plugin_ref = command_tuple[len(CODEX_PLUGIN_ADD_COMMAND)]
            plugin, separator, marketplace = plugin_ref.partition("@")
            if separator != "@" or marketplace != DEFAULT_MARKETPLACE:
                return subprocess.CompletedProcess(command, 64)
            write_plugin_root(
                self.cache_root,
                plugin,
                self.versions[plugin],
                f"{plugin} materialized content",
            )
        return subprocess.CompletedProcess(command, 0)


@dataclass(frozen=True)
class StaticHistory:
    """Interaction-protocol stub for plugin history in synthetic repositories."""

    plugins: frozenset[str]
    versions_by_plugin: dict[str, frozenset[str]]
    current_by_plugin: dict[str, str]

    def working_tree_plugins(self) -> frozenset[str]:
        return self.plugins

    def published_versions(self, plugin: str) -> frozenset[str]:
        return self.versions_by_plugin.get(plugin, frozenset())

    def current_version(self, plugin: str) -> str | None:
        return self.current_by_plugin.get(plugin)


@dataclass(frozen=True)
class StaticInstalled:
    """Interaction-protocol stub for the Codex installed-version provider."""

    versions: dict[str, str]
    calls: list[str] = field(default_factory=list)

    def installed_plugin_versions(self, marketplace: str) -> dict[str, str]:
        self.calls.append(marketplace)
        return self.versions


def codex_cache_refresh_property(
    test: Callable[[StaleAfterSuccessfulRefresh], None],
) -> Callable[[], None]:
    configured = seed(CODEX_CACHE_PROPERTY_SEED)(
        settings(max_examples=CODEX_CACHE_PROPERTY_EXAMPLES)(
            given(refresh=stale_after_successful_refreshes())(test)
        )
    )

    def wrapper() -> None:
        try:
            configured()
        except AssertionError as error:
            error.add_note(f"Hypothesis seed: {CODEX_CACHE_PROPERTY_SEED}")
            error.add_note(f"Replay path: {CODEX_CACHE_PROPERTY_REPLAY_PATH}")
            raise

    return wrapper


def codex_cache_addable_compliance(
    test: Callable[[AddableCodexPluginSet], None],
) -> Callable[[], None]:
    configured = seed(CODEX_CACHE_COMPLIANCE_SEED)(
        settings(max_examples=CODEX_CACHE_COMPLIANCE_EXAMPLES)(
            given(plugin_set=addable_codex_plugin_sets())(test)
        )
    )

    def wrapper() -> None:
        try:
            configured()
        except AssertionError as error:
            error.add_note(f"Hypothesis seed: {CODEX_CACHE_COMPLIANCE_SEED}")
            error.add_note(f"Replay path: {CODEX_CACHE_COMPLIANCE_REPLAY_PATH}")
            raise

    return wrapper


def codex_cache_property_failure_notes_include_seed_and_replay() -> bool:
    def always_fails(refresh: StaleAfterSuccessfulRefresh) -> None:
        assert refresh.plugin == ""

    try:
        codex_cache_refresh_property(always_fails)()
    except AssertionError as error:
        notes = getattr(error, "__notes__", ())
        return (
            f"Hypothesis seed: {CODEX_CACHE_PROPERTY_SEED}" in notes
            and f"Replay path: {CODEX_CACHE_PROPERTY_REPLAY_PATH}" in notes
        )
    return False


def local_refresh_never_invokes_marketplace_upgrade() -> bool:
    with codex_cache_workspace() as workspace:
        plugin_name = "spec-tree"
        version = "0.1.0"
        write_dist_codex_manifest(workspace.repo_root, plugin_name, version)
        history = StaticHistory(
            plugins=frozenset([plugin_name]),
            versions_by_plugin={plugin_name: frozenset([version])},
            current_by_plugin={plugin_name: version},
        )
        runner = MaterializingAddRunner(
            cache_root=workspace.cache_root,
            versions={plugin_name: version},
        )

        result = preserve_codex_plugin_cache.refresh_installed_plugins(
            DEFAULT_MARKETPLACE,
            repo_root=workspace.repo_root,
            cache_root=workspace.cache_root,
            history=history,
            installed=StaticInstalled({plugin_name: version}),
            runner=runner,
        )

    return (
        runner.calls
        == [
            (
                *preserve_codex_plugin_cache.CODEX_PLUGIN_ADD_COMMAND,
                f"{plugin_name}@{DEFAULT_MARKETPLACE}",
            )
        ]
        and all(
            command[:3] != ("codex", "plugin", "marketplace")
            for command in runner.calls
        )
        and result.refresh_returncode == 0
    )


@codex_cache_addable_compliance
def local_refresh_reads_addable_codex_plugins_from_dist_codex(
    plugin_set: AddableCodexPluginSet,
) -> None:
    with codex_cache_workspace() as workspace:
        generated_versions = {
            plugin: f"0.2.{index}"
            for index, plugin in enumerate(plugin_set.generated_plugins)
        }
        for plugin, version in generated_versions.items():
            write_dist_codex_manifest(workspace.repo_root, plugin, version)
        (workspace.repo_root / DIST_CODEX_PLUGINS_DIR / "missing-manifest").mkdir(
            parents=True
        )
        working_tree_only_version = "0.9.0"
        history = StaticHistory(
            plugins=frozenset(
                [*plugin_set.generated_plugins, plugin_set.working_tree_only_plugin]
            ),
            versions_by_plugin={
                **{
                    plugin: frozenset([version])
                    for plugin, version in generated_versions.items()
                },
                plugin_set.working_tree_only_plugin: frozenset(
                    [working_tree_only_version]
                ),
            },
            current_by_plugin={
                **generated_versions,
                plugin_set.working_tree_only_plugin: working_tree_only_version,
            },
        )
        runner = MaterializingAddRunner.from_dist_manifests(
            cache_root=workspace.cache_root,
            repo_root=workspace.repo_root,
        )

        result = preserve_codex_plugin_cache.refresh_installed_plugins(
            DEFAULT_MARKETPLACE,
            repo_root=workspace.repo_root,
            cache_root=workspace.cache_root,
            history=history,
            installed=StaticInstalled({}),
            runner=runner,
        )

    assert runner.calls == [
        (
            *preserve_codex_plugin_cache.CODEX_PLUGIN_ADD_COMMAND,
            f"{plugin}@{DEFAULT_MARKETPLACE}",
        )
        for plugin in plugin_set.generated_plugins
    ]
    assert result.refresh_returncode == 0
    assert "missing-manifest" not in {
        plugin.name for plugin in available_codex_plugins(workspace.repo_root)
    }


@codex_cache_refresh_property
def successful_refresh_reconciles_to_generated_codex_manifest_version(
    refresh: StaleAfterSuccessfulRefresh,
) -> None:
    with codex_cache_workspace() as workspace:
        write_dist_codex_manifest(
            workspace.repo_root,
            refresh.plugin,
            refresh.desired_version,
        )
        write_plugin_root(
            workspace.cache_root,
            refresh.plugin,
            refresh.stale_version,
            "stale content",
        )
        plugin_dir = workspace.cache_root / DEFAULT_MARKETPLACE / refresh.plugin
        stale_dir = plugin_dir / refresh.stale_version
        desired_dir = plugin_dir / refresh.desired_version
        history = StaticHistory(
            plugins=frozenset([refresh.plugin]),
            versions_by_plugin={
                refresh.plugin: frozenset(
                    [refresh.stale_version, refresh.desired_version]
                ),
            },
            current_by_plugin={refresh.plugin: refresh.stale_version},
        )
        installed = StaticInstalled(
            versions={refresh.plugin: refresh.stale_version},
        )
        runner = MaterializingAddRunner.from_dist_manifests(
            cache_root=workspace.cache_root,
            repo_root=workspace.repo_root,
        )

        result = preserve_codex_plugin_cache.refresh_installed_plugins(
            DEFAULT_MARKETPLACE,
            repo_root=workspace.repo_root,
            cache_root=workspace.cache_root,
            history=history,
            installed=installed,
            runner=runner,
        )

        assert runner.calls == [
            (
                *preserve_codex_plugin_cache.CODEX_PLUGIN_ADD_COMMAND,
                f"{refresh.plugin}@{DEFAULT_MARKETPLACE}",
            )
        ]
        assert installed.calls == [DEFAULT_MARKETPLACE, DEFAULT_MARKETPLACE]
        assert result.refresh_returncode == 0
        assert desired_dir.is_dir() and not desired_dir.is_symlink(), (
            f"expected {desired_dir} to remain the real current directory"
        )
        assert stale_dir.is_symlink(), (
            f"expected {stale_dir} to become a compatibility symlink"
        )
        assert stale_dir.resolve() == desired_dir.resolve(), (
            f"expected {stale_dir} to point at {desired_dir}"
        )
        real_versions = sorted(
            path.name
            for path in plugin_dir.iterdir()
            if path.is_dir() and not path.is_symlink()
        )
        assert real_versions == [refresh.desired_version]


@codex_cache_refresh_property
def successful_refresh_preserves_absent_stale_codex_reported_version(
    refresh: StaleAfterSuccessfulRefresh,
) -> None:
    with codex_cache_workspace() as workspace:
        write_dist_codex_manifest(
            workspace.repo_root,
            refresh.plugin,
            refresh.desired_version,
        )
        history = StaticHistory(
            plugins=frozenset([refresh.plugin]),
            versions_by_plugin={refresh.plugin: frozenset([refresh.desired_version])},
            current_by_plugin={refresh.plugin: refresh.desired_version},
        )
        installed = StaticInstalled(
            versions={refresh.plugin: refresh.stale_version},
        )
        runner = MaterializingAddRunner.from_dist_manifests(
            cache_root=workspace.cache_root,
            repo_root=workspace.repo_root,
        )

        result = preserve_codex_plugin_cache.refresh_installed_plugins(
            DEFAULT_MARKETPLACE,
            repo_root=workspace.repo_root,
            cache_root=workspace.cache_root,
            history=history,
            installed=installed,
            runner=runner,
        )

        plugin_dir = workspace.cache_root / DEFAULT_MARKETPLACE / refresh.plugin
        stale_dir = plugin_dir / refresh.stale_version
        desired_dir = plugin_dir / refresh.desired_version
        assert result.refresh_returncode == 0
        assert desired_dir.is_dir() and not desired_dir.is_symlink(), (
            f"expected {desired_dir} to remain the real current directory"
        )
        assert stale_dir.is_symlink(), (
            f"expected absent stale report {stale_dir} to be recreated"
        )
        assert stale_dir.resolve() == desired_dir.resolve(), (
            f"expected {stale_dir} to point at {desired_dir}"
        )


@contextmanager
def codex_cache_workspace() -> Iterator[CodexCacheWorkspace]:
    """Create an isolated repository/cache pair for one generated example."""
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        yield CodexCacheWorkspace(
            repo_root=workspace / "repo",
            cache_root=workspace / "cache",
        )


def write_plugin_root(
    cache_root: Path,
    plugin: str,
    version: str,
    text: str,
) -> None:
    plugin_root = cache_root / DEFAULT_MARKETPLACE / plugin / version
    skill_file = plugin_root / "skills" / "contextualize" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(text)
    manifest = plugin_root / CODEX_PLUGIN_MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {MARKETPLACE_FIELD_NAME: plugin, PLUGIN_MANIFEST_FIELD_VERSION: version}
        )
    )


def write_dist_codex_manifest(
    repo_root: Path,
    plugin: str,
    version: str,
) -> None:
    manifest = repo_root / DIST_CODEX_PLUGINS_DIR / plugin / CODEX_PLUGIN_MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {MARKETPLACE_FIELD_NAME: plugin, PLUGIN_MANIFEST_FIELD_VERSION: version}
        )
    )


__all__ = [
    "codex_cache_property_failure_notes_include_seed_and_replay",
    "CodexCacheWorkspace",
    "MaterializingAddRunner",
    "StaticHistory",
    "StaticInstalled",
    "codex_cache_refresh_property",
    "codex_cache_workspace",
    "local_refresh_reads_addable_codex_plugins_from_dist_codex",
    "local_refresh_never_invokes_marketplace_upgrade",
    "successful_refresh_preserves_absent_stale_codex_reported_version",
    "successful_refresh_reconciles_to_generated_codex_manifest_version",
    "write_dist_codex_manifest",
    "write_plugin_root",
]
