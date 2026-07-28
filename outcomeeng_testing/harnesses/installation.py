"""Resource harnesses and recording collaborators for marketplace installation."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

from outcomeeng.distribution.build import (
    PLACEMENT_MANIFEST_DIRECTORY_FIELD,
    PLACEMENT_MANIFEST_FILENAME,
    PLACEMENT_MANIFEST_PREFIX_FIELD,
)
from outcomeeng.distribution.installation import (
    Agent,
    CANONICAL_CODEX_SOURCE,
    CANONICAL_MARKETPLACE_SOURCE,
    CLAUDE_CATALOG_PATH,
    CLAUDE_CONFIG_ENV,
    CLAUDE_ENABLED_PLUGINS_FIELD,
    CLAUDE_PLUGIN_ENABLED_FIELD,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PROJECT_SETTINGS_PATH,
    CODEX_AGENTS_PATH,
    CODEX_CATALOG_PATH,
    CODEX_CONFIG_PATH,
    CODEX_HOME_ENV,
    CODEX_MARKETPLACE_LIST_COMMAND,
    CODEX_PLUGIN_ENABLED_FIELD,
    CODEX_PLUGIN_ENTRIES_FIELD,
    CODEX_PLUGIN_ID_FIELD,
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
    PYTHON_EXECUTABLE,
    SourceAction,
    STATE_ENV_NAMES,
    build_isolated_installation_plan,
    build_persistent_installation_plan,
    build_persistent_preflight,
    claude_marketplace_settings,
    codex_marketplace_listing_payload,
    codex_source_action,
    execute_installation,
    execute_persistent_installation,
)

UNOWNED_AGENT_FILENAME = "developer-owned.toml"
UNOWNED_AGENT_CONTENT = 'name = "developer-owned"\n'
REQUIRED_BINARIES: tuple[str, ...] = ("just", "claude", "codex", PYTHON_EXECUTABLE)
_RECORDED_JUST_INVOCATION_ENV = "OUTCOMEENG_RECORDED_JUST_INVOCATION"
_REAL_JUST_ENV = "OUTCOMEENG_REAL_JUST"


NONCANONICAL_MARKETPLACE_SOURCE = "/tmp/local-marketplace"


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
    """The attempted prefix and the first failure, absent when none was raised."""

    plan: InstallationPlan
    attempted: tuple[InstallationCommand, ...]
    failure: InstallationFailure | None


@dataclass(frozen=True)
class CollisionObservation:
    """A user-scope collision, absent when the run was not rejected."""

    settings_path: Path
    error: str | None
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
    """Executed nested command from the public isolated-verification recipe."""

    exit_code: int
    invoked: tuple[str, ...]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class RealInstallationObservation:
    """Real persistent and repeated isolated installation observations."""

    persistent_exit_code: int
    persistent_claude_plugins: frozenset[str]
    persistent_codex_plugins: frozenset[str]
    persistent_selection: frozenset[str]
    persistent_settings_before: bytes
    persistent_settings_after: bytes
    persistent_claude_source_action: SourceAction
    persistent_codex_source_action: SourceAction
    persistent_stdout: str
    persistent_stderr: str
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
    invocation_checkout: Path
    state_roots: tuple[Path, ...]
    placed_initial: tuple[tuple[str, bytes], ...]
    placed_first: tuple[tuple[str, bytes], ...]
    placed_second: tuple[tuple[str, bytes], ...]
    shipped_agents: tuple[tuple[str, bytes], ...]
    unowned_initial: bytes
    unowned_first: bytes
    unowned_second: bytes
    persistent_initial: tuple[tuple[str, bytes], ...]
    persistent_first: tuple[tuple[str, bytes], ...]
    persistent_second: tuple[tuple[str, bytes], ...]
    persistent_mode_first: int
    persistent_mode_second: int
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
        stdout = codex_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)
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
            codex_marketplace_listing_payload(codex_source),
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
            json.dumps(claude_marketplace_settings(CANONICAL_MARKETPLACE_SOURCE)),
            encoding="utf-8",
        )
        runner = RecordingRunner()
        rejection: str | None = None
        try:
            execute_persistent_installation(mirror, environment, runner)
        except ValueError as error:
            rejection = str(error)
        return CollisionObservation(
            settings_path=settings_path,
            error=rejection,
            attempted=tuple(runner.calls),
        )


def observe_missing_codex_home() -> str | None:
    """Expose the rejection, if any, when no Codex home is selected."""
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
    return None


def _installation_plans(temporary_root: Path) -> tuple[InstallationPlan, ...]:
    """Build every plan repository installation performs across its modes.

    A persistent plan against an already-canonical source refreshes it, while
    a noncanonical source is replaced (removed, then added), so both persistent
    variants are needed to cover the marketplace operation vocabulary.
    """
    checkout = repository_root()
    isolated = build_isolated_installation_plan(
        checkout,
        temporary_root / "isolated",
        os.environ,
    )
    plans = [isolated]
    for index, source in enumerate(
        (NONCANONICAL_MARKETPLACE_SOURCE, CANONICAL_MARKETPLACE_SOURCE)
    ):
        mirror = temporary_root / f"checkout-{index}"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, source)
        environment = _persistent_environment(temporary_root / f"state-{index}")
        preflight = build_persistent_preflight(mirror, environment)
        plans.append(
            build_persistent_installation_plan(
                preflight,
                codex_marketplace_listing_payload(source),
            )
        )
    return tuple(plans)


def observe_planned_operations() -> tuple[Operation, ...]:
    """Expose every operation a repository-installation plan performs.

    An isolated plan registers fresh sources, so it never carries the
    marketplace remove and refresh operations a persistent plan performs
    against an already-registered source. The union across every plan is the
    domain of operations a plan itself performs; the persistent preflight's
    marketplace inspection fails outside any plan and is exposed separately.
    """
    with TemporaryDirectory() as temporary_directory:
        plans = _installation_plans(Path(temporary_directory))
    return tuple(
        dict.fromkeys(command.operation for plan in plans for command in plan.commands)
    )


@dataclass(frozen=True)
class RestoreObservation:
    """Settings bytes around a persistent run scripted to fail partway."""

    settings_before: bytes
    settings_after: bytes
    failed_operation: Operation
    attempted: tuple[InstallationCommand, ...]
    failure: InstallationFailure | None


@dataclass
class SettingsMutatingRunner:
    """Runner that writes plugin state like the agent CLI, then fails one command.

    `/test` Stage 5 exception 1: a real mid-plan CLI failure after earlier
    commands have already mutated the settings document cannot be produced
    reliably against the real agent, and that partial-mutation state is
    exactly what the restore has to undo.
    """

    settings: Path
    failed_operation: Operation
    failed_occurrence: int = 1
    calls: list[InstallationCommand] = field(default_factory=list)
    _seen: int = 0

    def __call__(self, command: InstallationCommand) -> CommandResult:
        self.calls.append(command)
        if command.agent is Agent.CLAUDE and command.plugin is not None:
            document = cast(
                "dict[str, object]",
                json.loads(self.settings.read_text(encoding="utf-8")),
            )
            enabled = cast(
                "dict[str, object]",
                document.setdefault(CLAUDE_ENABLED_PLUGINS_FIELD, {}),
            )
            enabled[f"{command.plugin}@{MARKETPLACE_NAME}"] = True
            self.settings.write_text(json.dumps(document, indent=2), encoding="utf-8")
        if command.operation is self.failed_operation:
            self._seen += 1
            if self._seen == self.failed_occurrence:
                return CommandResult(command.argv, 1, "", command.operation.value)
        stdout = ""
        if command.operation is Operation.MARKETPLACE_INSPECT:
            stdout = codex_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)
        return CommandResult(command.argv, 0, stdout, "")


def observe_failed_run_restore(operation: Operation) -> RestoreObservation:
    """Fail a persistent run midway after it has already mutated settings."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        settings = mirror / CLAUDE_PROJECT_SETTINGS_PATH
        _copy_committed_project_settings(checkout, settings)
        environment = _persistent_environment(temporary_root)
        before = settings.read_bytes()
        runner = SettingsMutatingRunner(settings=settings, failed_operation=operation)
        failure: InstallationFailure | None = None
        try:
            execute_persistent_installation(mirror, environment, runner)
        except InstallationFailure as raised:
            failure = raised
        return RestoreObservation(
            settings_before=before,
            settings_after=settings.read_bytes(),
            failed_operation=operation,
            attempted=tuple(runner.calls),
            failure=failure,
        )


