"""Resource harnesses and recording collaborators for marketplace installation."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from functools import cache
from io import StringIO
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
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    CLAUDE_CATALOG_PATH,
    CLAUDE_CONFIG_ENV,
    CLAUDE_ENABLED_PLUGINS_FIELD,
    CLAUDE_PLUGIN_ENABLED_FIELD,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_PROJECT_SETTINGS_PATH,
    CODEX_AGENTS_PATH,
    CODEX_CATALOG_PATH,
    CODEX_CONFIG_PATH,
    CODEX_HOME_ENV,
    CODEX_MARKETPLACE_LIST_COMMAND,
    CODEX_PLUGIN_ENABLED_FIELD,
    CODEX_PLUGIN_ENTRIES_FIELD,
    CODEX_PLUGIN_ID_FIELD,
    CODEX_PLUGIN_MARKETPLACE_FIELD,
    CODEX_SQLITE_HOME_ENV,
    CommandResult,
    EXTRA_MARKETPLACES_FIELD,
    HOME_ENV,
    InstallationCommand,
    InstallationFailure,
    InstallationMode,
    InstallationPlan,
    InstallationReport,
    MARKETPLACE_NAME,
    Operation,
    PersistentPreflight,
    PLUGIN_OPERATIONS,
    PYTHON_EXECUTABLE,
    SourceAction,
    SPEC_TREE_PLUGIN,
    STATE_ENV_NAMES,
    UNPUBLISHED_PLUGIN_FRAGMENT,
    build_isolated_installation_plan,
    build_persistent_installation_plan,
    build_persistent_preflight,
    claude_marketplace_settings,
    codex_marketplace_listing_payload,
    codex_source_action,
    execute_installation,
    execute_persistent_installation,
    main,
)
from outcomeeng_testing.generators.installation import (
    catalog_plugin_names_from_document,
    generated_agent_subsets,
    generated_invalid_catalog_subsets,
    generated_persistent_catalog_selections,
)

UNOWNED_AGENT_FILENAME = "developer-owned.toml"
UNOWNED_AGENT_CONTENT = 'name = "developer-owned"\n'
REQUIRED_BINARIES: tuple[str, ...] = ("just", "claude", "codex", PYTHON_EXECUTABLE)
_RECORDED_JUST_INVOCATION_ENV = "OUTCOMEENG_RECORDED_JUST_INVOCATION"
NONCANONICAL_MARKETPLACE_SOURCE = "outcomeeng/plugins-fork"
PLUGIN_DISABLING_CODEX_CONFIG = b"[plugins]\nenabled = false\n"


def _settings_json(path: Path) -> dict[str, object]:
    """Read a JSON settings document from disk."""
    return cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))


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
class CatalogSubsetMapping:
    """One installed selection and its planned plugin operations."""

    selected: frozenset[str]
    planned: tuple[str, ...]
    installs: tuple[str, ...]
    enables: tuple[str, ...]


@dataclass(frozen=True)
class CatalogSubsetPlanObservation:
    """Persistent plan mappings for every valid subset of one agent's catalog."""

    agent: Agent
    catalog: tuple[str, ...]
    mappings: tuple[CatalogSubsetMapping, ...]


@dataclass(frozen=True)
class PersistentCliObservation:
    """Exit status and streams from one controlled persistent CLI run."""

    exit_code: int
    attempted: tuple[InstallationCommand, ...]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class FailureObservation:
    """Public CLI streams and command prefix from one terminal failure."""

    plan: InstallationPlan
    command_sequence: tuple[InstallationCommand, ...]
    attempted: tuple[InstallationCommand, ...]
    exit_code: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class CollisionObservation:
    """A user-scope collision, absent when the run was not rejected."""

    settings_path: Path
    error: str | None
    attempted: tuple[InstallationCommand, ...]


@dataclass(frozen=True)
class SelectionRejectionObservation:
    """An invalid selection rejection and any read-only commands attempted."""

    error: str | None
    attempted: tuple[InstallationCommand, ...]


@dataclass(frozen=True)
class ConfigObservation:
    """Plans and config bytes around a repository-config mutation."""

    before: InstallationPlan
    after: InstallationPlan
    persistent_before: InstallationPlan
    persistent_after: InstallationPlan
    config_written: bytes
    config_observed: bytes


@dataclass(frozen=True)
class VerificationRecipeObservation:
    """Executed nested command from the public isolated-verification recipe."""

    exit_code: int
    invoked: tuple[str, ...]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class PluginListing:
    """Plugin names one real agent CLI reports as installed and as enabled.

    Installation and activation are separate observations: a plugin the scope
    installs without activating appears in `installed` and not in `enabled`.
    """

    installed: frozenset[str]
    enabled: frozenset[str]


@dataclass(frozen=True)
class RealFirstInstallObservation:
    """Real agent-CLI observations from one empty persistent installation."""

    initial_state: tuple[tuple[str, bytes], ...]
    initial_project_settings: bytes | None
    exit_code: int
    stdout: str
    stderr: str
    claude_listing_exit_code: int
    claude_listing_stderr: str
    claude_plugins: PluginListing | None
    codex_listing_exit_code: int
    codex_listing_stderr: str
    codex_plugins: PluginListing | None


