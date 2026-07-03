"""Marketplace sync orchestration.

Reconciles local runtime marketplace configuration, refreshes the local Claude
marketplace, and re-validates installed plugins when plugin distribution paths
changed since a reference commit or configuration repair changed runtime state.

The module's contract:

- `REQUIRED_TOOLS` names the external binaries the orchestration shells out to.
- `DISTRIBUTION_PATHS` names the repository paths whose change drives a sync.
- `STEPS` is the ordered tuple of named subprocess calls executed when a refresh runs.
- `StepRunner`, `ToolProbe`, `ChangeProbe`, and `ConfigRepairer` Protocols describe
  the injected side-effecting boundaries; `sync()` accepts them as keyword arguments.
- `main()` wires real subprocess, `shutil.which`, and `git diff` adapters.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from outcomeeng.distribution.codex_cache import (
    CodexCliInstalled,
    InstalledSetError,
    codex_cache_topology_errors,
    default_cache_root,
)
from outcomeeng.distribution.marketplace_sources import (
    DEFAULT_MARKETPLACE,
    MarketplaceSourceError,
    ensure_local_marketplace_sources,
)

REQUIRED_TOOLS: tuple[str, ...] = ("claude", "codex", "uv")

DISTRIBUTION_PATHS: tuple[str, ...] = (
    "src",
    "dist",
    ".claude-plugin",
    ".agents/plugins",
    "outcomeeng/distribution/agents.py",
)
SYNC_LOCK_FILENAME = ".sync-marketplace.lock"
SYNC_PENDING_FILENAME = ".sync-marketplace.pending"
SYNC_ALREADY_RUNNING_MESSAGE = (
    "Marketplace refresh already running; recorded pending sync; exiting 0"
)
TOPOLOGY_CHECK_FAILED_PREFIX = "Codex cache topology check failed"
LOCK_OWNER_PID_FIELD = "pid"
LOCK_OWNER_IDENTITY_FIELD = "identity"
PROCESS_IDENTITY_TIMEOUT_SECONDS = 2.0


@dataclass(frozen=True)
class SyncStep:
    """A named orchestration step with its argv tuple."""

    name: str
    argv: tuple[str, ...]


STEPS: tuple[SyncStep, ...] = (
    SyncStep(
        name="claude_marketplace_update",
        argv=("claude", "plugin", "marketplace", "update", "outcomeeng"),
    ),
    SyncStep(
        name="codex_local_refresh",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.distribution.codex_cache",
            "outcomeeng",
        ),
    ),
    SyncStep(
        name="codex_agent_install",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.distribution.agents",
            "install",
        ),
    ),
    SyncStep(
        name="install_validate",
        argv=("uv", "run", "python", "-m", "outcomeeng.validation.install"),
    ),
    SyncStep(
        name="installed_check",
        argv=("just", "check-installed"),
    ),
    SyncStep(
        name="codex_local_refresh_final",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.distribution.codex_cache",
            "outcomeeng",
            "--strict-current-cache",
        ),
    ),
)


class StepRunner(Protocol):
    """Invokes one orchestration step. Returns the step's exit code."""

    def __call__(self, argv: Sequence[str]) -> int: ...


class ToolProbe(Protocol):
    """Returns True when `name` resolves to an executable on PATH."""

    def __call__(self, name: str) -> bool: ...


class ChangeProbe(Protocol):
    """Returns True when distribution paths changed since `base_ref`.

    When `base_ref` is None or empty, no diff baseline exists and the probe
    is not consulted; orchestration proceeds unconditionally.
    """

    def __call__(self, base_ref: str) -> bool: ...


class ConfigRepairer(Protocol):
    """Reconciles runtime marketplace source config; returns True if changed."""

    def __call__(self) -> bool: ...


class TopologyHealthProbe(Protocol):
    """Returns Codex cache topology errors for installed marketplace plugins."""

    def __call__(self) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class SingleFlightClaim:
    """Result of attempting to own one marketplace refresh sequence."""

    acquired: bool
    pending_recorded: bool = False
    detail: str = ""


class SingleFlight(Protocol):
    """Coordinates concurrent sync invocations around one refresh sequence."""

    def acquire(self) -> SingleFlightClaim: ...

    def release(self) -> None: ...


ProcessExists = Callable[[int], bool]
ProcessIdentity = Callable[[int], str | None]


@dataclass(frozen=True)
class _LockOwner:
    pid: int
    identity: str


