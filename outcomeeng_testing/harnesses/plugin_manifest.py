"""Resource lifecycle and observations for plugin-manifest evidence."""

from __future__ import annotations

import io
import json
import os
import subprocess
import time
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from typing import Final, cast

import pytest
from hypothesis import given, seed, settings

from outcomeeng.distribution.orchestration import (
    CLAUDE_DIST_PLUGINS_DIR,
    SOURCE_PLUGINS_DIR,
)
from outcomeeng.validation.audit_artifacts import SPEC_TREE_PLUGIN_NAME
from outcomeeng.validation.plugins import (
    CATALOGS,
    CATALOG_PLUGINS_FIELD,
    CLAUDE_PLUGIN_VALIDATE_ARGV,
    PLUGIN_NAME_FIELD,
    PLUGIN_VERSION_FIELD,
    VALIDATE_TIMEOUT_SECONDS,
    check_catalog_sync,
    check_manifest_parity,
    main,
    run_validate,
)
from outcomeeng_testing.harnesses.capturing_runner import (
    DESCENDANT_SLEEP_SECONDS,
    PROMPT_RETURN_CEILING_SECONDS,
    TEST_TIMEOUT_SECONDS,
    child_exiting_with_lingering_descendant,
    never_returning_child,
)
from outcomeeng_testing.generators.plugin_manifest import distinct_version_pairs
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PARITY_PROPERTY_EXAMPLES: Final = 100
PARITY_PROPERTY_SEED: Final = 20260716
PARITY_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/15-validation.enabler/32-plugin-manifest.enabler/tests/"
    "test_plugin_manifest.property.l1.py"
)

requires_fork = pytest.mark.skipif(
    not hasattr(os, "fork"),
    reason=(
        "POSIX-only: the capturing-runner harness uses os.fork and "
        "process-group signalling"
    ),
)