@dataclass(frozen=True)
class RealInstallationObservation:
    """Real persistent and repeated isolated installation observations."""

    persistent_exit_code: int
    persistent_claude_plugins: PluginListing
    persistent_codex_plugins: PluginListing
    persistent_claude_selected: frozenset[str]
    persistent_codex_selected: frozenset[str]
    persistent_planned_operations: int
    persistent_selection: frozenset[str]
    persistent_settings_before: bytes
    persistent_settings_after: bytes
    persistent_claude_source_action: SourceAction
    persistent_codex_source_action: SourceAction
    persistent_stdout: str
    persistent_stderr: str
    first_exit_code: int
    second_exit_code: int
    claude_plugins_first: PluginListing
    claude_plugins_second: PluginListing
    codex_plugins_first: PluginListing
    codex_plugins_second: PluginListing
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
    subset_exit_code: int
    subset_claude_plugins: PluginListing
    subset_codex_plugins: PluginListing
    subset_claude_catalog: bytes
    subset_codex_catalog: bytes
    subset_invocation_checkout: Path
    subset_claude_registration_target: str
    subset_codex_registration_target: str
    subset_stdout: str
    subset_stderr: str


@dataclass
class RecordingRunner:
    """Installation runner that records commands and can fail one operation."""

    failed_operation: Operation | None = None
    installed: Mapping[Agent, frozenset[str]] | None = None
    calls: list[InstallationCommand] = field(default_factory=list)

    def __call__(self, command: InstallationCommand) -> CommandResult:
        self.calls.append(command)
        exit_code = 1 if command.operation is self.failed_operation else 0
        stdout = _successful_command_payload(command, self.installed)
        return CommandResult(
            argv=command.argv,
            exit_code=exit_code,
            stdout=stdout,
            stderr=command.operation.value if exit_code else "",
        )


BASE_REF_BRANCH = "main"
BASE_REF = "origin/main"


def repository_root() -> Path:
    """Return the checkout containing this installed harness package."""
    return Path(__file__).resolve().parents[2]


def _installed_or_catalog_plugins(
    checkout: Path,
    installed: Mapping[Agent, frozenset[str]] | None,
) -> dict[Agent, frozenset[str]]:
    if installed is not None:
        return {agent: installed.get(agent, frozenset()) for agent in Agent}
    return {
        agent: frozenset(names)
        for agent, names in _catalogs_from_documents(checkout).items()
    }


def _catalogs_from_documents(checkout: Path) -> dict[Agent, tuple[str, ...]]:
    """Read both committed catalogs without the production catalog parser."""
    return {
        Agent.CLAUDE: catalog_plugin_names_from_document(
            checkout / CLAUDE_CATALOG_PATH
        ),
        Agent.CODEX: catalog_plugin_names_from_document(checkout / CODEX_CATALOG_PATH),
    }


def _plugin_listing_payload(
    agent: Agent,
    checkout: Path,
    plugins: frozenset[str],
) -> str:
    identifiers = sorted(plugins)
    if agent is Agent.CLAUDE:
        return json.dumps(
            [
                {
                    CLAUDE_PLUGIN_ID_FIELD: f"{plugin}@{MARKETPLACE_NAME}",
                    CLAUDE_PLUGIN_ENABLED_FIELD: True,
                    CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                    CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout.resolve()),
                }
                for plugin in identifiers
            ]
        )
    return json.dumps(
        {
            CODEX_PLUGIN_ENTRIES_FIELD: [
                {
                    CODEX_PLUGIN_ID_FIELD: f"{plugin}@{MARKETPLACE_NAME}",
                    CODEX_PLUGIN_ENABLED_FIELD: True,
                    CODEX_PLUGIN_MARKETPLACE_FIELD: MARKETPLACE_NAME,
                }
                for plugin in identifiers
            ]
        }
    )


def _successful_command_payload(
    command: InstallationCommand,
    installed: Mapping[Agent, frozenset[str]] | None,
) -> str:
    if command.operation is Operation.MARKETPLACE_INSPECT:
        return codex_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)
    if command.operation is Operation.PLUGIN_INSPECT:
        inventories = _installed_or_catalog_plugins(command.cwd, installed)
        return _plugin_listing_payload(
            command.agent,
            command.cwd,
            inventories[command.agent],
        )
    return ""


