"""Resource harnesses and recording collaborators for marketplace installation."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.installation import (
    Agent,
    CLAUDE_CATALOG_PATH,
    CODEX_AGENTS_PATH,
    CODEX_CATALOG_PATH,
    CODEX_CONFIG_PATH,
    CommandResult,
    InstallationCommand,
    InstallationFailure,
    InstallationPlan,
    Operation,
    build_installation_plan,
    installed_plugin_names,
)

UNOWNED_AGENT_FILENAME = "developer-owned.toml"
UNOWNED_AGENT_CONTENT = 'name = "developer-owned"\n'
REQUIRED_BINARIES: tuple[str, ...] = ("just", "claude", "codex")


@dataclass(frozen=True)
class PlanObservation:
    """Catalog and command observations from one repository plan."""

    plan: InstallationPlan
    claude_catalog: bytes
    codex_catalog: bytes


@dataclass(frozen=True)
class FailureObservation:
    """The attempted prefix and structured first failure."""

    plan: InstallationPlan
    attempted: tuple[InstallationCommand, ...]
    failure: InstallationFailure


@dataclass(frozen=True)
class ConfigObservation:
    """Plans and config bytes around a repository-config mutation."""

    before: InstallationPlan
    after: InstallationPlan
    config_bytes: bytes


@dataclass(frozen=True)
class RealInstallationObservation:
    """Real command, plugin-state, and placement observations across two runs."""

    first_exit_code: int
    second_exit_code: int
    claude_plugins_first: frozenset[str]
    claude_plugins_second: frozenset[str]
    codex_plugins_first: frozenset[str]
    codex_plugins_second: frozenset[str]
    claude_catalog: bytes
    codex_catalog: bytes
    placed_first: tuple[tuple[str, bytes], ...]
    placed_second: tuple[tuple[str, bytes], ...]
    unowned_initial: bytes
    unowned_first: bytes
    unowned_second: bytes
    first_stdout: str
    first_stderr: str
    second_stdout: str
    second_stderr: str


@dataclass
class RecordingRunner:
    """Installation runner that records commands and fails one selected operation."""

    failed_operation: Operation
    calls: list[InstallationCommand] = field(default_factory=list)

    def __call__(self, command: InstallationCommand) -> CommandResult:
        self.calls.append(command)
        exit_code = 1 if command.operation is self.failed_operation else 0
        return CommandResult(
            argv=command.argv,
            exit_code=exit_code,
            stdout="",
            stderr=command.operation.value if exit_code else "",
        )


def repository_root() -> Path:
    """Return the checkout containing this installed harness package."""
    return Path(__file__).resolve().parents[2]


def observe_repository_plan() -> PlanObservation:
    """Build a plan in a temporary state root and expose catalog observations."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        plan = build_installation_plan(
            checkout,
            Path(temporary_directory),
            os.environ,
        )
    return PlanObservation(
        plan=plan,
        claude_catalog=(checkout / CLAUDE_CATALOG_PATH).read_bytes(),
        codex_catalog=(checkout / CODEX_CATALOG_PATH).read_bytes(),
    )


def observe_first_failure() -> FailureObservation:
    """Fail the first plugin installation and expose the attempted prefix."""
    from outcomeeng.distribution.installation import execute_installation

    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        plan = build_installation_plan(checkout, Path(temporary_directory), os.environ)
        runner = RecordingRunner(failed_operation=Operation.PLUGIN_INSTALL)
        try:
            execute_installation(plan, runner)
        except InstallationFailure as failure:
            return FailureObservation(
                plan=plan,
                attempted=tuple(runner.calls),
                failure=failure,
            )
    raise RuntimeError("installation completed without the scripted failure")


