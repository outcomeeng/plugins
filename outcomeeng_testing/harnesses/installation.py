"""Resource harnesses and recording collaborators for marketplace installation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.installation import (
    Agent,
    CANONICAL_MARKETPLACE_SOURCE,
    CLAUDE_CATALOG_PATH,
    CLAUDE_PROJECT_SETTINGS_PATH,
    CODEX_AGENTS_PATH,
    CODEX_CATALOG_PATH,
    CODEX_CONFIG_PATH,
    CODEX_HOME_ENV,
    CODEX_SQLITE_HOME_ENV,
    CommandResult,
    HOME_ENV,
    InstallationCommand,
    InstallationFailure,
    InstallationPlan,
    InstallationReport,
    MARKETPLACE_NAME,
    Operation,
    PersistentPreflight,
    STATE_ENV_NAMES,
    build_isolated_installation_plan,
    build_persistent_installation_plan,
    build_persistent_preflight,
    execute_persistent_installation,
)

UNOWNED_AGENT_FILENAME = "developer-owned.toml"
UNOWNED_AGENT_CONTENT = 'name = "developer-owned"\n'
REQUIRED_BINARIES: tuple[str, ...] = ("just", "claude", "codex")
CANONICAL_CODEX_SOURCE = "https://github.com/outcomeeng/plugins.git"
_CLAUDE_PLUGIN_ID_FIELD = "id"
_CLAUDE_PLUGIN_ENABLED_FIELD = "enabled"
_CODEX_PLUGIN_ENTRIES_FIELD = "installed"
_CODEX_PLUGIN_ID_FIELD = "pluginId"
_CODEX_PLUGIN_ENABLED_FIELD = "enabled"


@dataclass(frozen=True)
class PlanObservation:
    """Catalog and command observations from one isolated plan."""

    plan: InstallationPlan
    claude_catalog: bytes
    codex_catalog: bytes
    ambient_state_values: tuple[str, ...]


@dataclass(frozen=True)
class PersistentPlanObservation:
    """Catalog, preflight, and command observations from a persistent plan."""

    preflight: PersistentPreflight
    plan: InstallationPlan
    claude_catalog: bytes
    codex_catalog: bytes


@dataclass(frozen=True)
class PersistentExecutionObservation:
    """Preflight, report, and calls from one controlled persistent execution."""

    preflight: PersistentPreflight
    report: InstallationReport
    attempted: tuple[InstallationCommand, ...]
    claude_catalog: bytes
    codex_catalog: bytes


@dataclass(frozen=True)
class FailureObservation:
    """The attempted prefix and structured first failure."""

    plan: InstallationPlan
    attempted: tuple[InstallationCommand, ...]
    failure: InstallationFailure


@dataclass(frozen=True)
class CollisionObservation:
    """A user-scope collision and the commands attempted before rejection."""

    settings_path: Path
    error: str
    attempted: tuple[InstallationCommand, ...]


@dataclass(frozen=True)
class ConfigObservation:
    """Plans and config bytes around a repository-config mutation."""

    before: InstallationPlan
    after: InstallationPlan
    persistent_before: InstallationPlan
    persistent_after: InstallationPlan
    config_bytes: bytes


@dataclass(frozen=True)
class VerificationRecipeObservation:
    """Dry-run output from the public isolated-verification recipe."""

    exit_code: int
    stdout: str
    stderr: str


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
    claude_registration_target: str
    codex_registration_target: str
    state_roots: tuple[Path, ...]
    placed_initial: tuple[tuple[str, bytes], ...]
    placed_first: tuple[tuple[str, bytes], ...]
    placed_second: tuple[tuple[str, bytes], ...]
    unowned_initial: bytes
    unowned_first: bytes
    unowned_second: bytes
    ownership_prefixes: tuple[str, ...]
    persistent_initial: tuple[tuple[str, bytes], ...]
    persistent_first: tuple[tuple[str, bytes], ...]
    persistent_second: tuple[tuple[str, bytes], ...]
    first_stdout: str
    first_stderr: str
    second_stdout: str
    second_stderr: str


@dataclass
class RecordingRunner:
    """Installation runner that records commands and can fail one operation."""

    failed_operation: Operation | None = None
    calls: list[InstallationCommand] = field(default_factory=list)

    def __call__(self, command: InstallationCommand) -> CommandResult:
        self.calls.append(command)
        exit_code = 1 if command.operation is self.failed_operation else 0
        stdout = _codex_marketplace_payload(CANONICAL_CODEX_SOURCE)
        if command.operation is not Operation.MARKETPLACE_INSPECT:
            stdout = ""
        return CommandResult(
            argv=command.argv,
            exit_code=exit_code,
            stdout=stdout,
            stderr=command.operation.value if exit_code else "",
        )


def repository_root() -> Path:
    """Return the checkout containing this installed harness package."""
    return Path(__file__).resolve().parents[2]


def observe_repository_plan() -> PlanObservation:
    """Build an isolated plan from immutable pre-execution catalog bytes."""
    checkout = repository_root()
    claude_catalog = (checkout / CLAUDE_CATALOG_PATH).read_bytes()
    codex_catalog = (checkout / CODEX_CATALOG_PATH).read_bytes()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        ambient_environment = _persistent_environment(
            temporary_root / "developer-state"
        )
        plan = build_isolated_installation_plan(
            checkout,
            temporary_root / "isolated-state",
            ambient_environment,
        )
        ambient_state_values = tuple(
            ambient_environment[name] for name in STATE_ENV_NAMES
        )
    return PlanObservation(
        plan=plan,
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
        ambient_state_values=ambient_state_values,
    )


def observe_persistent_plan(
    *,
    claude_repository: str = CANONICAL_MARKETPLACE_SOURCE,
    codex_source: str = CANONICAL_CODEX_SOURCE,
) -> PersistentPlanObservation:
    """Build a persistent plan in caller-selected temporary homes."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, claude_repository)
        environment = _persistent_environment(temporary_root)
        claude_catalog = (mirror / CLAUDE_CATALOG_PATH).read_bytes()
        codex_catalog = (mirror / CODEX_CATALOG_PATH).read_bytes()
        preflight = build_persistent_preflight(mirror, environment)
        plan = build_persistent_installation_plan(
            preflight,
            _codex_marketplace_payload(codex_source),
        )
    return PersistentPlanObservation(
        preflight=preflight,
        plan=plan,
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
    )