def _persistent_plan_with_catalog_inventories(
    preflight: PersistentPreflight,
    codex_source: str,
) -> InstallationPlan:
    inventories = _installed_or_catalog_plugins(preflight.roots.checkout, None)
    return build_persistent_installation_plan(
        preflight,
        claude_plugins_payload=_plugin_listing_payload(
            Agent.CLAUDE,
            preflight.roots.checkout,
            inventories[Agent.CLAUDE],
        ),
        codex_marketplace_payload=codex_marketplace_listing_payload(codex_source),
        codex_plugins_payload=_plugin_listing_payload(
            Agent.CODEX,
            preflight.roots.checkout,
            inventories[Agent.CODEX],
        ),
    )


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
    installed: Mapping[Agent, frozenset[str]] | None = None,
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
        inventories = _installed_or_catalog_plugins(mirror, installed)
        plan = build_persistent_installation_plan(
            preflight,
            claude_plugins_payload=_plugin_listing_payload(
                Agent.CLAUDE,
                mirror,
                inventories[Agent.CLAUDE],
            ),
            codex_marketplace_payload=codex_marketplace_listing_payload(codex_source),
            codex_plugins_payload=_plugin_listing_payload(
                Agent.CODEX,
                mirror,
                inventories[Agent.CODEX],
            ),
        )
    return PersistentPlanObservation(
        preflight=preflight,
        plan=plan,
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
    )


def observe_persistent_execution(
    installed: Mapping[Agent, frozenset[str]] | None = None,
) -> PersistentExecutionObservation:
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
        runner = RecordingRunner(installed=installed)
        report = execute_persistent_installation(mirror, environment, runner)
    return PersistentExecutionObservation(
        preflight=preflight,
        report=report,
        attempted=tuple(runner.calls),
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
    )