def observe_codex_config_independence() -> ConfigObservation:
    """Build plans before and after adding conflicting repository config bytes."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        state = temporary_root / "state"
        before = build_installation_plan(mirror, state, os.environ)
        config = mirror / CODEX_CONFIG_PATH
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("[plugins]\nenabled = false\n", encoding="utf-8")
        after = build_installation_plan(mirror, state, os.environ)
        config_bytes = config.read_bytes()
    return ConfigObservation(before=before, after=after, config_bytes=config_bytes)


def observe_real_installation() -> RealInstallationObservation:
    """Run the public recipe twice with real agent CLIs in one disposable home."""
    checkout = repository_root()
    _require_binaries(REQUIRED_BINARIES)
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        state = temporary_root / "state"
        _mirror_installation_inputs(checkout, mirror)
        unowned = mirror / CODEX_AGENTS_PATH / UNOWNED_AGENT_FILENAME
        unowned.parent.mkdir(parents=True, exist_ok=True)
        unowned.write_text(UNOWNED_AGENT_CONTENT, encoding="utf-8")
        unowned_initial = unowned.read_bytes()
        plan = build_installation_plan(mirror, state, os.environ)
        environment = dict(plan.commands[0].environment)
        first = _run_recipe(checkout, mirror, state, environment)
        claude_first = _run_listing(Agent.CLAUDE, mirror, environment)
        codex_first = _run_listing(Agent.CODEX, mirror, environment)
        placed_first = _agent_snapshot(mirror)
        unowned_first = unowned.read_bytes()
        second = _run_recipe(checkout, mirror, state, environment)
        claude_second = _run_listing(Agent.CLAUDE, mirror, environment)
        codex_second = _run_listing(Agent.CODEX, mirror, environment)
        placed_second = _agent_snapshot(mirror)
        unowned_second = unowned.read_bytes()
        claude_catalog = (mirror / CLAUDE_CATALOG_PATH).read_bytes()
        codex_catalog = (mirror / CODEX_CATALOG_PATH).read_bytes()
    return RealInstallationObservation(
        first_exit_code=first.returncode,
        second_exit_code=second.returncode,
        claude_plugins_first=installed_plugin_names(Agent.CLAUDE, claude_first.stdout),
        claude_plugins_second=installed_plugin_names(
            Agent.CLAUDE, claude_second.stdout
        ),
        codex_plugins_first=installed_plugin_names(Agent.CODEX, codex_first.stdout),
        codex_plugins_second=installed_plugin_names(Agent.CODEX, codex_second.stdout),
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
        placed_first=placed_first,
        placed_second=placed_second,
        unowned_initial=unowned_initial,
        unowned_first=unowned_first,
        unowned_second=unowned_second,
        first_stdout=first.stdout,
        first_stderr=first.stderr,
        second_stdout=second.stdout,
        second_stderr=second.stderr,
    )


def _mirror_installation_inputs(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative_path in (
        CODEX_CATALOG_PATH,
        CLAUDE_CATALOG_PATH,
    ):
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative_path, target)
    shutil.copytree(source / "dist/codex", destination / "dist/codex")
    shutil.copytree(source / "dist/claude", destination / "dist/claude")


def _require_binaries(names: Sequence[str]) -> None:
    missing = tuple(name for name in names if shutil.which(name) is None)
    if missing:
        raise RuntimeError(f"required installation binaries are unavailable: {missing}")


def _run_recipe(
    source_checkout: Path,
    mirror: Path,
    state: Path,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (
            "just",
            "install-marketplace",
            "--checkout",
            str(mirror),
            "--state-root",
            str(state),
            "--json",
        ),
        cwd=source_checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )


def _run_listing(
    agent: Agent,
    checkout: Path,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    argv = (
        ("claude", "plugin", "list", "--json")
        if agent is Agent.CLAUDE
        else ("codex", "plugin", "list", "--json")
    )
    result = subprocess.run(
        argv,
        cwd=checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{agent.value} plugin listing failed with exit {result.returncode}: "
            f"{result.stderr}"
        )
    return result


def _agent_snapshot(checkout: Path) -> tuple[tuple[str, bytes], ...]:
    directory = checkout / CODEX_AGENTS_PATH
    return tuple((path.name, path.read_bytes()) for path in sorted(directory.glob("*")))


__all__ = [
    "ConfigObservation",
    "FailureObservation",
    "PlanObservation",
    "RealInstallationObservation",
    "RecordingRunner",
    "observe_codex_config_independence",
    "observe_first_failure",
    "observe_real_installation",
    "observe_repository_plan",
]