@dataclass
class RecordingValidationRunner:
    """Record validator commands and optionally fail one exact target."""

    failing_target: Path | None = None
    commands: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(
        self,
        command: list[str],
        **_: object,
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(tuple(command))
        failed = self.failing_target is not None and command[-1] == str(
            self.failing_target
        )
        return subprocess.CompletedProcess(
            command,
            returncode=int(failed),
            stdout="" if failed else RecordingValidationRunner.__doc__ or "",
            stderr=RecordingValidationRunner.__doc__ or "" if failed else "",
        )


def marketplace_is_validated() -> bool:
    """Validate a marketplace root through the exact Claude CLI command."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        _write_catalogs(root, ())
        runner = RecordingValidationRunner()
        exit_code, _, _ = _captured_main(root, runner)
        return exit_code == 0 and runner.commands == [_validation_command(root)]


def source_plugins_are_validated() -> bool:
    """Validate every discovered authored plugin and the marketplace root."""
    return _plugin_layout_is_validated(
        SOURCE_PLUGINS_DIR, catalogs_include_plugins=True
    )


def generated_plugins_are_validated() -> bool:
    """Validate every discovered generated Claude plugin and marketplace root."""
    return _plugin_layout_is_validated(
        CLAUDE_DIST_PLUGINS_DIR,
        catalogs_include_plugins=False,
    )


def failed_plugin_validation_is_reported() -> bool:
    """Return whether one failed plugin names itself and exits nonzero."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        plugin_path = _copy_plugin(root, SOURCE_PLUGINS_DIR, plugin_name)
        _write_catalogs(root, (plugin_name,))
        runner = RecordingValidationRunner(failing_target=plugin_path)
        exit_code, _, stderr = _captured_main(root, runner)
        return exit_code != 0 and plugin_name in stderr


def absent_validation_targets_are_rejected() -> bool:
    """Return whether an empty root exits nonzero with a diagnostic."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        exit_code, _, stderr = _captured_main(root, RecordingValidationRunner())
        return exit_code != 0 and bool(stderr)


def plugin_absent_from_claude_catalog_is_reported() -> bool:
    """Return whether Claude catalog omission names the authored plugin."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        _write_plugin(root, plugin_name, _version_pair()[0])
        _write_catalog(root, next(iter(CATALOGS.values())), ())
        _write_catalog(root, tuple(CATALOGS.values())[1], (plugin_name,))
        return _catalog_errors_name(root, plugin_name)


def plugin_absent_from_codex_catalog_is_reported() -> bool:
    """Return whether Codex catalog omission names the authored plugin."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        _write_plugin(root, plugin_name, _version_pair()[0])
        _write_catalog(root, next(iter(CATALOGS.values())), (plugin_name,))
        _write_catalog(root, tuple(CATALOGS.values())[1], ())
        return _catalog_errors_name(root, plugin_name)


def matching_catalogs_pass() -> bool:
    """Return whether identical catalog membership produces no errors."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        plugin_names = _sample_plugin_names(2)
        for plugin_name in plugin_names:
            _write_plugin(root, plugin_name, _version_pair()[0])
        _write_catalogs(root, plugin_names)
        return not check_catalog_sync(root)


def catalog_entry_without_plugin_is_reported() -> bool:
    """Return whether a catalog-only plugin entry is rejected."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        _write_catalogs(root, (plugin_name,))
        return _catalog_errors_name(root, plugin_name)


def catalog_mismatch_makes_main_fail() -> bool:
    """Return whether main reports an authored plugin absent from catalogs."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        _copy_plugin(root, SOURCE_PLUGINS_DIR, plugin_name)
        _write_catalogs(root, ())
        exit_code, _, stderr = _captured_main(root, RecordingValidationRunner())
        return exit_code != 0 and plugin_name in stderr


def matching_manifest_versions_pass() -> bool:
    """Return whether equal Claude and Codex versions pass parity."""
    return _manifest_parity_errors(None, None) == []


def manifest_version_drift_names_both_versions() -> bool:
    """Return whether drift reports the plugin and both version values."""
    first, second = _version_pair()
    errors = _manifest_parity_errors(first, second)
    (plugin_name,) = _sample_plugin_names(1)
    return (
        len(errors) == 1
        and plugin_name in errors[0]
        and first in errors[0]
        and second in errors[0]
    )


def absent_codex_manifest_skips_parity() -> bool:
    """Return whether a Claude-only plugin skips parity validation."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        _write_plugin(root, plugin_name, _version_pair()[0])
        return not check_manifest_parity(root)


def absent_claude_version_is_reported() -> bool:
    """Return whether an absent Claude version field is named."""
    return _missing_version_is_reported(
        claude_version=None, codex_version=_version_pair()[0]
    )


def absent_codex_version_is_reported() -> bool:
    """Return whether an absent Codex version field is named."""
    return _missing_version_is_reported(
        claude_version=_version_pair()[0], codex_version=None
    )


def manifest_version_parity_is_symmetric() -> bool:
    """Exercise both drift directions across generated version pairs."""
    run_replayable_property(
        _generated_manifest_version_parity_is_symmetric,
        seed_value=PARITY_PROPERTY_SEED,
        replay_path=PARITY_PROPERTY_REPLAY_PATH,
    )
    return True


@seed(PARITY_PROPERTY_SEED)
@settings(
    max_examples=PARITY_PROPERTY_EXAMPLES,
    deadline=None,
    print_blob=True,
)
@given(versions=distinct_version_pairs())
def _generated_manifest_version_parity_is_symmetric(
    versions: tuple[str, str],
) -> None:
    first, second = versions
    assert len(_manifest_parity_errors(first, second)) == 1
    assert len(_manifest_parity_errors(second, first)) == 1


def parity_drift_makes_main_fail() -> bool:
    """Return whether main exits nonzero and reports manifest parity drift."""
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        first, second = _version_pair()
        _write_plugin(root, plugin_name, first, codex_version=second)
        _write_catalogs(root, (plugin_name,))
        exit_code, _, stderr = _captured_main(root, RecordingValidationRunner())
        return (
            exit_code != 0
            and plugin_name in stderr
            and first in stderr
            and second in stderr
            and "manifest parity" in stderr
        )


def timeout_terminates_group_and_names_command() -> bool:
    """Return whether timeout bounds execution and terminates descendants."""
    with never_returning_child() as child:
        start = time.monotonic()
        result = run_validate(list(child.command), timeout=TEST_TIMEOUT_SECONDS)
        elapsed = time.monotonic() - start
        return (
            result.returncode != 0
            and result.args == list(child.command)
            and "timed out" in result.stderr
            and child.command[0] in result.stderr
            and elapsed < DESCENDANT_SLEEP_SECONDS
            and child.descendant_alive() is False
        )


def invocation_exit_is_not_blocked_by_descendant() -> bool:
    """Return whether capture ends when the invoked process exits."""
    with child_exiting_with_lingering_descendant() as child:
        start = time.monotonic()
        result = run_validate(list(child.command), timeout=VALIDATE_TIMEOUT_SECONDS)
        elapsed = time.monotonic() - start
        return (
            result.returncode == 0
            and result.stdout == "done"
            and elapsed < PROMPT_RETURN_CEILING_SECONDS
            and child.descendant_alive() is True
        )


def _plugin_layout_is_validated(
    relative_plugins_dir: Path,
    *,
    catalogs_include_plugins: bool,
) -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        source_plugin_paths = _layout_plugin_paths(relative_plugins_dir)
        plugin_names = tuple(path.name for path in source_plugin_paths)
        plugin_paths = tuple(
            _copy_layout_plugin(root, relative_plugins_dir, plugin_path)
            for plugin_path in source_plugin_paths
        )
        _write_catalogs(root, plugin_names if catalogs_include_plugins else ())
        runner = RecordingValidationRunner()
        exit_code, _, _ = _captured_main(root, runner)
        expected = sorted(
            (_validation_command(root), *map(_validation_command, plugin_paths))
        )
        return exit_code == 0 and sorted(runner.commands) == expected


def _captured_main(
    root: Path,
    runner: RecordingValidationRunner,
) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        exit_code = main([str(root)], runner=runner)
    return exit_code, stdout.getvalue(), stderr.getvalue()


def _catalog_errors_name(root: Path, plugin_name: str) -> bool:
    return any(plugin_name in error for error in check_catalog_sync(root))


def _manifest_parity_errors(
    claude_version: str | None,
    codex_version: str | None,
) -> list[str]:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        first, _ = _version_pair()
        _write_plugin(
            root,
            plugin_name,
            first
            if claude_version is None and codex_version is None
            else claude_version,
            codex_version=(
                first
                if claude_version is None and codex_version is None
                else codex_version
            ),
        )
        return check_manifest_parity(root)


def _missing_version_is_reported(
    *,
    claude_version: str | None,
    codex_version: str | None,
) -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        (plugin_name,) = _sample_plugin_names(1)
        _write_plugin(
            root,
            plugin_name,
            claude_version,
            codex_version=codex_version,
        )
        _write_catalogs(root, (plugin_name,))
        exit_code, _, stderr = _captured_main(root, RecordingValidationRunner())
        return (
            exit_code != 0
            and plugin_name in stderr
            and PLUGIN_VERSION_FIELD in stderr
            and "missing" in stderr
        )


def _sample_plugin_names(count: int) -> tuple[str, ...]:
    return tuple(
        plugin_dir.name
        for plugin_dir in sorted((REPO_ROOT / SOURCE_PLUGINS_DIR).iterdir())
        if plugin_dir.is_dir()
        and plugin_dir.name != SPEC_TREE_PLUGIN_NAME
        and (plugin_dir / ".claude-plugin" / "plugin.json").is_file()
    )[:count]


def _copy_plugin(root: Path, relative_plugins_dir: Path, plugin_name: str) -> Path:
    plugin_path = root / relative_plugins_dir / plugin_name
    copytree(
        REPO_ROOT / SOURCE_PLUGINS_DIR / plugin_name / ".claude-plugin",
        plugin_path / ".claude-plugin",
    )
    return plugin_path


def _layout_plugin_paths(relative_plugins_dir: Path) -> tuple[Path, ...]:
    return tuple(
        plugin_path
        for plugin_path in sorted((REPO_ROOT / relative_plugins_dir).iterdir())
        if plugin_path.is_dir()
        and (plugin_path / ".claude-plugin" / "plugin.json").is_file()
    )


def _copy_layout_plugin(
    root: Path,
    relative_plugins_dir: Path,
    source_plugin_path: Path,
) -> Path:
    plugin_path = root / relative_plugins_dir / source_plugin_path.name
    copytree(source_plugin_path, plugin_path)
    return plugin_path


def _write_catalogs(root: Path, plugin_names: tuple[str, ...]) -> None:
    for relative_path in CATALOGS.values():
        _write_catalog(root, relative_path, plugin_names)


def _write_catalog(
    root: Path,
    relative_path: Path,
    plugin_names: tuple[str, ...],
) -> None:
    catalog_path = root / relative_path
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(
            {
                CATALOG_PLUGINS_FIELD: [
                    {PLUGIN_NAME_FIELD: plugin_name} for plugin_name in plugin_names
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_plugin(
    root: Path,
    plugin_name: str,
    claude_version: str | None,
    *,
    codex_version: str | None | object = ...,
) -> Path:
    plugin_path = root / SOURCE_PLUGINS_DIR / plugin_name
    _write_manifest(
        plugin_path / ".claude-plugin" / "plugin.json",
        plugin_name,
        claude_version,
    )
    if codex_version is not ...:
        _write_manifest(
            plugin_path / ".codex-plugin" / "plugin.json",
            plugin_name,
            cast(str | None, codex_version),
        )
    return plugin_path


def _write_manifest(path: Path, plugin_name: str, version: str | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {PLUGIN_NAME_FIELD: plugin_name}
    if version is not None:
        manifest[PLUGIN_VERSION_FIELD] = version
    path.write_text(json.dumps(manifest), encoding="utf-8")


def _version_pair() -> tuple[str, str]:
    (plugin_name,) = _sample_plugin_names(1)
    manifest_path = (
        REPO_ROOT / SOURCE_PLUGINS_DIR / plugin_name / ".claude-plugin" / "plugin.json"
    )
    manifest = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
    if not isinstance(manifest, dict):
        raise TypeError(f"plugin manifest is not a JSON object: {manifest_path}")
    version = manifest.get(PLUGIN_VERSION_FIELD)
    if not isinstance(version, str):
        raise TypeError(f"plugin manifest has no version: {manifest_path}")
    major, minor, patch = (int(part) for part in version.split("."))
    return version, f"{major}.{minor}.{patch + 1}"


def _validation_command(target: Path) -> tuple[str, ...]:
    return (*CLAUDE_PLUGIN_VALIDATE_ARGV, str(target))