def observe_persistent_catalog_subset_plans() -> tuple[
    CatalogSubsetPlanObservation, ...
]:
    """Build persistent plans for every valid subset of each agent catalog."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        preflight = build_persistent_preflight(mirror, environment)
        catalogs = _catalogs_from_documents(mirror)
        observations: list[CatalogSubsetPlanObservation] = []
        for agent in Agent:
            mappings: list[CatalogSubsetMapping] = []
            for selected in generated_persistent_catalog_selections(catalogs[agent]):
                installed = {
                    candidate: frozenset({SPEC_TREE_PLUGIN}) for candidate in Agent
                }
                installed[agent] = selected
                plan = build_persistent_installation_plan(
                    preflight,
                    claude_plugins_payload=_plugin_listing_payload(
                        Agent.CLAUDE,
                        mirror,
                        installed[Agent.CLAUDE],
                    ),
                    codex_marketplace_payload=codex_marketplace_listing_payload(
                        CANONICAL_CODEX_SOURCE
                    ),
                    codex_plugins_payload=_plugin_listing_payload(
                        Agent.CODEX,
                        mirror,
                        installed[Agent.CODEX],
                    ),
                )
                planned = (
                    plan.claude_plugins if agent is Agent.CLAUDE else plan.codex_plugins
                )
                mappings.append(
                    CatalogSubsetMapping(
                        selected=selected,
                        planned=planned,
                        installs=tuple(
                            command.plugin
                            for command in plan.commands
                            if command.agent is agent
                            and command.operation is Operation.PLUGIN_INSTALL
                            and command.plugin is not None
                        ),
                        enables=tuple(
                            command.plugin
                            for command in plan.commands
                            if command.agent is agent
                            and command.operation is Operation.PLUGIN_ENABLE
                            and command.plugin is not None
                        ),
                    )
                )
            observations.append(
                CatalogSubsetPlanObservation(
                    agent=agent,
                    catalog=catalogs[agent],
                    mappings=tuple(mappings),
                )
            )
    return tuple(observations)


def observe_first_persistent_cli() -> PersistentCliObservation:
    """Run the public persistent CLI against empty controlled agent inventories."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        runner = RecordingRunner(installed={agent: frozenset() for agent in Agent})
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(
                ("--checkout", str(mirror), "--json"),
                base_environment=environment,
                runner=runner,
            )
    return PersistentCliObservation(
        exit_code=exit_code,
        attempted=tuple(runner.calls),
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
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


def observe_invalid_persistent_selection() -> SelectionRejectionObservation:
    """Expose nonempty selections without spec-tree at the mutation boundary."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        installed = generated_agent_subsets(mirror, include_spec_tree=False)
        runner = RecordingRunner(installed=installed)
        rejection: str | None = None
        try:
            execute_persistent_installation(mirror, environment, runner)
        except ValueError as error:
            rejection = str(error)
        return SelectionRejectionObservation(
            error=rejection,
            attempted=tuple(runner.calls),
        )


def observe_invalid_persistent_selections() -> tuple[
    SelectionRejectionObservation, ...
]:
    """Expose every nonempty per-agent selection that omits spec-tree."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        catalogs = _catalogs_from_documents(mirror)
        observations: list[SelectionRejectionObservation] = []
        for agent in Agent:
            for selected in generated_invalid_catalog_subsets(catalogs[agent]):
                installed = {
                    candidate: frozenset({SPEC_TREE_PLUGIN}) for candidate in Agent
                }
                installed[agent] = selected
                runner = RecordingRunner(installed=installed)
                rejection: str | None = None
                try:
                    execute_persistent_installation(mirror, environment, runner)
                except ValueError as error:
                    rejection = str(error)
                observations.append(
                    SelectionRejectionObservation(
                        error=rejection,
                        attempted=tuple(runner.calls),
                    )
                )
    return tuple(observations)


def observe_invalid_isolated_selection() -> SelectionRejectionObservation:
    """Expose invalid isolated planning before any command can execute."""
    checkout = repository_root()
    invalid = generated_agent_subsets(checkout, include_spec_tree=False)
    rejection: str | None = None
    with TemporaryDirectory() as temporary_directory:
        try:
            build_isolated_installation_plan(
                checkout,
                Path(temporary_directory) / "state",
                os.environ,
                claude_plugins=tuple(invalid[Agent.CLAUDE]),
                codex_plugins=tuple(invalid[Agent.CODEX]),
            )
        except ValueError as error:
            rejection = str(error)
    return SelectionRejectionObservation(error=rejection, attempted=())


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
        plans.append(_persistent_plan_with_catalog_inventories(preflight, source))
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
    failed_operation: Operation | None = None
    failed_occurrence: int = 1
    calls: list[InstallationCommand] = field(default_factory=list)
    _seen: int = 0

    def __call__(self, command: InstallationCommand) -> CommandResult:
        self.calls.append(command)
        if command.agent is Agent.CLAUDE and command.plugin is not None:
            document = self._document()
            enabled = cast(
                "dict[str, object]",
                document.setdefault(CLAUDE_ENABLED_PLUGINS_FIELD, {}),
            )
            enabled[f"{command.plugin}@{MARKETPLACE_NAME}"] = True
            self._write(document)
        if (
            command.agent is Agent.CLAUDE
            and command.operation is Operation.MARKETPLACE_ADD
        ):
            document = self._document()
            document[EXTRA_MARKETPLACES_FIELD] = claude_marketplace_settings(
                CANONICAL_MARKETPLACE_SOURCE
            )[EXTRA_MARKETPLACES_FIELD]
            self._write(document)
        if command.operation is self.failed_operation:
            self._seen += 1
            if self._seen == self.failed_occurrence:
                return CommandResult(command.argv, 1, "", command.operation.value)
        stdout = _successful_command_payload(command, None)
        return CommandResult(command.argv, 0, stdout, "")

    def _document(self) -> dict[str, object]:
        return _settings_json(self.settings)

    def _write(self, document: dict[str, object]) -> None:
        self.settings.write_text(
            json.dumps(document, indent=2) + "\n",
            encoding="utf-8",
        )


@dataclass(frozen=True)
class ReconciliationObservation:
    """Selection and marketplace source around a reconciling persistent run."""

    selection_before: object
    selection_after: object
    marketplace_before: object
    marketplace_after: object
    canonical_marketplace: object
    source_action: SourceAction


def observe_noncanonical_reconciliation() -> ReconciliationObservation:
    """Run the persistent path from a checkout declaring a noncanonical source."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        _mirror_installation_inputs(checkout, mirror)
        settings = mirror / CLAUDE_PROJECT_SETTINGS_PATH
        _copy_committed_project_settings(checkout, settings)
        document = _settings_json(settings)
        document[EXTRA_MARKETPLACES_FIELD] = claude_marketplace_settings(
            NONCANONICAL_MARKETPLACE_SOURCE
        )[EXTRA_MARKETPLACES_FIELD]
        settings.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        before = _settings_json(settings)
        environment = _persistent_environment(temporary_root)
        preflight = build_persistent_preflight(mirror, environment)
        execute_persistent_installation(
            mirror,
            environment,
            SettingsMutatingRunner(settings=settings),
        )
        after = _settings_json(settings)
    return ReconciliationObservation(
        selection_before=before.get(CLAUDE_ENABLED_PLUGINS_FIELD),
        selection_after=after.get(CLAUDE_ENABLED_PLUGINS_FIELD),
        marketplace_before=before.get(EXTRA_MARKETPLACES_FIELD),
        marketplace_after=after.get(EXTRA_MARKETPLACES_FIELD),
        canonical_marketplace=claude_marketplace_settings(CANONICAL_MARKETPLACE_SOURCE)[
            EXTRA_MARKETPLACES_FIELD
        ],
        source_action=preflight.claude_source_action,
    )


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
        preflight = build_persistent_preflight(mirror, environment)
        plan = _persistent_plan_with_catalog_inventories(
            preflight,
            CANONICAL_MARKETPLACE_SOURCE,
        )
        runner = RecordingRunner(failed_operation=Operation.MARKETPLACE_INSPECT)
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(
                ("--checkout", str(mirror), "--json"),
                base_environment=environment,
                runner=runner,
            )
        return FailureObservation(
            plan=plan,
            command_sequence=(*preflight.inspections, *plan.commands),
            attempted=tuple(runner.calls),
            exit_code=exit_code,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )


def observe_first_failure(operation: Operation) -> FailureObservation:
    """Fail a selected plan operation through the public CLI surface."""
    with TemporaryDirectory() as temporary_directory:
        plans = _installation_plans(Path(temporary_directory))
        plan = next(
            candidate
            for candidate in plans
            if any(command.operation is operation for command in candidate.commands)
        )
        runner = RecordingRunner(failed_operation=operation)
        environment = dict(plan.commands[0].environment)
        arguments = ["--checkout", str(plan.roots.checkout), "--json"]
        if plan.mode is InstallationMode.ISOLATED:
            if plan.roots.state is None:
                raise RuntimeError("isolated plan must declare its state root")
            arguments.extend(("--state-root", str(plan.roots.state)))
            command_sequence = plan.commands
        else:
            preflight = build_persistent_preflight(plan.roots.checkout, environment)
            command_sequence = (*preflight.inspections, *plan.commands)
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(
                arguments,
                base_environment=environment,
                runner=runner,
            )
        return FailureObservation(
            plan=plan,
            command_sequence=command_sequence,
            attempted=tuple(runner.calls),
            exit_code=exit_code,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
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
        config.write_bytes(PLUGIN_DISABLING_CODEX_CONFIG)
        after = build_isolated_installation_plan(mirror, state, os.environ)
        persistent_after = execute_persistent_installation(
            mirror, environment, RecordingRunner()
        ).plan
        config_observed = config.read_bytes()
    return ConfigObservation(
        before=before,
        after=after,
        persistent_before=persistent_before,
        persistent_after=persistent_after,
        config_written=PLUGIN_DISABLING_CODEX_CONFIG,
        config_observed=config_observed,
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
            "raise SystemExit(0)\n",
            encoding="utf-8",
        )
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR)
        environment = dict(os.environ)
        environment.update(
            {
                _RECORDED_JUST_INVOCATION_ENV: str(invocation_path),
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


@cache
def observe_real_first_install() -> RealFirstInstallObservation:
    """Run persistent installation in empty selected homes with real agent CLIs."""
    checkout = repository_root()
    _require_binaries(REQUIRED_BINARIES)
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        selected_root = temporary_root / "selected-agent-state"
        _mirror_installation_inputs(checkout, mirror)
        environment = _persistent_environment(selected_root)
        _prepare_agent_state(environment)
        initial_state = _tree_snapshot(selected_root)
        project_settings = mirror / CLAUDE_PROJECT_SETTINGS_PATH
        initial_project_settings = (
            project_settings.read_bytes() if project_settings.exists() else None
        )
        installation = _run_persistent_recipe(checkout, mirror, environment)
        claude_listing = _run_listing_unchecked(Agent.CLAUDE, mirror, environment)
        codex_listing = _run_listing_unchecked(Agent.CODEX, mirror, environment)
    return RealFirstInstallObservation(
        initial_state=initial_state,
        initial_project_settings=initial_project_settings,
        exit_code=installation.returncode,
        stdout=installation.stdout,
        stderr=installation.stderr,
        claude_listing_exit_code=claude_listing.returncode,
        claude_listing_stderr=claude_listing.stderr,
        claude_plugins=(
            _listed_plugins(Agent.CLAUDE, claude_listing.stdout)
            if claude_listing.returncode == 0
            else None
        ),
        codex_listing_exit_code=codex_listing.returncode,
        codex_listing_stderr=codex_listing.stderr,
        codex_plugins=(
            _listed_plugins(Agent.CODEX, codex_listing.stdout)
            if codex_listing.returncode == 0
            else None
        ),
    )


@cache
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
        persistent_subsets = generated_agent_subsets(
            persistent_mirror,
            include_spec_tree=True,
        )
        _seed_persistent_plugins(
            persistent_mirror,
            selected_environment,
            persistent_subsets,
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
        persistent_plan = build_persistent_installation_plan(
            persistent_preflight,
            claude_plugins_payload=_plugin_listing_payload(
                Agent.CLAUDE,
                persistent_mirror,
                persistent_subsets[Agent.CLAUDE],
            ),
            codex_marketplace_payload=persistent_codex_marketplaces.stdout,
            codex_plugins_payload=_plugin_listing_payload(
                Agent.CODEX,
                persistent_mirror,
                persistent_subsets[Agent.CODEX],
            ),
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
        subset_mirror = temporary_root / "subset-checkout"
        subset_state = temporary_root / "subset-state"
        _mirror_installation_inputs(checkout, subset_mirror)
        subset_selections = generated_agent_subsets(
            subset_mirror,
            include_spec_tree=True,
        )
        _write_catalog_selection(
            subset_mirror / CLAUDE_CATALOG_PATH,
            subset_selections[Agent.CLAUDE],
        )
        _write_catalog_selection(
            subset_mirror / CODEX_CATALOG_PATH,
            subset_selections[Agent.CODEX],
        )
        subset_claude_catalog = (subset_mirror / CLAUDE_CATALOG_PATH).read_bytes()
        subset_codex_catalog = (subset_mirror / CODEX_CATALOG_PATH).read_bytes()
        subset_plan = build_isolated_installation_plan(
            subset_mirror,
            subset_state,
            persistent_environment,
        )
        subset_environment = dict(subset_plan.commands[0].environment)
        subset_claude_target = _registration_target(subset_plan, Agent.CLAUDE)
        subset_codex_target = _registration_target(subset_plan, Agent.CODEX)
        subset = _run_recipe(
            checkout,
            subset_mirror,
            subset_state,
            subset_environment,
        )
        subset_claude = _run_listing(
            Agent.CLAUDE,
            subset_mirror,
            subset_environment,
        )
        subset_codex = _run_listing(
            Agent.CODEX,
            subset_mirror,
            subset_environment,
        )
        persistent_settings_after = persistent_settings.read_bytes()
    return RealInstallationObservation(
        persistent_exit_code=persistent.returncode,
        persistent_claude_plugins=_listed_plugins(
            Agent.CLAUDE,
            persistent_claude.stdout,
        ),
        persistent_codex_plugins=_listed_plugins(
            Agent.CODEX,
            persistent_codex.stdout,
        ),
        persistent_claude_selected=persistent_subsets[Agent.CLAUDE],
        persistent_codex_selected=persistent_subsets[Agent.CODEX],
        persistent_planned_operations=(
            len(persistent_preflight.inspections) + len(persistent_plan.commands)
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
        claude_plugins_first=_listed_plugins(Agent.CLAUDE, claude_first.stdout),
        claude_plugins_second=_listed_plugins(Agent.CLAUDE, claude_second.stdout),
        codex_plugins_first=_listed_plugins(Agent.CODEX, codex_first.stdout),
        codex_plugins_second=_listed_plugins(Agent.CODEX, codex_second.stdout),
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
        claude_registration_target=claude_target,
        codex_registration_target=codex_target,
        invocation_checkout=mirror.resolve(),
        state_roots=(*state_roots, *_state_roots(subset_plan)),
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
        subset_exit_code=subset.returncode,
        subset_claude_plugins=_listed_plugins(Agent.CLAUDE, subset_claude.stdout),
        subset_codex_plugins=_listed_plugins(Agent.CODEX, subset_codex.stdout),
        subset_claude_catalog=subset_claude_catalog,
        subset_codex_catalog=subset_codex_catalog,
        subset_invocation_checkout=subset_mirror.resolve(),
        subset_claude_registration_target=subset_claude_target,
        subset_codex_registration_target=subset_codex_target,
        subset_stdout=subset.stdout,
        subset_stderr=subset.stderr,
    )


def _listing_entries(agent: Agent, payload: str) -> list[object]:
    """Read the plugin entry array from a real agent CLI listing."""
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
    return entries


def _listed_identity(agent: Agent, entry: object) -> tuple[str, bool]:
    """Read one listing entry's plugin identifier and enabled state."""
    if not isinstance(entry, dict):
        raise RuntimeError(f"{agent.value} plugin listing contains a non-object")
    claude = agent is Agent.CLAUDE
    plugin_id = entry.get(CLAUDE_PLUGIN_ID_FIELD if claude else CODEX_PLUGIN_ID_FIELD)
    enabled = entry.get(
        CLAUDE_PLUGIN_ENABLED_FIELD if claude else CODEX_PLUGIN_ENABLED_FIELD
    )
    if not isinstance(plugin_id, str) or not isinstance(enabled, bool):
        raise RuntimeError(
            f"{agent.value} plugin listing entry lacks typed identity or state"
        )
    return plugin_id, enabled


def _listed_plugins(agent: Agent, payload: str) -> PluginListing:
    """Read installed and enabled plugin names from a real agent CLI listing."""
    marketplace_suffix = f"@{MARKETPLACE_NAME}"
    installed: set[str] = set()
    enabled_names: set[str] = set()
    for entry in _listing_entries(agent, payload):
        plugin_id, enabled = _listed_identity(agent, entry)
        if not plugin_id.endswith(marketplace_suffix):
            continue
        name = plugin_id.removesuffix(marketplace_suffix)
        installed.add(name)
        if enabled:
            enabled_names.add(name)
    return PluginListing(
        installed=frozenset(installed),
        enabled=frozenset(enabled_names),
    )


def _mirror_installation_inputs(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative_path in (CODEX_CATALOG_PATH, CLAUDE_CATALOG_PATH):
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative_path, target)
    shutil.copytree(source / "dist/codex", destination / "dist/codex")
    shutil.copytree(source / "dist/claude", destination / "dist/claude")


def _write_catalog_selection(path: Path, selected: frozenset[str]) -> None:
    document = cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))
    entries = cast("list[dict[str, object]]", document[CATALOG_PLUGINS_FIELD])
    document[CATALOG_PLUGINS_FIELD] = [
        entry for entry in entries if entry[CATALOG_PLUGIN_NAME_FIELD] in selected
    ]
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


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
    document = _settings_json(settings)
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