def observe_persistent_execution() -> PersistentExecutionObservation:
    """Execute the persistent path through a recording command collaborator."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        claude_catalog = (mirror / CLAUDE_CATALOG_PATH).read_bytes()
        codex_catalog = (mirror / CODEX_CATALOG_PATH).read_bytes()
        preflight = build_persistent_preflight(mirror, environment)
        runner = RecordingRunner()
        report = execute_persistent_installation(mirror, environment, runner)
    return PersistentExecutionObservation(
        preflight=preflight,
        report=report,
        attempted=tuple(runner.calls),
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
    )


def observe_claude_user_collision() -> CollisionObservation:
    """Expose user-scope collision rejection before command execution."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        settings_path = temporary_root / "claude" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            json.dumps(_claude_settings(CANONICAL_MARKETPLACE_SOURCE)),
            encoding="utf-8",
        )
        runner = RecordingRunner()
        try:
            execute_persistent_installation(mirror, environment, runner)
        except ValueError as error:
            return CollisionObservation(
                settings_path=settings_path,
                error=str(error),
                attempted=tuple(runner.calls),
            )
    raise RuntimeError("persistent installation accepted a user-scope collision")


def observe_missing_codex_home() -> str:
    """Expose rejection when persistent state has no selected Codex home."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        del environment[CODEX_HOME_ENV]
        try:
            build_persistent_preflight(mirror, environment)
        except ValueError as error:
            return str(error)
    raise RuntimeError("persistent installation accepted a missing CODEX_HOME")


def observe_first_failure() -> FailureObservation:
    """Fail the first plugin installation and expose the attempted prefix."""
    from outcomeeng.distribution.installation import execute_installation

    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        plan = build_isolated_installation_plan(
            checkout,
            Path(temporary_directory),
            os.environ,
        )
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
    """Build isolated and persistent plans around repository config bytes."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        state = temporary_root / "state"
        before = build_isolated_installation_plan(mirror, state, os.environ)
        environment = _persistent_environment(temporary_root / "persistent")
        persistent_before = execute_persistent_installation(
            mirror, environment, RecordingRunner()
        ).plan
        config = mirror / CODEX_CONFIG_PATH
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text("[plugins]\nenabled = false\n", encoding="utf-8")
        after = build_isolated_installation_plan(mirror, state, os.environ)
        persistent_after = execute_persistent_installation(
            mirror, environment, RecordingRunner()
        ).plan
        config_bytes = config.read_bytes()
    return ConfigObservation(
        before=before,
        after=after,
        persistent_before=persistent_before,
        persistent_after=persistent_after,
        config_bytes=config_bytes,
    )


