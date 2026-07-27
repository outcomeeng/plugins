"""Discover and validate all marketplace and plugin manifests.

Finds the marketplace root (.claude-plugin/marketplace.json) and all built
Claude plugin directories (dist/claude/*/.claude-plugin/plugin.json), then runs
``claude plugin validate`` on each.

Also checks:
  - Every authored plugin directory is registered in all marketplace catalogs:
      - .claude-plugin/marketplace.json  (Claude Code)
      - .agents/plugins/marketplace.json (Codex)
  - For plugins with both .claude-plugin/plugin.json and
    .codex-plugin/plugin.json, the ``version`` field matches across both
    manifests. Drift breaks repository installation because each agent reads
    its own manifest.

Usage::

    uv run python -m outcomeeng.validation.plugins [root_dir]

Exit codes:
    0 - All validations passed
    1 - One or more validations failed or no targets found
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import IO, Final

from outcomeeng.distribution.orchestration import (
    CATALOG_PATHS,
    CLAUDE_DIST_PLUGINS_DIR,
    SOURCE_PLUGINS_DIR,
)
from outcomeeng.validation.audit_artifacts import check_audit_artifact_contract

# Paths to both marketplace catalogs, relative to the repo root.
CATALOGS = CATALOG_PATHS
CATALOG_PLUGINS_FIELD: Final = "plugins"
PLUGIN_NAME_FIELD: Final = "name"
PLUGIN_VERSION_FIELD: Final = "version"
CLAUDE_PLUGIN_MANIFEST_PATH: Final = ".claude-plugin/plugin.json"
CODEX_PLUGIN_MANIFEST_PATH: Final = ".codex-plugin/plugin.json"
CLAUDE_PLUGIN_VALIDATE_ARGV: Final = ("claude", "plugin", "validate")


def discover_targets(root: Path) -> list[Path]:
    """Discover marketplace root and plugin directories to validate.

    Returns a sorted list of directories that contain
    .claude-plugin/marketplace.json or .claude-plugin/plugin.json.
    """
    targets: list[Path] = []

    # Marketplace root
    if (root / ".claude-plugin" / "marketplace.json").is_file():
        targets.append(root)

    # Built Claude plugin directories are the install targets.
    plugin_candidates = root / CLAUDE_DIST_PLUGINS_DIR
    if not plugin_candidates.is_dir():
        plugin_candidates = root / SOURCE_PLUGINS_DIR
    if plugin_candidates.is_dir():
        for child in sorted(plugin_candidates.iterdir()):
            if child.is_dir() and (child / ".claude-plugin" / "plugin.json").is_file():
                targets.append(child)

    return targets


def _catalog_plugin_names(path: Path) -> set[str]:
    """Return the set of plugin names listed in a marketplace catalog JSON."""
    data = json.loads(path.read_text())
    return {plugin[PLUGIN_NAME_FIELD] for plugin in data.get(CATALOG_PLUGINS_FIELD, [])}


def check_catalog_sync(root: Path) -> list[str]:
    """Report plugins missing from any marketplace catalog.

    Compares the set of plugin directories under ``src/plugins/`` against each
    catalog listed in CATALOGS.  Returns a list of human-readable error
    strings; empty means everything is in sync.
    """
    plugins_dir = root / SOURCE_PLUGINS_DIR
    plugin_dirs: set[str] = (
        {
            child.name
            for child in plugins_dir.iterdir()
            if child.is_dir() and (child / ".claude-plugin" / "plugin.json").is_file()
        }
        if plugins_dir.is_dir()
        else set()
    )

    errors: list[str] = []
    for surface, rel_path in CATALOGS.items():
        catalog_path = root / rel_path
        if not catalog_path.is_file():
            errors.append(f"catalog missing: {rel_path}")
            continue
        registered = _catalog_plugin_names(catalog_path)
        for name in sorted(plugin_dirs - registered):
            errors.append(f"{name} not in {surface} catalog ({rel_path})")
        for name in sorted(registered - plugin_dirs):
            errors.append(
                f"{name} in {surface} catalog but has no src/plugins/{name}/ directory"
            )

    return errors


def check_manifest_parity(root: Path) -> list[str]:
    """Report plugin directories whose Claude and Codex manifests disagree on version.

    For each plugin under ``src/plugins/`` that ships both
    ``.claude-plugin/plugin.json`` and ``.codex-plugin/plugin.json``, asserts
    that the ``version`` field matches across the two manifests. Plugins that
    ship only the Claude manifest are skipped — Codex coverage is optional.

    Returns a list of human-readable error strings; empty means parity holds.
    """
    plugins_dir = root / SOURCE_PLUGINS_DIR
    if not plugins_dir.is_dir():
        return []

    errors: list[str] = []
    for child in sorted(plugins_dir.iterdir()):
        if not child.is_dir():
            continue
        claude_manifest = child / ".claude-plugin" / "plugin.json"
        codex_manifest = child / ".codex-plugin" / "plugin.json"
        if not claude_manifest.is_file() or not codex_manifest.is_file():
            continue

        claude_data = json.loads(claude_manifest.read_text())
        codex_data = json.loads(codex_manifest.read_text())
        claude_version = claude_data.get(PLUGIN_VERSION_FIELD)
        codex_version = codex_data.get(PLUGIN_VERSION_FIELD)

        if claude_version is None:
            errors.append(
                f"{child.name}: {CLAUDE_PLUGIN_MANIFEST_PATH} "
                f"missing {PLUGIN_VERSION_FIELD} field"
            )
        if codex_version is None:
            errors.append(
                f"{child.name}: {CODEX_PLUGIN_MANIFEST_PATH} "
                f"missing {PLUGIN_VERSION_FIELD} field"
            )
        if claude_version is None or codex_version is None:
            continue

        if claude_version != codex_version:
            errors.append(
                f"{child.name}: version drift — "
                f"{CLAUDE_PLUGIN_MANIFEST_PATH}={claude_version}, "
                f"{CODEX_PLUGIN_MANIFEST_PATH}={codex_version}"
            )

    return errors


# Wall-clock bound for a single `claude plugin validate` invocation. Tests import this
# constant rather than restating the value.
VALIDATE_TIMEOUT_SECONDS: Final = 60.0

# Conventional exit code for a process the runner had to terminate on timeout.
_TIMEOUT_RETURNCODE: Final = 124


def run_validate(
    cmd: list[str], *, timeout: float = VALIDATE_TIMEOUT_SECONDS
) -> subprocess.CompletedProcess[str]:
    """Run a validation command with a bounded, capture-safe wait.

    Output is captured to temporary files rather than inherited pipes: a short-lived
    descendant of the validated process can hold a pipe's write end open after the
    process itself has exited, and a pipe-draining read would then block on EOF without
    bound. Writing to files makes the wait depend only on the invoked process exiting.
    The child runs in its own process group with stdin detached; if it does not exit
    within ``timeout`` the whole group is signalled with SIGKILL — the one signal a child
    cannot ignore — and a non-zero result naming the command is returned.
    """
    with (
        tempfile.TemporaryFile() as out,
        tempfile.TemporaryFile() as err,
    ):
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=err,
            start_new_session=True,
        )
        try:
            returncode = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_process_group(proc)
            proc.wait()
            stdout, stderr = _read_captures(out, err)
            note = f"timed out after {timeout}s: {' '.join(cmd)}"
            stderr = f"{stderr}\n{note}".strip()
            return subprocess.CompletedProcess(cmd, _TIMEOUT_RETURNCODE, stdout, stderr)
        stdout, stderr = _read_captures(out, err)
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)


def _kill_process_group(proc: subprocess.Popen[bytes]) -> None:
    """SIGKILL the process group led by ``proc`` (created with start_new_session)."""
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        return
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return


def _read_captures(out: IO[bytes], err: IO[bytes]) -> tuple[str, str]:
    """Rewind and decode the captured stdout and stderr temp files."""
    out.seek(0)
    err.seek(0)
    return out.read().decode(errors="replace"), err.read().decode(errors="replace")


def _validate_target(
    target: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> tuple[Path, subprocess.CompletedProcess[str]]:
    cmd = [*CLAUDE_PLUGIN_VALIDATE_ARGV, str(target)]
    return target, runner(cmd)


def _validate_targets(
    targets: list[Path],
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> list[tuple[Path, str]]:
    failures: list[tuple[Path, str]] = []
    with ThreadPoolExecutor(max_workers=len(targets)) as pool:
        futures = {
            pool.submit(_validate_target, target, runner): target for target in targets
        }
        for future in as_completed(futures):
            target, result = future.result()
            if result.returncode != 0:
                failures.append((target, result.stderr or result.stdout))
            else:
                print(result.stdout, end="")
    return failures


def _report_validation_failures(failures: list[tuple[Path, str]]) -> None:
    for target, output in failures:
        print(f"error: validation failed for {target}", file=sys.stderr)
        if output.strip():
            print(f"  {output.strip()}", file=sys.stderr)


def _report_contract_errors(prefix: str, errors: list[str]) -> None:
    for message in errors:
        print(f"error: {prefix}: {message}", file=sys.stderr)


def main(
    argv: list[str] | None = None,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = run_validate,
) -> int:
    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]) if args else Path(".")

    targets = discover_targets(root)
    if not targets:
        print(
            f"error: no marketplace or plugins found under {root}",
            file=sys.stderr,
        )
        return 1

    failures = _validate_targets(targets, runner)
    _report_validation_failures(failures)

    sync_errors = check_catalog_sync(root)
    _report_contract_errors("catalog sync", sync_errors)

    parity_errors = check_manifest_parity(root)
    _report_contract_errors("manifest parity", parity_errors)

    audit_artifact_errors = check_audit_artifact_contract(root)
    _report_contract_errors("audit artifacts", audit_artifact_errors)

    return (
        1 if (failures or sync_errors or parity_errors or audit_artifact_errors) else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