def _seed_persistent_plugins(
    checkout: Path,
    environment: Mapping[str, str],
    selections: Mapping[Agent, frozenset[str]],
) -> None:
    commands = tuple(
        (
            Agent.CLAUDE,
            (
                "claude",
                "plugin",
                "install",
                f"{plugin}@{MARKETPLACE_NAME}",
                "--scope",
                CLAUDE_PROJECT_SCOPE,
            ),
        )
        for plugin in sorted(selections[Agent.CLAUDE])
    ) + tuple(
        (
            Agent.CODEX,
            (
                "codex",
                "plugin",
                "add",
                f"{plugin}@{MARKETPLACE_NAME}",
                "--json",
            ),
        )
        for plugin in sorted(selections[Agent.CODEX])
    )
    for agent, argv in commands:
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
                f"{agent.value} persistent plugin seed failed with exit "
                f"{result.returncode}: {result.stderr}"
            )


def _run_listing_unchecked(
    agent: Agent,
    checkout: Path,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    argv = (
        ("claude", "plugin", "list", "--json")
        if agent is Agent.CLAUDE
        else (
            "codex",
            "plugin",
            "list",
            "--marketplace",
            MARKETPLACE_NAME,
            "--json",
        )
    )
    result = subprocess.run(
        argv,
        cwd=checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def _run_listing(
    agent: Agent,
    checkout: Path,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    result = _run_listing_unchecked(agent, checkout, environment)
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
    "CatalogSubsetMapping",
    "CatalogSubsetPlanObservation",
    "CollisionObservation",
    "ConfigObservation",
    "FailureObservation",
    "PersistentExecutionObservation",
    "PersistentPlanObservation",
    "PlanObservation",
    "DesignatedFailureRunner",
    "RealFirstInstallObservation",
    "RealInstallationObservation",
    "RecordingRunner",
    "UnpublishedPluginObservation",
    "UnpublishedPluginRunner",
    "VerificationRecipeObservation",
    "canonical_catalog_plugin_names",
    "committed_catalog_plugin_names",
    "observe_claude_user_collision",
    "observe_codex_config_independence",
    "observe_designated_failure",
    "observe_first_failure",
    "observe_failed_run_restore",
    "observe_failure_operation_domains",
    "observe_inspection_failure",
    "observe_invalid_isolated_selection",
    "observe_invalid_persistent_selection",
    "observe_invalid_persistent_selections",
    "observe_missing_codex_home",
    "observe_persistent_execution",
    "observe_persistent_catalog_subset_plans",
    "observe_persistent_plan",
    "observe_planned_operations",
    "observe_real_first_install",
    "observe_real_installation",
    "observe_repository_plan",
    "absent_from_every_agent",
    "observe_unpublished_plugin",
    "observe_verification_recipe",
]


@dataclass
class UnpublishedPluginRunner:
    """Installation runner whose marketplace has not published a named plugin set.

    Controlled under `/test` Stage 5 Failure simulation: a real marketplace
    reports a plugin absent only while that plugin is genuinely unpublished, a
    state that disappears the moment the plugin merges, so it cannot be produced
    on demand against the canonical source.
    """

    unpublished: Mapping[Agent, frozenset[str]]
    calls: list[InstallationCommand] = field(default_factory=list)

    def __call__(self, command: InstallationCommand) -> CommandResult:
        self.calls.append(command)
        plugin_operation = command.operation in PLUGIN_OPERATIONS
        absent = self.unpublished.get(command.agent, frozenset())
        if plugin_operation and command.plugin in absent:
            return CommandResult(
                argv=command.argv,
                exit_code=1,
                stdout="",
                stderr=(
                    f"Error: plugin `{command.plugin}` was "
                    f"{UNPUBLISHED_PLUGIN_FRAGMENT} `{MARKETPLACE_NAME}`"
                ),
            )
        stdout = (
            codex_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)
            if command.operation is Operation.MARKETPLACE_INSPECT
            else ""
        )
        return CommandResult(argv=command.argv, exit_code=0, stdout=stdout, stderr="")


@dataclass(frozen=True)
class UnpublishedPluginObservation:
    """What one installation run did when the marketplace lacked a plugin."""

    report: InstallationReport | None
    failure: InstallationFailure | None
    calls: tuple[InstallationCommand, ...]


@dataclass
class DesignatedFailureRunner:
    """Installation runner that fails one designated command with a given stderr.

    Controlled under `/test` Stage 5 Failure simulation: the classification a
    run applies to a failed command depends on that command's operation and on
    the wording its agent CLI emitted, and a real CLI produces neither on
    demand for an arbitrary operation.

    The stderr is supplied by the caller so the executed test owns which
    wording each case carries; this runner selects nothing.
    """

    operation: Operation
    stderr: str
    plugin: str | None = None
    calls: list[InstallationCommand] = field(default_factory=list)

    def __call__(self, command: InstallationCommand) -> CommandResult:
        self.calls.append(command)
        designated = command.operation is self.operation and (
            self.plugin is None or command.plugin == self.plugin
        )
        if designated:
            return CommandResult(
                argv=command.argv, exit_code=1, stdout="", stderr=self.stderr
            )
        stdout = (
            codex_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)
            if command.operation is Operation.MARKETPLACE_INSPECT
            else ""
        )
        return CommandResult(argv=command.argv, exit_code=0, stdout=stdout, stderr="")