def observe_verification_recipe() -> VerificationRecipeObservation:
    """Render the verification recipe without running its L2 test."""
    result = subprocess.run(
        ("just", "--dry-run", "verify-marketplace-installation"),
        cwd=repository_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    return VerificationRecipeObservation(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def observe_real_installation() -> RealInstallationObservation:
    """Run isolated installation twice with real agent CLIs."""
    checkout = repository_root()
    _require_binaries(REQUIRED_BINARIES)
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        state = temporary_root / "state"
        _mirror_installation_inputs(checkout, mirror)
        claude_catalog = (mirror / CLAUDE_CATALOG_PATH).read_bytes()
        codex_catalog = (mirror / CODEX_CATALOG_PATH).read_bytes()
        ownership_prefixes = _placement_prefixes(mirror)
        persistent_root = temporary_root / "persistent"
        persistent_environment = _persistent_environment(persistent_root)
        _seed_persistent_state(persistent_root)
        persistent_initial = _tree_snapshot(persistent_root)
        unowned = mirror / CODEX_AGENTS_PATH / UNOWNED_AGENT_FILENAME
        unowned.parent.mkdir(parents=True, exist_ok=True)
        unowned.write_text(UNOWNED_AGENT_CONTENT, encoding="utf-8")
        unowned_initial = unowned.read_bytes()
        placed_initial = _agent_snapshot(mirror)
        plan = build_isolated_installation_plan(mirror, state, persistent_environment)
        environment = dict(plan.commands[0].environment)
        claude_target = _registration_target(plan, Agent.CLAUDE)
        codex_target = _registration_target(plan, Agent.CODEX)
        state_roots = _state_roots(plan)
        first = _run_recipe(checkout, mirror, state, environment)
        claude_first = _run_listing(Agent.CLAUDE, mirror, environment)
        codex_first = _run_listing(Agent.CODEX, mirror, environment)
        placed_first = _agent_snapshot(mirror)
        unowned_first = unowned.read_bytes()
        persistent_first = _tree_snapshot(persistent_root)
        second = _run_recipe(checkout, mirror, state, environment)
        claude_second = _run_listing(Agent.CLAUDE, mirror, environment)
        codex_second = _run_listing(Agent.CODEX, mirror, environment)
        placed_second = _agent_snapshot(mirror)
        unowned_second = unowned.read_bytes()
        persistent_second = _tree_snapshot(persistent_root)
    return RealInstallationObservation(
        first_exit_code=first.returncode,
        second_exit_code=second.returncode,
        claude_plugins_first=_listed_plugin_names(Agent.CLAUDE, claude_first.stdout),
        claude_plugins_second=_listed_plugin_names(Agent.CLAUDE, claude_second.stdout),
        codex_plugins_first=_listed_plugin_names(Agent.CODEX, codex_first.stdout),
        codex_plugins_second=_listed_plugin_names(Agent.CODEX, codex_second.stdout),
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
        claude_registration_target=claude_target,
        codex_registration_target=codex_target,
        state_roots=state_roots,
        placed_initial=placed_initial,
        placed_first=placed_first,
        placed_second=placed_second,
        unowned_initial=unowned_initial,
        unowned_first=unowned_first,
        unowned_second=unowned_second,
        ownership_prefixes=ownership_prefixes,
        persistent_initial=persistent_initial,
        persistent_first=persistent_first,
        persistent_second=persistent_second,
        first_stdout=first.stdout,
        first_stderr=first.stderr,
        second_stdout=second.stdout,
        second_stderr=second.stderr,
    )


def _listed_plugin_names(agent: Agent, payload: str) -> frozenset[str]:
    """Read installed and enabled plugin names from a real agent CLI listing."""
    try:
        document = json.loads(payload)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid {agent.value} plugin listing: {error}") from error
    entries: object = document
    if agent is Agent.CODEX:
        if not isinstance(document, dict):
            raise RuntimeError("Codex plugin listing must be a JSON object")
        entries = document.get(_CODEX_PLUGIN_ENTRIES_FIELD)
    if not isinstance(entries, list):
        raise RuntimeError(f"{agent.value} plugin listing must contain an array")
    plugin_id_field = (
        _CLAUDE_PLUGIN_ID_FIELD if agent is Agent.CLAUDE else _CODEX_PLUGIN_ID_FIELD
    )
    plugin_enabled_field = (
        _CLAUDE_PLUGIN_ENABLED_FIELD
        if agent is Agent.CLAUDE
        else _CODEX_PLUGIN_ENABLED_FIELD
    )
    marketplace_suffix = f"@{MARKETPLACE_NAME}"
    names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError(f"{agent.value} plugin listing contains a non-object")
        plugin_id = entry.get(plugin_id_field)
        enabled = entry.get(plugin_enabled_field)
        if not isinstance(plugin_id, str) or not isinstance(enabled, bool):
            raise RuntimeError(
                f"{agent.value} plugin listing entry lacks typed identity or state"
            )
        if enabled and plugin_id.endswith(marketplace_suffix):
            names.add(plugin_id.removesuffix(marketplace_suffix))
    return frozenset(names)


def _mirror_installation_inputs(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative_path in (CODEX_CATALOG_PATH, CLAUDE_CATALOG_PATH):
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative_path, target)
    shutil.copytree(source / "dist/codex", destination / "dist/codex")
    shutil.copytree(source / "dist/claude", destination / "dist/claude")


def _write_project_marketplace(checkout: Path, repository: str) -> None:
    settings = checkout / CLAUDE_PROJECT_SETTINGS_PATH
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(_claude_settings(repository)), encoding="utf-8")


def _claude_settings(repository: str) -> dict[str, object]:
    source: dict[str, str]
    if repository == CANONICAL_MARKETPLACE_SOURCE:
        source = {"source": "github", "repo": repository}
    else:
        source = {"source": "directory", "path": repository}
    return {
        "extraKnownMarketplaces": {
            "outcomeeng": {
                "source": source,
            }
        }
    }


def _persistent_environment(root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            HOME_ENV: str(root / "home"),
            "CLAUDE_CONFIG_DIR": str(root / "claude"),
            CODEX_HOME_ENV: str(root / "codex"),
            CODEX_SQLITE_HOME_ENV: str(root / "codex-sqlite"),
        }
    )
    return environment