@dataclass(frozen=True)
class _FileSingleFlight:
    """File-backed single-flight guard stored in the Codex cache directory."""

    state_dir: Path
    process_exists: ProcessExists = lambda pid: _process_exists(pid)
    process_identity: ProcessIdentity = lambda pid: _process_identity(pid)

    @property
    def lock_path(self) -> Path:
        return self.state_dir / SYNC_LOCK_FILENAME

    @property
    def pending_path(self) -> Path:
        return self.state_dir / SYNC_PENDING_FILENAME

    def acquire(self) -> SingleFlightClaim:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        current_owner = self._current_owner()
        lock_body = _serialize_lock_owner(current_owner)
        for _attempt in range(2):
            try:
                fd = os.open(
                    self.lock_path,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    0o644,
                )
            except FileExistsError:
                lock_owner = self._read_lock_owner()
                if lock_owner is not None and self._owner_is_active(lock_owner):
                    self.pending_path.write_text(lock_body, encoding="utf-8")
                    return SingleFlightClaim(
                        acquired=False,
                        pending_recorded=True,
                        detail=f"pid {lock_owner.pid} owns active repair",
                    )
                try:
                    self.lock_path.unlink()
                except FileNotFoundError:
                    pass
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
                lock_file.write(lock_body)
            return SingleFlightClaim(
                acquired=True,
                detail=f"pid {current_owner.pid} owns active repair",
            )
        self.pending_path.write_text(lock_body, encoding="utf-8")
        return SingleFlightClaim(
            acquired=False,
            pending_recorded=True,
            detail="active repair lock changed during acquisition",
        )

    def release(self) -> None:
        current_owner = self._current_owner()
        if self._read_lock_owner() == current_owner:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass
        try:
            self.pending_path.unlink()
        except FileNotFoundError:
            pass

    def _read_lock_owner(self) -> _LockOwner | None:
        try:
            raw = self.lock_path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return _read_lock_owner_body(raw)

    def _current_owner(self) -> _LockOwner:
        pid = os.getpid()
        identity = self.process_identity(pid)
        if identity is None:
            identity = f"pid:{pid}:identity-unavailable"
        return _LockOwner(pid=pid, identity=identity)

    def _owner_is_active(self, owner: _LockOwner) -> bool:
        if not self.process_exists(owner.pid):
            return False
        return self.process_identity(owner.pid) == owner.identity


def _read_lock_owner_body(raw: str) -> _LockOwner | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    pid = data.get(LOCK_OWNER_PID_FIELD)
    identity = data.get(LOCK_OWNER_IDENTITY_FIELD)
    if not isinstance(pid, int) or not isinstance(identity, str):
        return None
    return _LockOwner(pid=pid, identity=identity)


def _serialize_lock_owner(owner: _LockOwner) -> str:
    return (
        json.dumps(
            {
                LOCK_OWNER_PID_FIELD: owner.pid,
                LOCK_OWNER_IDENTITY_FIELD: owner.identity,
            },
            sort_keys=True,
        )
        + "\n"
    )


def _process_identity(pid: int) -> str | None:
    if not _process_exists(pid):
        return None
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "lstart="],
            check=False,
            capture_output=True,
            text=True,
            timeout=PROCESS_IDENTITY_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    started_at = result.stdout.strip()
    if result.returncode != 0 or not started_at:
        return None
    return f"pid:{pid}:started:{started_at}"


def sync(
    base_ref: str | None,
    *,
    runner: StepRunner | None = None,
    tool_probe: ToolProbe | None = None,
    change_probe: ChangeProbe | None = None,
    config_repairer: ConfigRepairer | None = None,
    topology_probe: TopologyHealthProbe | None = None,
    single_flight: SingleFlight | None = None,
) -> int:
    """Run the marketplace sync orchestration. Returns the process exit code."""
    runner = runner or _real_runner
    tool_probe = tool_probe or _real_tool_probe
    change_probe = change_probe or _real_change_probe
    config_repairer = config_repairer or _real_config_repairer
    topology_probe = topology_probe or _real_topology_probe
    single_flight = single_flight or _real_single_flight()
    for tool in REQUIRED_TOOLS:
        if not tool_probe(tool):
            print(f"Missing required tool: {tool}", file=sys.stderr)
            return 1
    try:
        config_changed = config_repairer()
    except MarketplaceSourceError as exc:
        print(f"Marketplace source configuration failed: {exc}", file=sys.stderr)
        return 1
    distribution_changed = True
    if base_ref:
        distribution_changed = change_probe(base_ref)
    if base_ref and not distribution_changed and not config_changed:
        try:
            topology_errors = topology_probe()
        except InstalledSetError as exc:
            print(f"{TOPOLOGY_CHECK_FAILED_PREFIX}: {exc}", file=sys.stderr)
            return 1
        if not topology_errors:
            print(
                f"No plugin distribution changes since {base_ref}; "
                "runtime marketplace sources already configured; "
                "Codex cache topology healthy; "
                "skipping marketplace refresh",
            )
            return 0
        for error in topology_errors:
            print(f"Codex cache topology invalid: {error}", file=sys.stderr)
        return _run_refresh_sequence(
            runner,
            single_flight,
            reason="Codex cache topology invalid",
        )
    if not base_ref:
        reason = "no base_ref supplied"
    elif distribution_changed:
        reason = "plugin distribution paths changed"
    else:
        reason = "runtime marketplace source configuration changed"
    return _run_refresh_sequence(runner, single_flight, reason=reason)