def _build_run_plan(
    temporary_root: Path, *, isolated: bool, source: str
) -> InstallationPlan:
    """One installation plan of the selected mode and configured source."""
    mirror = temporary_root / "checkout"
    _mirror_installation_inputs(repository_root(), mirror)
    if isolated:
        return build_isolated_installation_plan(
            mirror, temporary_root / "state", os.environ
        )
    _write_project_marketplace(mirror, source)
    environment = _persistent_environment(temporary_root)
    preflight = build_persistent_preflight(mirror, environment)
    codex_source = (
        CANONICAL_CODEX_SOURCE if source == CANONICAL_MARKETPLACE_SOURCE else source
    )
    return _persistent_plan_with_catalog_inventories(preflight, codex_source)


def observe_failure_operation_domains() -> tuple[
    tuple[InstallationMode, str, tuple[Operation, ...]], ...
]:
    """Expose reachable operations for every mode and source plan variant."""
    sources = (NONCANONICAL_MARKETPLACE_SOURCE, CANONICAL_MARKETPLACE_SOURCE)
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        domains = []
        for mode in InstallationMode:
            for index, source in enumerate(sources):
                plan = _build_run_plan(
                    temporary_root / f"{mode.value}-{index}",
                    isolated=mode is InstallationMode.ISOLATED,
                    source=source,
                )
                operations = tuple(
                    dict.fromkeys(command.operation for command in plan.commands)
                )
                domains.append((mode, source, operations))
    return tuple(domains)