def _codex_marketplace_payload(source: str) -> str:
    return json.dumps(
        {
            "marketplaces": [
                {
                    "name": "outcomeeng",
                    "marketplaceSource": {
                        "sourceType": "git" if source.startswith("http") else "local",
                        "source": source,
                    },
                }
            ]
        }
    )


def _registration_target(plan: InstallationPlan, agent: Agent) -> str:
    command = next(
        command
        for command in plan.commands
        if command.agent is agent and command.operation is Operation.MARKETPLACE_ADD
    )
    return command.argv[4]


def _state_roots(plan: InstallationPlan) -> tuple[Path, ...]:
    roots = plan.roots
    if roots.state is None or roots.codex_sqlite_home is None:
        raise RuntimeError("real installation plan is not isolated")
    return (
        roots.home,
        roots.claude_config,
        roots.codex_home,
        roots.codex_sqlite_home,
    )


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


def _placement_prefixes(checkout: Path) -> tuple[str, ...]:
    prefixes = []
    manifests = (checkout / "dist/codex").glob("*/skills/*/agents/placement.json")
    for manifest in sorted(manifests):
        document = json.loads(manifest.read_text(encoding="utf-8"))
        if document.get("directory") == str(CODEX_AGENTS_PATH):
            prefixes.append(str(document["prefix"]))
    return tuple(prefixes)


def _seed_persistent_state(root: Path) -> None:
    for relative_path in (
        Path("home/.claude/settings.json"),
        Path("claude/plugins/installed.json"),
        Path("codex/plugins/installed.json"),
        Path("codex-sqlite/state.db"),
        Path("checkout/.codex/agents/developer.toml"),
    ):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(relative_path), encoding="utf-8")


def _tree_snapshot(root: Path) -> tuple[tuple[str, bytes], ...]:
    return tuple(
        (str(path.relative_to(root)), path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


__all__ = [
    "CollisionObservation",
    "ConfigObservation",
    "FailureObservation",
    "PersistentExecutionObservation",
    "PersistentPlanObservation",
    "PlanObservation",
    "RealInstallationObservation",
    "RecordingRunner",
    "VerificationRecipeObservation",
    "observe_claude_user_collision",
    "observe_codex_config_independence",
    "observe_first_failure",
    "observe_missing_codex_home",
    "observe_persistent_execution",
    "observe_persistent_plan",
    "observe_real_installation",
    "observe_repository_plan",
    "observe_verification_recipe",
]