def observe_inspection_failure() -> FailureObservation:
    """Fail the persistent preflight's marketplace inspection before any plan."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        runner = RecordingRunner(failed_operation=Operation.MARKETPLACE_INSPECT)
        failure: InstallationFailure | None = None
        try:
            execute_persistent_installation(mirror, environment, runner)
        except InstallationFailure as raised:
            failure = raised
        return FailureObservation(
            plan=build_persistent_installation_plan(
                build_persistent_preflight(mirror, environment),
                codex_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE),
            ),
            attempted=tuple(runner.calls),
            failure=failure,
        )


def observe_first_failure(operation: Operation) -> FailureObservation:
    """Fail the selected operation in the plan that performs it."""
    with TemporaryDirectory() as temporary_directory:
        plans = _installation_plans(Path(temporary_directory))
        plan = next(
            candidate
            for candidate in plans
            if any(command.operation is operation for command in candidate.commands)
        )
        runner = RecordingRunner(failed_operation=operation)
        failure: InstallationFailure | None = None
        try:
            execute_installation(plan, runner)
        except InstallationFailure as raised:
            failure = raised
        return FailureObservation(
            plan=plan,
            attempted=tuple(runner.calls),
            failure=failure,
        )


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
    """Run the public isolated-verification recipe."""
    real_just = _required_binary("just")
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        invocation_path = temporary_root / "invocation.json"
        shim_directory = temporary_root / "bin"
        shim_directory.mkdir()
        shim = shim_directory / "just"
        shim.write_text(
            "#!/usr/bin/env python3\n"
            "import json\n"
            "import os\n"
            "import sys\n"
            "from pathlib import Path\n"
            f"invocation_path = Path(os.environ[{_RECORDED_JUST_INVOCATION_ENV!r}])\n"
            "if not invocation_path.exists():\n"
            "    invocation_path.write_text("
            "json.dumps(sys.argv[1:]), encoding='utf-8')\n"
            f"real_just = os.environ[{_REAL_JUST_ENV!r}]\n"
            "os.execv(real_just, [real_just, *sys.argv[1:]])\n",
            encoding="utf-8",
        )
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
        environment = dict(os.environ)
        environment.update(
            {
                _RECORDED_JUST_INVOCATION_ENV: str(invocation_path),
                _REAL_JUST_ENV: real_just,
                "PATH": f"{shim_directory}{os.pathsep}{environment['PATH']}",
            }
        )
        result = subprocess.run(
            (real_just, "verify-marketplace-installation"),
            cwd=repository_root(),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        recorded = cast(
            object,
            json.loads(invocation_path.read_text(encoding="utf-8")),
        )
        if not isinstance(recorded, list) or not all(
            isinstance(argument, str) for argument in recorded
        ):
            raise RuntimeError("recorded just invocation must be a string array")
        invoked = tuple(recorded)
    return VerificationRecipeObservation(
        exit_code=result.returncode,
        invoked=invoked,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def observe_real_installation() -> RealInstallationObservation:
    """Run persistent and isolated installation with real agent CLIs.

    Both source actions are read from the pre-run agent state, so they are the
    reconciliation each agent's run actually takes. Reading them afterwards
    would report a canonical registration whichever action produced it.
    """
    checkout = repository_root()
    _require_binaries(REQUIRED_BINARIES)
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        persistent_mirror = temporary_root / "persistent-checkout"
        _mirror_installation_inputs(checkout, persistent_mirror)
        selected_environment = _persistent_environment(
            temporary_root / "selected-agent-state"
        )
        _prepare_agent_state(selected_environment)
        _register_persistent_claude_marketplace(
            persistent_mirror,
            selected_environment,
        )
        _register_persistent_codex_marketplace(
            persistent_mirror,
            selected_environment,
        )
        persistent_settings = persistent_mirror / CLAUDE_PROJECT_SETTINGS_PATH
        _copy_committed_project_settings(checkout, persistent_settings)
        persistent_selection = _declared_selection(persistent_settings)
        persistent_settings_before = persistent_settings.read_bytes()
        persistent_preflight = build_persistent_preflight(
            persistent_mirror,
            selected_environment,
        )
        persistent_codex_marketplaces = _run_codex_marketplace_listing(
            persistent_mirror,
            selected_environment,
        )
        persistent = _run_persistent_recipe(
            checkout,
            persistent_mirror,
            selected_environment,
        )
        persistent_claude = _run_listing(
            Agent.CLAUDE,
            persistent_mirror,
            selected_environment,
        )
        persistent_codex = _run_listing(
            Agent.CODEX,
            persistent_mirror,
            selected_environment,
        )
        mirror = temporary_root / "checkout"
        state = temporary_root / "state"
        _mirror_installation_inputs(checkout, mirror)
        claude_catalog = (mirror / CLAUDE_CATALOG_PATH).read_bytes()
        codex_catalog = (mirror / CODEX_CATALOG_PATH).read_bytes()
        shipped_agents = _shipped_agent_snapshot(mirror)
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
        with _blocked_directory(persistent_root) as persistent_mode_first:
            first = _run_recipe(checkout, mirror, state, environment)
        claude_first = _run_listing(Agent.CLAUDE, mirror, environment)
        codex_first = _run_listing(Agent.CODEX, mirror, environment)
        placed_first = _agent_snapshot(mirror)
        unowned_first = unowned.read_bytes()
        persistent_first = _tree_snapshot(persistent_root)
        with _blocked_directory(persistent_root) as persistent_mode_second:
            second = _run_recipe(checkout, mirror, state, environment)
        claude_second = _run_listing(Agent.CLAUDE, mirror, environment)
        codex_second = _run_listing(Agent.CODEX, mirror, environment)
        placed_second = _agent_snapshot(mirror)
        unowned_second = unowned.read_bytes()
        persistent_second = _tree_snapshot(persistent_root)
        persistent_settings_after = persistent_settings.read_bytes()
    return RealInstallationObservation(
        persistent_exit_code=persistent.returncode,
        persistent_claude_plugins=_listed_plugin_names(
            Agent.CLAUDE,
            persistent_claude.stdout,
        ),
        persistent_codex_plugins=_listed_plugin_names(
            Agent.CODEX,
            persistent_codex.stdout,
        ),
        persistent_selection=persistent_selection,
        persistent_settings_before=persistent_settings_before,
        persistent_settings_after=persistent_settings_after,
        persistent_claude_source_action=persistent_preflight.claude_source_action,
        persistent_codex_source_action=codex_source_action(
            persistent_codex_marketplaces.stdout
        ),
        persistent_stdout=persistent.stdout,
        persistent_stderr=persistent.stderr,
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
        invocation_checkout=mirror.resolve(),
        state_roots=state_roots,
        placed_initial=placed_initial,
        placed_first=placed_first,
        placed_second=placed_second,
        shipped_agents=shipped_agents,
        unowned_initial=unowned_initial,
        unowned_first=unowned_first,
        unowned_second=unowned_second,
        persistent_initial=persistent_initial,
        persistent_first=persistent_first,
        persistent_second=persistent_second,
        persistent_mode_first=persistent_mode_first,
        persistent_mode_second=persistent_mode_second,
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
        entries = document.get(CODEX_PLUGIN_ENTRIES_FIELD)
    if not isinstance(entries, list):
        raise RuntimeError(f"{agent.value} plugin listing must contain an array")
    plugin_id_field = (
        CLAUDE_PLUGIN_ID_FIELD if agent is Agent.CLAUDE else CODEX_PLUGIN_ID_FIELD
    )
    plugin_enabled_field = (
        CLAUDE_PLUGIN_ENABLED_FIELD
        if agent is Agent.CLAUDE
        else CODEX_PLUGIN_ENABLED_FIELD
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


def _copy_committed_project_settings(checkout: Path, destination: Path) -> None:
    """Copy the checkout's committed Claude project settings into a mirror.

    The committed document carries this repository's real plugin selection,
    the whole-payload artifact the persistent-installation scenario is about.
    """
    source = checkout / CLAUDE_PROJECT_SETTINGS_PATH
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _declared_selection(settings: Path) -> frozenset[str]:
    """Read the plugin names a project settings document declares enabled."""
    document = cast(
        "dict[str, object]", json.loads(settings.read_text(encoding="utf-8"))
    )
    enabled = document.get(CLAUDE_ENABLED_PLUGINS_FIELD)
    if not isinstance(enabled, dict):
        raise RuntimeError(f"{settings} declares no plugin selection")
    suffix = f"@{MARKETPLACE_NAME}"
    return frozenset(
        identifier.removesuffix(suffix)
        for identifier, active in enabled.items()
        if active is True and identifier.endswith(suffix)
    )


def _write_project_marketplace(checkout: Path, repository: str) -> None:
    settings = checkout / CLAUDE_PROJECT_SETTINGS_PATH
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(
        json.dumps(claude_marketplace_settings(repository)),
        encoding="utf-8",
    )


def _persistent_environment(root: Path) -> dict[str, str]:
    root = root.resolve()
    environment = dict(os.environ)
    environment.update(
        {
            HOME_ENV: str(root / "home"),
            CLAUDE_CONFIG_ENV: str(root / "claude"),
            CODEX_HOME_ENV: str(root / "codex"),
            CODEX_SQLITE_HOME_ENV: str(root / "codex-sqlite"),
        }
    )
    return environment


def _prepare_agent_state(environment: Mapping[str, str]) -> None:
    for name in STATE_ENV_NAMES:
        Path(environment[name]).mkdir(parents=True, exist_ok=True)


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


def _required_binary(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"required installation binary is unavailable: {name}")
    return executable


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


def _run_persistent_recipe(
    source_checkout: Path,
    mirror: Path,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (
            "just",
            "install-marketplace",
            "--checkout",
            str(mirror),
            "--json",
        ),
        cwd=source_checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )


def _register_persistent_claude_marketplace(
    checkout: Path,
    environment: Mapping[str, str],
) -> None:
    result = subprocess.run(
        (
            "claude",
            "plugin",
            "marketplace",
            "add",
            CANONICAL_MARKETPLACE_SOURCE,
            "--scope",
            "project",
        ),
        cwd=checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Claude project marketplace registration failed with exit "
            f"{result.returncode}: {result.stderr}"
        )


def _register_persistent_codex_marketplace(
    checkout: Path,
    environment: Mapping[str, str],
) -> None:
    result = subprocess.run(
        (
            "codex",
            "plugin",
            "marketplace",
            "add",
            CANONICAL_CODEX_SOURCE,
            "--json",
        ),
        cwd=checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Codex marketplace registration failed with exit "
            f"{result.returncode}: {result.stderr}"
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


def _run_codex_marketplace_listing(
    checkout: Path,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        CODEX_MARKETPLACE_LIST_COMMAND,
        cwd=checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Codex marketplace listing failed with exit "
            f"{result.returncode}: {result.stderr}"
        )
    return result


def _agent_snapshot(checkout: Path) -> tuple[tuple[str, bytes], ...]:
    directory = checkout / CODEX_AGENTS_PATH
    return tuple((path.name, path.read_bytes()) for path in sorted(directory.glob("*")))


def _shipped_agent_snapshot(checkout: Path) -> tuple[tuple[str, bytes], ...]:
    shipped: dict[str, bytes] = {}
    manifests = (checkout / "dist/codex").glob(
        f"*/skills/*/agents/{PLACEMENT_MANIFEST_FILENAME}"
    )
    for manifest in sorted(manifests):
        document = json.loads(manifest.read_text(encoding="utf-8"))
        if document.get(PLACEMENT_MANIFEST_DIRECTORY_FIELD) != str(CODEX_AGENTS_PATH):
            continue
        prefix = str(document[PLACEMENT_MANIFEST_PREFIX_FIELD])
        for definition in sorted(manifest.parent.glob(f"{prefix}*")):
            if definition.name in shipped:
                raise RuntimeError(
                    f"duplicate shipped Codex agent definition: {definition.name}"
                )
            shipped[definition.name] = definition.read_bytes()
    return tuple(sorted(shipped.items()))


@contextmanager
def _blocked_directory(path: Path) -> Iterator[int]:
    original_mode = stat.S_IMODE(path.stat().st_mode)
    path.chmod(0)
    try:
        yield stat.S_IMODE(path.stat().st_mode)
    finally:
        path.chmod(original_mode)


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
    "observe_failed_run_restore",
    "observe_inspection_failure",
    "observe_missing_codex_home",
    "observe_persistent_execution",
    "observe_persistent_plan",
    "observe_planned_operations",
    "observe_real_installation",
    "observe_repository_plan",
    "observe_verification_recipe",
]