def _observe_installation_run(
    runner: UnpublishedPluginRunner | DesignatedFailureRunner,
    *,
    isolated: bool,
    source: str = CANONICAL_MARKETPLACE_SOURCE,
) -> UnpublishedPluginObservation:
    """Execute one installation plan of the selected mode through `runner`."""
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        plan = _build_run_plan(temporary_root, isolated=isolated, source=source)
        try:
            report = execute_installation(plan, runner)
        except InstallationFailure as failure:
            return UnpublishedPluginObservation(
                report=None, failure=failure, calls=tuple(runner.calls)
            )
    return UnpublishedPluginObservation(
        report=report, failure=None, calls=tuple(runner.calls)
    )


def absent_from_every_agent(names: frozenset[str]) -> Mapping[Agent, frozenset[str]]:
    """The named plugins missing from every agent's marketplace.

    The agent set comes from `Agent` itself, so an agent the source adds enters
    this mapping without the callers naming it.
    """
    return {agent: names for agent in Agent}


def observe_unpublished_plugin(
    *,
    isolated: bool,
    unpublished: Mapping[Agent, frozenset[str]],
) -> UnpublishedPluginObservation:
    """Run one installation whose marketplaces lack the named plugins.

    The mapping is per agent because the two marketplaces refresh separately: a
    plugin can be absent from one and installable from the other.
    """
    return _observe_installation_run(
        UnpublishedPluginRunner(unpublished), isolated=isolated
    )