def _run_refresh_sequence(
    runner: StepRunner,
    single_flight: SingleFlight,
    *,
    reason: str,
) -> int:
    try:
        claim = single_flight.acquire()
    except OSError as exc:
        print(f"Marketplace refresh lock failed: {exc}", file=sys.stderr)
        return 1
    if not claim.acquired:
        print(
            SYNC_ALREADY_RUNNING_MESSAGE,
        )
        if claim.detail:
            print(f"Active sync: {claim.detail}")
        return 0
    refresh_rc = 0
    release_error: OSError | None = None
    print(f"Running marketplace refresh: {reason}")
    try:
        for step in STEPS:
            refresh_rc = runner(step.argv)
            if refresh_rc != 0:
                break
    finally:
        try:
            single_flight.release()
        except OSError as exc:
            release_error = exc
    if release_error is not None:
        print(
            f"Marketplace refresh lock release failed: {release_error}", file=sys.stderr
        )
        return 1
    return refresh_rc


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Parses `base_ref` and runs `sync` with real adapters."""
    args = _build_parser().parse_args(argv)
    return sync(
        args.base_ref or None,
        runner=_real_runner,
        tool_probe=_real_tool_probe,
        change_probe=_real_change_probe,
        config_repairer=_real_config_repairer,
    )


def _real_runner(argv: Sequence[str]) -> int:
    return subprocess.run(list(argv), check=False).returncode


def _real_tool_probe(name: str) -> bool:
    return shutil.which(name) is not None


def _real_change_probe(base_ref: str) -> bool:
    tracked_result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            base_ref,
            "--",
            *DISTRIBUTION_PATHS,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    if tracked_result.stdout.strip():
        return True
    untracked_result = subprocess.run(
        [
            "git",
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            *DISTRIBUTION_PATHS,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(untracked_result.stdout.strip())


def _real_config_repairer() -> bool:
    result = ensure_local_marketplace_sources(
        DEFAULT_MARKETPLACE,
        source_root=_real_source_root(),
    )
    return result.changed


def _real_topology_probe() -> tuple[str, ...]:
    installed_versions = CodexCliInstalled().installed_plugin_versions(
        DEFAULT_MARKETPLACE,
    )
    marketplace_dir = default_cache_root() / DEFAULT_MARKETPLACE
    errors: list[str] = []
    for plugin, version in sorted(installed_versions.items()):
        errors.extend(codex_cache_topology_errors(marketplace_dir, plugin, version))
    return tuple(errors)


def _real_single_flight() -> SingleFlight:
    return _FileSingleFlight(default_cache_root() / DEFAULT_MARKETPLACE)


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _real_source_root() -> Path:
    default_branch = _real_default_branch_name()
    if default_branch is not None:
        worktree_root = _real_worktree_root_for_branch(default_branch)
        if worktree_root is not None:
            return worktree_root
    return _real_git_toplevel()


def _real_default_branch_name() -> str | None:
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return "main"
    ref = result.stdout.strip()
    if not ref:
        return "main"
    return ref.rsplit("/", maxsplit=1)[-1]


def _real_worktree_root_for_branch(branch: str) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return _worktree_path_for_branch(result.stdout, branch)


def _worktree_path_for_branch(porcelain: str, branch: str) -> Path | None:
    current_path: Path | None = None
    branch_ref = f"branch refs/heads/{branch}"
    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line.removeprefix("worktree "))
            continue
        if line == branch_ref and current_path is not None:
            return current_path
        if not line:
            current_path = None
    return None


def _real_git_toplevel() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return Path.cwd()
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip())
    return Path.cwd()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outcomeeng.distribution.sync",
        description=(
            "Refresh local marketplace installs and re-validate installed plugins "
            "when plugin distribution paths changed since base_ref."
        ),
    )
    parser.add_argument(
        "base_ref",
        nargs="?",
        default="",
        help=(
            "Optional git ref to compare against the working tree. "
            "When omitted, all sync steps run unconditionally."
        ),
    )
    return parser


__all__ = [
    "DISTRIBUTION_PATHS",
    "REQUIRED_TOOLS",
    "STEPS",
    "ChangeProbe",
    "ConfigRepairer",
    "SingleFlight",
    "SingleFlightClaim",
    "StepRunner",
    "SyncStep",
    "TopologyHealthProbe",
    "ToolProbe",
    "main",
    "sync",
]


if __name__ == "__main__":
    sys.exit(main())