def observe_designated_failure(
    *,
    isolated: bool,
    operation: Operation,
    stderr: str,
    plugin: str | None = None,
    source: str = CANONICAL_MARKETPLACE_SOURCE,
) -> UnpublishedPluginObservation:
    """Run one installation in which the designated command fails with `stderr`."""
    return _observe_installation_run(
        DesignatedFailureRunner(operation=operation, stderr=stderr, plugin=plugin),
        isolated=isolated,
        source=source,
    )


def canonical_catalog_plugin_names() -> frozenset[str]:
    """Plugins the canonical marketplace publishes, read from the base ref.

    An independent oracle: the published branch's own committed catalogs, read
    through git rather than through the installation run whose classification is
    under test. A missing base ref raises rather than reporting an empty set,
    because an empty oracle would make every pending claim vacuously true.
    """
    root = repository_root()
    names: set[str] = set()
    for path in (CLAUDE_CATALOG_PATH, CODEX_CATALOG_PATH):
        names.update(_base_ref_catalog_names(root, path))
    return frozenset(names)


def _base_ref_catalog_names(root: Path, path: Path) -> set[str]:
    """Read one catalog at the base ref, fetching that ref when absent.

    A shallow checkout has no `origin/main`, which is how the governing CI job
    checks out. Fetching the ref keeps the oracle available there rather than
    turning an absent ref into an unrelated failure of every assertion this
    test carries.
    """
    for fetch_first in (False, True):
        if fetch_first:
            fetched = subprocess.run(
                ("git", "fetch", "--depth=1", "origin", BASE_REF_BRANCH),
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if fetched.returncode != 0:
                raise RuntimeError(
                    f"cannot read the canonical catalog: fetching "
                    f"{BASE_REF_BRANCH} failed with {fetched.stderr.strip()}"
                )
        shown = subprocess.run(
            ("git", "show", f"{BASE_REF}:{path.as_posix()}"),
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if shown.returncode == 0:
            document = json.loads(shown.stdout)
            return {
                entry[CATALOG_PLUGIN_NAME_FIELD]
                for entry in document[CATALOG_PLUGINS_FIELD]
            }
    raise RuntimeError(
        f"cannot read {path.as_posix()} at {BASE_REF}: {shown.stderr.strip()}"
    )


def committed_catalog_plugin_names() -> frozenset[str]:
    """Plugins this checkout's own committed catalogs declare."""
    return frozenset(
        name
        for names in _catalogs_from_documents(repository_root()).values()
        for name in names
    )
