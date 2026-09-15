"""Resource harnesses and recording collaborators for marketplace installation."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tomllib
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from functools import cache
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import cast

from outcomeeng.distribution.agents import (
    AGENT_NAME_FIELD,
    AGENT_SKILL_ENABLED_FIELD,
)
from outcomeeng.distribution.build import render_text
from outcomeeng.distribution.contracts import (
    BUILD_TARGET_VARIABLE,
    CLAUDE_DIST_RELATIVE,
    DIST_CODEX_PLUGINS_DIR,
    PLUGIN_NAME_VARIABLE,
    Target,
)
from outcomeeng.distribution.installation import (
    AGENT_OWNERSHIP_DESTINATION_FIELD,
    AGENT_OWNERSHIP_DIGEST_FIELD,
    AGENT_OWNERSHIP_ENTRIES_FIELD,
    AGENT_OWNERSHIP_FILENAME,
    AGENT_OWNERSHIP_PLUGIN_FIELD,
    AGENT_OWNERSHIP_SCHEMA_FIELD,
    AGENT_OWNERSHIP_SCHEMA_VERSION,
    AGENT_SKILL_NAME_FIELD,
    AGENT_SKILLS_CONFIG_FIELD,
    AGENT_SKILLS_FIELD,
    Agent,
    AgentHomeCollision,
    AgentHomeCollisionError,
    AgentHomeResult,
    ClaudeInstallRecord,
    CANONICAL_CODEX_SOURCE,
    CANONICAL_MARKETPLACE_SOURCE,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    CHECKOUT_OPTION,
    CLAUDE_CATALOG_PATH,
    CLAUDE_MARKETPLACE_LIST_COMMAND,
    CLAUDE_CONFIG_ENV,
    CLAUDE_ENABLED_PLUGINS_FIELD,
    CLAUDE_LOCAL_SCOPE,
    CLAUDE_PLUGIN_ENABLED_FIELD,
    CLAUDE_PLUGIN_ID_FIELD,
    CLAUDE_PLUGIN_PROJECT_PATH_FIELD,
    CLAUDE_PLUGIN_SCOPE_FIELD,
    CLAUDE_PROJECT_SCOPE,
    CLAUDE_PROJECT_SETTINGS_PATH,
    CODEX_AGENTS_PATH,
    CLAUDE_EXECUTABLE,
    CLAUDE_LIST_COMMAND,
    CLAUDE_LOCAL_SETTINGS_PATH,
    CLAUDE_SCOPE_FLAG,
    CODEX_LIST_COMMAND,
    CODEX_EXEC_SUBCOMMAND,
    CODEX_EXECUTABLE,
    CODEX_MARKETPLACES_FIELD,
    CODEX_CATALOG_PATH,
    CODEX_CONFIG_PATH,
    CODEX_HOME_ENV,
    CODEX_HOME_AGENTS_PATH,
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
    JSON_OUTPUT_OPTION,
    MARKETPLACE_NAME,
    Operation,
    PathlessInstallRecord,
    PersistentPreflight,
    PLUGIN_OPERATIONS,
    ScopeSplitClassification,
    ScopeSplitEntry,
    ScopeSplitError,
    SourceAction,
    SPEC_TREE_PLUGIN,
    STATE_ENV_NAMES,
    STATE_ROOT_OPTION,
    build_isolated_installation_plan,
    build_persistent_installation_plan,
    build_persistent_preflight,
    claude_install_records,
    claude_marketplace_listing_payload,
    claude_marketplace_settings,
    codex_marketplace_listing_payload,
    codex_source_action,
    execute_installation,
    report_document,
    execute_persistent_installation,
    main,
    marketplace_plugin_identifier,
    marketplace_plugin_name,
)
from outcomeeng_testing.generators.installation import (
    RecordDisposition,
    UNCATALOGED_PLUGIN,
    catalog_plugin_names_from_document,
    generated_agent_subsets,
    generated_claude_install_records,
    generated_invalid_catalog_subsets,
    generated_persistent_catalog_selections,
)
from outcomeeng.validation.ci_gate import JUST_BINARY
from outcomeeng_testing.harnesses.discovery_auth import (
    DiscoveryAuthentication,
    DiscoveryAuthenticationError,
    FILE_STORE_ARGS,
    ProbeRunner,
    credential_free_environment,
    run_probe_process,
    select_authentication,
)

UNOWNED_AGENT_FILENAME = "developer-owned.toml"
UNOWNED_AGENT_CONTENT = 'name = "developer-owned"\n'
FOREIGN_DEFINITION_CONTENT = b'name = "foreign-definition"\n'
"""A definition some other party wrote at a destination a plugin wants."""
EXTERNAL_DEFINITION_CONTENT = b'name = "external"\n'
"""A definition outside the agent home that a home symlink points at."""
CONCURRENT_EDIT_CONTENT = b"edited while the run was planning\n"
"""Bytes a concurrent writer leaves at a destination between preflight and mutation."""
MALFORMED_OWNERSHIP_DIGEST = "z" * 64
"""A 64-character digest the ownership record must reject as non-hex."""
MALFORMED_SETTINGS_CONTENT = "{ not json"
"""A settings document no reader can parse, standing for a foreign checkout's defect."""
REQUIRED_BINARIES: tuple[str, ...] = (JUST_BINARY, CLAUDE_EXECUTABLE, CODEX_EXECUTABLE)
_RECORDED_JUST_INVOCATION_ENV = "OUTCOMEENG_RECORDED_JUST_INVOCATION"
NONCANONICAL_MARKETPLACE_SOURCE = "outcomeeng/plugins-fork"
CODEX_CONFIG_PLUGINS_TABLE = "plugins"
"""The trusted-product `config.toml` table carrying plugin activation overrides."""
CODEX_CONFIG_PLUGIN_ENABLED_KEY = "enabled"
"""The activation key inside that table, read by the Codex CLI and never by production."""
PLUGIN_DISABLING_CODEX_CONFIG = f"[{CODEX_CONFIG_PLUGINS_TABLE}]\n{CODEX_CONFIG_PLUGIN_ENABLED_KEY} = false\n".encode()

SUBAGENT_DISCOVERY_NAMES_FIELD = "subagent_names"
RENAMED_CHECKOUT_AGENT_NAME = "local_helper.toml"
RENAMED_CHECKOUT_SKILL_NAME = "renamed-skill"
SUBAGENT_DISCOVERY_OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        SUBAGENT_DISCOVERY_NAMES_FIELD: {"type": "array", "items": {"type": "string"}}
    },
    "required": [SUBAGENT_DISCOVERY_NAMES_FIELD],
    "additionalProperties": False,
}
SUBAGENT_DISCOVERY_PROMPT = (
    "Report every subagent name you can spawn in this session: "
    "the exact `agent_type` values your subagent-spawning tool declares, "
    "from its `Available roles` list, including built-in ones. If absent, discover "
    "it through your deferred-tool registry first. Do not read any file, run "
    "any command, or spawn any agent. Answer only with JSON matching the "
    "required output schema."
)


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
    updates: tuple[str, ...]


@dataclass(frozen=True)
class CatalogSubsetPlanObservation:
    """Persistent plan mappings for every valid subset of one agent's catalog."""

    agent: Agent
    catalog: tuple[str, ...]
    mappings: tuple[CatalogSubsetMapping, ...]


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
class AgentHomeReconciliationObservation:
    """Selected-home definitions across install and catalog reconciliation."""

    desired_first: tuple[tuple[str, bytes], ...]
    desired_second: tuple[tuple[str, bytes], ...]
    home_initial: tuple[tuple[str, bytes], ...]
    home_first: tuple[tuple[str, bytes], ...]
    home_second: tuple[tuple[str, bytes], ...]
    foreign_initial: bytes
    foreign_first: bytes
    foreign_second: bytes
    first_result: AgentHomeResult
    second_result: AgentHomeResult
    ownership_record_present: bool


@dataclass(frozen=True)
class AgentHomeCollisionObservation:
    """Foreign destination and command observations from a rejected plan."""

    collisions: tuple[AgentHomeCollision, ...]
    attempted: tuple[InstallationCommand, ...]
    home_before: tuple[tuple[str, bytes], ...]
    home_after: tuple[tuple[str, bytes], ...]


@dataclass(frozen=True)
class ScopeSplitObservation:
    """Checkout split classifications and selected-home mutation boundary."""

    entries: tuple[ScopeSplitEntry, ...]
    attempted: tuple[InstallationCommand, ...]
    home_before: tuple[tuple[str, bytes], ...]
    home_after: tuple[tuple[str, bytes], ...]


@dataclass(frozen=True)
class PluginLifecycleRun:
    """One shipped plugin lifecycle-script execution and its resulting trees."""

    exit_code: int
    stdout: str
    stderr: str
    home_snapshot: tuple[tuple[str, str], ...]
    checkout_snapshot: tuple[tuple[str, str], ...]


@dataclass
class PluginLifecycleHarness:
    """Temporary shipped-plugin, selected-home, and checkout resources."""

    root: Path
    plugin_name: str

    @classmethod
    def create(cls, root: Path, *, plugin_name: str) -> PluginLifecycleHarness:
        harness = cls(root=root, plugin_name=plugin_name)
        harness._materialize_script()
        return harness

    @property
    def skill_root(self) -> Path:
        return self.root / "plugin" / "skills" / f"{self.plugin_name}-plugin"

    @property
    def script_path(self) -> Path:
        return self.skill_root / "scripts" / "place_agents.py"

    @property
    def shipped_agents(self) -> Path:
        return self.skill_root / "agents"

    @property
    def home(self) -> Path:
        return self.root / "codex-home"

    @property
    def home_agents(self) -> Path:
        return self.home / "agents"

    @property
    def ownership_path(self) -> Path:
        return self.home_agents / AGENT_OWNERSHIP_FILENAME

    @property
    def checkout(self) -> Path:
        return self.root / "checkout"

    @property
    def checkout_agents(self) -> Path:
        return self.checkout / CODEX_AGENTS_PATH

    def _materialize_script(self) -> None:
        template = (
            repository_root() / "src/templates/plugin/scripts/place_agents.py"
        ).read_text(encoding="utf-8")
        rendered = render_text(
            template,
            variables={
                BUILD_TARGET_VARIABLE: Target.CODEX.value,
                PLUGIN_NAME_VARIABLE: self.plugin_name,
            },
        )
        self.script_path.parent.mkdir(parents=True, exist_ok=True)
        self.script_path.write_text(rendered, encoding="utf-8")
        self.shipped_agents.mkdir(parents=True, exist_ok=True)
        self.checkout.mkdir(parents=True, exist_ok=True)

    def load_module(self) -> ModuleType:
        """Import the rendered script for in-process race simulation."""
        spec = importlib.util.spec_from_file_location(
            f"place_agents_{self.plugin_name.replace('-', '_')}", self.script_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(
                f"cannot load the placement script module: {self.script_path}"
            )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def definition_name(self, slug: str) -> str:
        """The shipped filename this plugin gives the agent named `slug`."""
        return f"{self.plugin_name}_{slug}.toml"

    def definition_content(self, slug: str) -> bytes:
        """The shipped definition bytes for the agent named `slug`."""
        return f'name = "{self.plugin_name}-{slug}"\n'.encode()

    def ship(self, slug: str) -> Path:
        """Write the shipped definition for `slug` and return its path."""
        return self.write_shipped(
            self.definition_name(slug), self.definition_content(slug)
        )

    def destination_of(self, name: str) -> str:
        """The ownership-record destination for a home agent file name."""
        return f"{CODEX_HOME_AGENTS_PATH.as_posix()}/{name}"

    def ownership_entry(self, name: str, digest: str) -> dict[str, object]:
        """One ownership entry claiming `name` for this plugin at `digest`."""
        return {
            AGENT_OWNERSHIP_DESTINATION_FIELD: self.destination_of(name),
            AGENT_OWNERSHIP_PLUGIN_FIELD: self.plugin_name,
            AGENT_OWNERSHIP_DIGEST_FIELD: digest,
        }

    @staticmethod
    def ownership_document(*entries: Mapping[str, object]) -> dict[str, object]:
        """An ownership record carrying `entries` under the current schema."""
        return {
            AGENT_OWNERSHIP_SCHEMA_FIELD: AGENT_OWNERSHIP_SCHEMA_VERSION,
            AGENT_OWNERSHIP_ENTRIES_FIELD: list(entries),
        }

    def write_shipped(self, name: str, content: bytes) -> Path:
        path = self.shipped_agents / name
        path.write_bytes(content)
        return path

    def write_home(self, name: str, content: bytes) -> Path:
        self.home_agents.mkdir(parents=True, exist_ok=True)
        path = self.home_agents / name
        path.write_bytes(content)
        return path

    def write_checkout(self, name: str, content: bytes) -> Path:
        self.checkout_agents.mkdir(parents=True, exist_ok=True)
        path = self.checkout_agents / name
        path.write_bytes(content)
        return path

    def write_ownership(self, document: Mapping[str, object]) -> None:
        self.home_agents.mkdir(parents=True, exist_ok=True)
        self.ownership_path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def run(self, *, check: bool = False) -> PluginLifecycleRun:
        argv = [
            sys.executable,
            str(self.script_path),
            "--home",
            str(self.home),
            "--checkout",
            str(self.checkout),
        ]
        if check:
            argv.append("--check")
        result = subprocess.run(
            argv,
            cwd=self.checkout,
            capture_output=True,
            text=True,
            check=False,
        )
        return PluginLifecycleRun(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            home_snapshot=self.snapshot(self.home),
            checkout_snapshot=self.snapshot(self.checkout),
        )

    @staticmethod
    def snapshot(root: Path) -> tuple[tuple[str, str], ...]:
        if not root.exists() and not root.is_symlink():
            return ()
        values: list[tuple[str, str]] = []
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                values.append((relative, f"symlink:{os.readlink(path)}"))
            elif path.is_file():
                values.append((relative, path.read_bytes().hex()))
            else:
                values.append((relative, "directory"))
        return tuple(values)

    @staticmethod
    def file_identity(path: Path) -> tuple[int, int, int]:
        metadata = path.stat()
        return metadata.st_ino, metadata.st_mtime_ns, metadata.st_size


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
    """Installation runner that records commands and can fail one operation.

    Controlled under `/test` Stage 5 Interaction protocols: the command order
    and shape a plan emits are observable only by recording the calls at the
    injected runner boundary. Failing one designated operation — narrowed to
    one agent when `failed_agent` is set — is the Stage 5 Failure simulation
    case, because a real CLI does not fail an arbitrary operation on demand.
    It returns observations only.
    """

    failed_operation: Operation | None = None
    installed: Mapping[Agent, frozenset[str]] | None = None
    failed_agent: Agent | None = None
    calls: list[InstallationCommand] = field(default_factory=list)

    def __call__(self, command: InstallationCommand) -> CommandResult:
        self.calls.append(command)
        designated_agent = (
            self.failed_agent is None or command.agent is self.failed_agent
        )
        exit_code = (
            1 if command.operation is self.failed_operation and designated_agent else 0
        )
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
    """One agent's installed listing for `plugins` at the invocation checkout.

    Every second entry is listed disabled, so a selection that must include
    disabled plugins has a disabled member to lose whenever an enabled-state
    filter creeps into selection.
    """
    identifiers = sorted(plugins)
    if agent is Agent.CLAUDE:
        return json.dumps(
            [
                {
                    CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(plugin),
                    CLAUDE_PLUGIN_ENABLED_FIELD: index % 2 == 0,
                    CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                    CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(checkout.resolve()),
                }
                for index, plugin in enumerate(identifiers)
            ]
        )
    return json.dumps(
        {
            CODEX_PLUGIN_ENTRIES_FIELD: [
                {
                    CODEX_PLUGIN_ID_FIELD: marketplace_plugin_identifier(plugin),
                    CODEX_PLUGIN_ENABLED_FIELD: index % 2 == 0,
                    CODEX_PLUGIN_MARKETPLACE_FIELD: MARKETPLACE_NAME,
                }
                for index, plugin in enumerate(identifiers)
            ]
        }
    )


def _marketplace_listing_payload(agent: Agent) -> str:
    """One agent's marketplace listing carrying the canonical registration."""
    if agent is Agent.CLAUDE:
        return claude_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)
    return codex_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)


def _successful_command_payload(
    command: InstallationCommand,
    installed: Mapping[Agent, frozenset[str]] | None,
) -> str:
    if command.operation is Operation.MARKETPLACE_INSPECT:
        return _marketplace_listing_payload(command.agent)
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
    codex_source: str | None,
) -> InstallationPlan:
    """Plan against catalog-wide inventories; `None` leaves both registries empty."""
    inventories = _installed_or_catalog_plugins(preflight.roots.checkout, None)
    return build_persistent_installation_plan(
        preflight,
        claude_marketplace_payload=(
            claude_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)
            if codex_source is not None
            else json.dumps([])
        ),
        claude_plugins_payload=_plugin_listing_payload(
            Agent.CLAUDE,
            preflight.roots.checkout,
            inventories[Agent.CLAUDE],
        ),
        codex_marketplace_payload=(
            codex_marketplace_listing_payload(codex_source)
            if codex_source is not None
            else json.dumps({CODEX_MARKETPLACES_FIELD: []})
        ),
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
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        ambient_environment = _persistent_environment(
            temporary_root / "developer-state"
        )
        plan = build_isolated_installation_plan(
            mirror,
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
    claude_repository: str | None = CANONICAL_MARKETPLACE_SOURCE,
    claude_marketplace_listed: bool = True,
    codex_source: str = CANONICAL_CODEX_SOURCE,
    installed: Mapping[Agent, frozenset[str]] | None = None,
) -> PersistentPlanObservation:
    """Build a persistent plan in caller-selected temporary homes.

    `claude_repository` is the marketplace source the mirrored checkout's
    project settings declare; `None` leaves the checkout declaring none, the
    registration-bootstrap case.
    """
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        if claude_repository is not None:
            _write_project_marketplace(mirror, claude_repository)
        environment = _persistent_environment(temporary_root)
        claude_catalog = (mirror / CLAUDE_CATALOG_PATH).read_bytes()
        codex_catalog = (mirror / CODEX_CATALOG_PATH).read_bytes()
        preflight = build_persistent_preflight(mirror, environment)
        inventories = _installed_or_catalog_plugins(mirror, installed)
        plan = build_persistent_installation_plan(
            preflight,
            claude_marketplace_payload=(
                claude_marketplace_listing_payload(CANONICAL_MARKETPLACE_SOURCE)
                if claude_marketplace_listed
                else json.dumps([])
            ),
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


@dataclass(frozen=True)
class RecordRefreshObservation:
    """One persistent plan built from a generated machine-wide Claude listing.

    Each generated record is paired with the disposition its construction
    implies; the plan's update commands, warnings, and checkout are the
    observations the linked test judges against those dispositions.
    """

    checkout: Path
    other_checkout: Path
    absent_path: Path
    file_path: Path
    forked_checkout: Path
    forked_local_checkout: Path
    local_forked_checkout: Path
    local_canonical_checkout: Path
    malformed_checkout: Path
    denied_checkout: Path
    cases: tuple[tuple[dict[str, str], RecordDisposition], ...]
    plan: InstallationPlan
    catalog: tuple[str, ...]
    report: InstallationReport
    document: dict[str, object]
    attempted: tuple[InstallationCommand, ...]


def observe_record_refresh_plan() -> RecordRefreshObservation:
    """Plan a persistent run against records spread across scopes and paths."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        other = temporary_root / "other-checkout"
        other.mkdir()
        absent = temporary_root / "removed-checkout"
        forked = temporary_root / "forked-checkout"
        forked.mkdir()
        _write_project_marketplace(forked, NONCANONICAL_MARKETPLACE_SOURCE)
        forked_local = temporary_root / "forked-local-checkout"
        forked_local.mkdir()
        _write_project_marketplace(
            forked_local, NONCANONICAL_MARKETPLACE_SOURCE, local=True
        )
        local_forked = temporary_root / "local-forked-checkout"
        local_forked.mkdir()
        _write_project_marketplace(local_forked, CANONICAL_MARKETPLACE_SOURCE)
        _write_project_marketplace(
            local_forked, NONCANONICAL_MARKETPLACE_SOURCE, local=True
        )
        local_canonical = temporary_root / "local-canonical-checkout"
        local_canonical.mkdir()
        _write_project_marketplace(local_canonical, NONCANONICAL_MARKETPLACE_SOURCE)
        _write_project_marketplace(
            local_canonical, CANONICAL_MARKETPLACE_SOURCE, local=True
        )
        regular_file = temporary_root / "regular-file"
        regular_file.write_text("", encoding="utf-8")
        malformed = temporary_root / "malformed-checkout"
        malformed_settings = malformed / CLAUDE_PROJECT_SETTINGS_PATH
        malformed_settings.parent.mkdir(parents=True)
        malformed_settings.write_text(MALFORMED_SETTINGS_CONTENT, encoding="utf-8")
        denied = temporary_root / "denied-checkout"
        denied.mkdir()
        _write_project_marketplace(denied, CANONICAL_MARKETPLACE_SOURCE)
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        preflight = build_persistent_preflight(mirror, environment)
        catalog = _catalogs_from_documents(mirror)[Agent.CLAUDE]
        groups = generated_claude_install_records(
            catalog,
            preflight.roots.checkout,
            other.resolve(),
            absent.resolve(),
            regular_file.resolve(),
            forked.resolve(),
            forked_local.resolve(),
            local_forked.resolve(),
            local_canonical.resolve(),
            malformed.resolve(),
            denied.resolve(),
        )
        cases = tuple(case for group in groups for case in group)
        with _blocked_directory(denied / CLAUDE_PROJECT_SETTINGS_PATH.parent):
            plan = build_persistent_installation_plan(
                preflight,
                claude_marketplace_payload=claude_marketplace_listing_payload(
                    CANONICAL_MARKETPLACE_SOURCE
                ),
                claude_plugins_payload=json.dumps([entry for entry, _ in cases]),
                codex_marketplace_payload=codex_marketplace_listing_payload(
                    CANONICAL_CODEX_SOURCE
                ),
                codex_plugins_payload=_plugin_listing_payload(
                    Agent.CODEX,
                    mirror,
                    frozenset(catalog),
                ),
            )
        runner = RecordingRunner()
        report = execute_installation(plan, runner)
        return RecordRefreshObservation(
            checkout=preflight.roots.checkout,
            other_checkout=other.resolve(),
            absent_path=absent.resolve(),
            file_path=regular_file.resolve(),
            forked_checkout=forked.resolve(),
            forked_local_checkout=forked_local.resolve(),
            local_forked_checkout=local_forked.resolve(),
            local_canonical_checkout=local_canonical.resolve(),
            malformed_checkout=malformed.resolve(),
            denied_checkout=denied.resolve(),
            cases=cases,
            plan=plan,
            catalog=catalog,
            report=report,
            document=report_document(report),
            attempted=tuple(runner.calls),
        )


@dataclass(frozen=True)
class UnreadableSourceObservation:
    """Persistent preflight against an invocation checkout whose settings cannot be read."""

    settings_path: Path
    error: str | None


def observe_unreadable_source() -> UnreadableSourceObservation:
    """Run persistent preflight with the invocation checkout's own settings unreadable.

    The mirrored checkout's project settings carry malformed JSON, which
    preflight reads before any plan; the rejection message, if any, is the
    observation beside the path it names.
    """
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory).resolve()
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        settings = mirror / CLAUDE_PROJECT_SETTINGS_PATH
        settings.parent.mkdir(parents=True, exist_ok=True)
        settings.write_text(MALFORMED_SETTINGS_CONTENT, encoding="utf-8")
        environment = _persistent_environment(temporary_root)
        try:
            build_persistent_preflight(mirror, environment)
        except ValueError as error:
            return UnreadableSourceObservation(settings_path=settings, error=str(error))
    return UnreadableSourceObservation(settings_path=settings, error=None)


def observe_noncanonical_registry_plan() -> str | None:
    """Plan a persistent run whose machine registry names a noncanonical source.

    The invocation checkout declares the canonical source, so the registry
    entry alone carries the mismatch; the rejection message, if any, is the
    observation.
    """
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        preflight = build_persistent_preflight(mirror, environment)
        try:
            build_persistent_installation_plan(
                preflight,
                claude_marketplace_payload=claude_marketplace_listing_payload(
                    NONCANONICAL_MARKETPLACE_SOURCE
                ),
                claude_plugins_payload=_plugin_listing_payload(
                    Agent.CLAUDE, mirror, frozenset({SPEC_TREE_PLUGIN})
                ),
                codex_marketplace_payload=codex_marketplace_listing_payload(
                    CANONICAL_CODEX_SOURCE
                ),
                codex_plugins_payload=_plugin_listing_payload(
                    Agent.CODEX, mirror, frozenset({SPEC_TREE_PLUGIN})
                ),
            )
        except ValueError as error:
            return str(error)
    return None


def observe_noncanonical_source(agent: Agent) -> str | None:
    """Run persistent planning with one agent's own source noncanonical.

    For Claude Code the mirrored checkout's project settings declare the
    noncanonical source, which preflight reads; for Codex the selected home's
    live marketplace listing carries it, which planning reads. The rejection
    message, if any, is the observation.
    """
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(
            mirror,
            NONCANONICAL_MARKETPLACE_SOURCE
            if agent is Agent.CLAUDE
            else CANONICAL_MARKETPLACE_SOURCE,
        )
        environment = _persistent_environment(temporary_root)
        try:
            preflight = build_persistent_preflight(mirror, environment)
            build_persistent_installation_plan(
                preflight,
                claude_marketplace_payload=claude_marketplace_listing_payload(
                    CANONICAL_MARKETPLACE_SOURCE
                ),
                claude_plugins_payload=_plugin_listing_payload(
                    Agent.CLAUDE, mirror, frozenset({SPEC_TREE_PLUGIN})
                ),
                codex_marketplace_payload=codex_marketplace_listing_payload(
                    NONCANONICAL_MARKETPLACE_SOURCE
                    if agent is Agent.CODEX
                    else CANONICAL_CODEX_SOURCE
                ),
                codex_plugins_payload=_plugin_listing_payload(
                    Agent.CODEX, mirror, frozenset({SPEC_TREE_PLUGIN})
                ),
            )
        except ValueError as error:
            return str(error)
    return None


def observe_pathless_record_listing() -> str | None:
    """Plan a persistent run whose Claude listing names a project-scope record with no path.

    The rejection message, if any, is the observation.
    """
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        preflight = build_persistent_preflight(mirror, environment)
        listing = json.dumps(
            [
                {
                    CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(
                        SPEC_TREE_PLUGIN
                    ),
                    CLAUDE_PLUGIN_ENABLED_FIELD: True,
                    CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_PROJECT_SCOPE,
                }
            ]
        )
        try:
            build_persistent_installation_plan(
                preflight,
                claude_marketplace_payload=claude_marketplace_listing_payload(
                    CANONICAL_MARKETPLACE_SOURCE
                ),
                claude_plugins_payload=listing,
                codex_marketplace_payload=codex_marketplace_listing_payload(
                    CANONICAL_CODEX_SOURCE
                ),
                codex_plugins_payload=_plugin_listing_payload(
                    Agent.CODEX, mirror, frozenset({SPEC_TREE_PLUGIN})
                ),
            )
        except ValueError as error:
            return str(error)
    return None


def observe_local_record_bootstrap_plan() -> PersistentPlanObservation:
    """Plan a persistent run whose only Claude record is local scope at the checkout.

    The checkout records `spec-tree` at local scope and nothing at project
    scope, so the inventory is nonempty without a project-scope member; the
    plan's install, enable, and update commands and its warnings are the
    observations the linked test judges.
    """
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        claude_catalog = (mirror / CLAUDE_CATALOG_PATH).read_bytes()
        codex_catalog = (mirror / CODEX_CATALOG_PATH).read_bytes()
        preflight = build_persistent_preflight(mirror, environment)
        listing = json.dumps(
            [
                {
                    CLAUDE_PLUGIN_ID_FIELD: marketplace_plugin_identifier(
                        SPEC_TREE_PLUGIN
                    ),
                    CLAUDE_PLUGIN_ENABLED_FIELD: True,
                    CLAUDE_PLUGIN_SCOPE_FIELD: CLAUDE_LOCAL_SCOPE,
                    CLAUDE_PLUGIN_PROJECT_PATH_FIELD: str(preflight.roots.checkout),
                }
            ]
        )
        plan = build_persistent_installation_plan(
            preflight,
            claude_marketplace_payload=claude_marketplace_listing_payload(
                CANONICAL_MARKETPLACE_SOURCE
            ),
            claude_plugins_payload=listing,
            codex_marketplace_payload=codex_marketplace_listing_payload(
                CANONICAL_CODEX_SOURCE
            ),
            codex_plugins_payload=_plugin_listing_payload(
                Agent.CODEX, mirror, frozenset({SPEC_TREE_PLUGIN})
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
        mirror_installation_inputs(checkout, mirror)
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
    """Build persistent plans for every valid subset of each agent catalog.

    Each nonempty listing carries one plugin the committed catalog does not
    name beside the selected subset, so a plan that admits a reported plugin
    from outside the catalog has a member to be caught on; the empty listing
    stays empty so the bootstrap case keeps its shape.
    """
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
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
                installed[agent] = (
                    selected | {UNCATALOGED_PLUGIN} if selected else selected
                )
                plan = build_persistent_installation_plan(
                    preflight,
                    claude_marketplace_payload=claude_marketplace_listing_payload(
                        CANONICAL_MARKETPLACE_SOURCE
                    ),
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
                        updates=tuple(
                            command.plugin
                            for command in plan.commands
                            if command.agent is agent
                            and command.operation is Operation.PLUGIN_UPDATE
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


def observe_agent_home_reconciliation() -> AgentHomeReconciliationObservation:
    """Install selected-home agents, then remove one from the desired catalog set."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        agents_root = Path(environment[CODEX_HOME_ENV]) / CODEX_HOME_AGENTS_PATH
        foreign = agents_root / UNOWNED_AGENT_FILENAME
        foreign.parent.mkdir(parents=True, exist_ok=True)
        foreign.write_text(UNOWNED_AGENT_CONTENT, encoding="utf-8")
        foreign_initial = foreign.read_bytes()
        home_initial = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))

        first_preflight = build_persistent_preflight(mirror, environment)
        desired_first = _shipped_agent_snapshot(mirror)
        first_report = execute_persistent_installation(
            mirror,
            environment,
            RecordingRunner(),
        )
        first_result = first_report.agent_home
        if first_result is None:
            raise RuntimeError("persistent installation returned no agent-home result")
        home_first = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))
        foreign_first = foreign.read_bytes()

        retired = first_preflight.codex_agents[0]
        retired.source.unlink()
        desired_second = _shipped_agent_snapshot(mirror)
        second_report = execute_persistent_installation(
            mirror,
            environment,
            RecordingRunner(),
        )
        second_result = second_report.agent_home
        if second_result is None:
            raise RuntimeError("persistent installation returned no agent-home result")
        home_second = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))
        foreign_second = foreign.read_bytes()
        ownership_record_present = (agents_root / AGENT_OWNERSHIP_FILENAME).is_file()

    return AgentHomeReconciliationObservation(
        desired_first=desired_first,
        desired_second=desired_second,
        home_initial=home_initial,
        home_first=home_first,
        home_second=home_second,
        foreign_initial=foreign_initial,
        foreign_first=foreign_first,
        foreign_second=foreign_second,
        first_result=first_result,
        second_result=second_result,
        ownership_record_present=ownership_record_present,
    )


@dataclass(frozen=True)
class InterruptedReconciliationObservation:
    """Home state across an install, a lost ownership record, and a re-run."""

    first_result: AgentHomeResult
    second_result: AgentHomeResult
    home_first: tuple[tuple[str, bytes], ...]
    home_second: tuple[tuple[str, bytes], ...]
    record_present_after: bool


def observe_interrupted_reconciliation() -> InterruptedReconciliationObservation:
    """Install, drop the ownership record as an interrupted run would, re-run."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        agents_root = Path(environment[CODEX_HOME_ENV]) / CODEX_HOME_AGENTS_PATH

        first_report = execute_persistent_installation(
            mirror,
            environment,
            RecordingRunner(),
        )
        first_result = first_report.agent_home
        if first_result is None:
            raise RuntimeError("persistent installation returned no agent-home result")
        home_first = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))
        (agents_root / AGENT_OWNERSHIP_FILENAME).unlink()

        second_report = execute_persistent_installation(
            mirror,
            environment,
            RecordingRunner(),
        )
        second_result = second_report.agent_home
        if second_result is None:
            raise RuntimeError("persistent installation returned no agent-home result")
        home_second = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))
        record_present_after = (agents_root / AGENT_OWNERSHIP_FILENAME).is_file()

    return InterruptedReconciliationObservation(
        first_result=first_result,
        second_result=second_result,
        home_first=home_first,
        home_second=home_second,
        record_present_after=record_present_after,
    )


def observe_agent_home_collision() -> AgentHomeCollisionObservation:
    """Occupy one desired destination without ownership before installation."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        preflight = build_persistent_preflight(mirror, environment)
        destination = preflight.codex_agents[0].destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text('name = "foreign-definition"\n', encoding="utf-8")
        home_before = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))
        runner = RecordingRunner()
        collisions: tuple[AgentHomeCollision, ...] = ()
        try:
            execute_persistent_installation(mirror, environment, runner)
        except AgentHomeCollisionError as error:
            collisions = error.collisions
        home_after = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))
    return AgentHomeCollisionObservation(
        collisions=collisions,
        attempted=tuple(runner.calls),
        home_before=home_before,
        home_after=home_after,
    )


def skill_enabling_definition(plugin: str) -> bytes:
    """A definition carrying no plugin filename prefix that enables one plugin skill."""
    return (
        'name = "local-helper"\n'
        f"[[{AGENT_SKILLS_FIELD}.{AGENT_SKILLS_CONFIG_FIELD}]]\n"
        f'{AGENT_SKILL_NAME_FIELD} = "{plugin}:{RENAMED_CHECKOUT_SKILL_NAME}"\n'
        f"{AGENT_SKILL_ENABLED_FIELD} = true\n"
    ).encode("utf-8")


def observe_scope_split() -> ScopeSplitObservation:
    """Place exact and changed plugin definitions in the checkout before install."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        _write_project_marketplace(mirror, CANONICAL_MARKETPLACE_SOURCE)
        environment = _persistent_environment(temporary_root)
        preflight = build_persistent_preflight(mirror, environment)
        exact = preflight.codex_agents[0]
        changed = preflight.codex_agents[1]
        checkout_agents = mirror / CODEX_AGENTS_PATH
        checkout_agents.mkdir(parents=True, exist_ok=True)
        (checkout_agents / exact.destination.name).write_bytes(exact.content)
        (checkout_agents / changed.destination.name).write_bytes(
            changed.content + b"# locally changed\n"
        )
        (checkout_agents / f"{changed.plugin}_symlink.toml").symlink_to(changed.source)
        (checkout_agents / RENAMED_CHECKOUT_AGENT_NAME).write_bytes(
            skill_enabling_definition(changed.plugin)
        )
        home_before = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))
        runner = RecordingRunner()
        entries: tuple[ScopeSplitEntry, ...] = ()
        try:
            execute_persistent_installation(mirror, environment, runner)
        except ScopeSplitError as error:
            entries = error.entries
        home_after = _agent_snapshot(Path(environment[CODEX_HOME_ENV]))
    return ScopeSplitObservation(
        entries=entries,
        attempted=tuple(runner.calls),
        home_before=home_before,
        home_after=home_after,
    )


def observe_claude_user_collision() -> CollisionObservation:
    """Expose user-scope collision rejection before command execution."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
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
        mirror_installation_inputs(checkout, mirror)
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
        mirror_installation_inputs(checkout, mirror)
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
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        try:
            build_isolated_installation_plan(
                mirror,
                temporary_root / "state",
                os.environ,
                claude_plugins=tuple(invalid[Agent.CLAUDE]),
                codex_plugins=tuple(invalid[Agent.CODEX]),
            )
        except ValueError as error:
            rejection = str(error)
    return SelectionRejectionObservation(error=rejection, attempted=())


@dataclass(frozen=True)
class IsolatedSubsetPlanObservation:
    """Catalog and plan observations for one explicit isolated subset."""

    plan: InstallationPlan
    subsets: Mapping[Agent, frozenset[str]]
    claude_catalog: bytes
    codex_catalog: bytes


def observe_isolated_subset_plan() -> IsolatedSubsetPlanObservation:
    """Build an isolated plan from one generated valid explicit subset."""
    checkout = repository_root()
    subsets = generated_agent_subsets(checkout, include_spec_tree=True)
    claude_catalog = (checkout / CLAUDE_CATALOG_PATH).read_bytes()
    codex_catalog = (checkout / CODEX_CATALOG_PATH).read_bytes()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
        plan = build_isolated_installation_plan(
            mirror,
            temporary_root / "state",
            os.environ,
            claude_plugins=tuple(subsets[Agent.CLAUDE]),
            codex_plugins=tuple(subsets[Agent.CODEX]),
        )
    return IsolatedSubsetPlanObservation(
        plan=plan,
        subsets=subsets,
        claude_catalog=claude_catalog,
        codex_catalog=codex_catalog,
    )


def observe_missing_codex_home() -> str | None:
    """Expose the rejection, if any, when no Codex home is selected."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
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
    an absent registration is added, so both persistent variants are needed to
    cover the marketplace operation vocabulary.
    """
    checkout = repository_root()
    isolated_checkout = temporary_root / "isolated-checkout"
    mirror_installation_inputs(checkout, isolated_checkout)
    isolated = build_isolated_installation_plan(
        isolated_checkout,
        temporary_root / "isolated",
        os.environ,
    )
    plans = [isolated]
    for index, source in enumerate((None, CANONICAL_MARKETPLACE_SOURCE)):
        mirror = temporary_root / f"checkout-{index}"
        mirror_installation_inputs(checkout, mirror)
        if source is not None:
            _write_project_marketplace(mirror, source)
        environment = _persistent_environment(temporary_root / f"state-{index}")
        preflight = build_persistent_preflight(mirror, environment)
        plans.append(_persistent_plan_with_catalog_inventories(preflight, source))
    return tuple(plans)


def observe_planned_operations() -> tuple[Operation, ...]:
    """Expose every operation a repository-installation plan performs.

    An isolated plan registers fresh sources, so it never carries the
    marketplace refresh operation a persistent plan performs against an
    already-registered source. The union across every plan is the
    domain of operations a plan itself performs; the persistent preflight's
    marketplace inspection fails outside any plan and is exposed separately.
    """
    with TemporaryDirectory() as temporary_directory:
        plans = _installation_plans(Path(temporary_directory))
    return tuple(
        dict.fromkeys(command.operation for plan in plans for command in plan.commands)
    )


def observe_inspection_failure() -> FailureObservation:
    """Fail the persistent preflight's marketplace inspection before any plan."""
    checkout = repository_root()
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        mirror_installation_inputs(checkout, mirror)
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
                (CHECKOUT_OPTION, str(mirror), JSON_OUTPUT_OPTION),
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


def observe_first_failure(
    operation: Operation,
    *,
    agent: Agent | None = None,
) -> FailureObservation:
    """Fail a selected plan operation through the public CLI surface."""
    with TemporaryDirectory() as temporary_directory:
        plans = _installation_plans(Path(temporary_directory))
        plan = next(
            candidate
            for candidate in plans
            if any(
                command.operation is operation
                and (agent is None or command.agent is agent)
                for command in candidate.commands
            )
        )
        runner = RecordingRunner(failed_operation=operation, failed_agent=agent)
        environment = dict(plan.commands[0].environment)
        arguments = [CHECKOUT_OPTION, str(plan.roots.checkout), JSON_OUTPUT_OPTION]
        if plan.mode is InstallationMode.ISOLATED:
            if plan.roots.state is None:
                raise RuntimeError("isolated plan must declare its state root")
            arguments.extend((STATE_ROOT_OPTION, str(plan.roots.state)))
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
        mirror_installation_inputs(checkout, mirror)
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
    real_just = _required_binary(JUST_BINARY)
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        invocation_path = temporary_root / "invocation.json"
        shim_directory = temporary_root / "bin"
        shim_directory.mkdir()
        shim = shim_directory / JUST_BINARY
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
@dataclass(frozen=True)
class RealRecordRefreshObservation:
    """A real persistent run over records in the invocation checkout and a second one.

    The second checkout records its plugin at local scope, so the run's native
    update executes at that scope from that checkout's own path.
    """

    exit_code: int
    stdout: str
    stderr: str
    invocation_checkout: Path
    other_checkout: Path
    records_before: tuple[ClaudeInstallRecord | PathlessInstallRecord, ...]
    records_after: tuple[ClaudeInstallRecord | PathlessInstallRecord, ...]
    invocation_activation_before: object
    invocation_activation_after: object
    other_activation_before: object
    other_activation_after: object


def observe_real_record_refresh() -> RealRecordRefreshObservation:
    """Seed two checkouts' records with the real Claude Code CLI, then run the recipe.

    The invocation checkout records `spec-tree` at project scope and a second
    checkout records it at local scope with the canonical source declared in
    its local settings; the persistent recipe then runs from the invocation
    checkout against the same disposable agent state.
    """
    checkout = repository_root()
    _require_binaries(REQUIRED_BINARIES)
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory).resolve()
        invocation = temporary_root / "invocation-checkout"
        other = temporary_root / "other-checkout"
        mirror_installation_inputs(checkout, invocation)
        mirror_installation_inputs(checkout, other)
        environment = _persistent_environment(temporary_root / "agent-state")
        _prepare_agent_state(environment)
        _register_persistent_claude_marketplace(invocation, environment)
        _register_persistent_codex_marketplace(invocation, environment)
        _write_project_marketplace(other, CANONICAL_MARKETPLACE_SOURCE, local=True)
        _install_claude_plugin(invocation, environment, CLAUDE_PROJECT_SCOPE)
        _install_claude_plugin(other, environment, CLAUDE_LOCAL_SCOPE)
        invocation_settings = invocation / CLAUDE_PROJECT_SETTINGS_PATH
        other_settings = other / CLAUDE_LOCAL_SETTINGS_PATH
        invocation_activation_before = _declared_activation(invocation_settings)
        other_activation_before = _declared_activation(other_settings)
        records_before = claude_install_records(
            _run_listing(Agent.CLAUDE, invocation, environment).stdout
        )
        result = _run_persistent_recipe(checkout, invocation, environment)
        records_after = claude_install_records(
            _run_listing(Agent.CLAUDE, invocation, environment).stdout
        )
        invocation_activation_after = _declared_activation(invocation_settings)
        other_activation_after = _declared_activation(other_settings)
    return RealRecordRefreshObservation(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        invocation_checkout=invocation,
        other_checkout=other,
        records_before=records_before,
        records_after=records_after,
        invocation_activation_before=invocation_activation_before,
        invocation_activation_after=invocation_activation_after,
        other_activation_before=other_activation_before,
        other_activation_after=other_activation_after,
    )


def _install_claude_plugin(
    checkout: Path, environment: Mapping[str, str], scope: str
) -> None:
    """Install `spec-tree` at one scope from one checkout through the real CLI."""
    result = subprocess.run(
        (
            CLAUDE_EXECUTABLE,
            "plugin",
            "install",
            marketplace_plugin_identifier(SPEC_TREE_PLUGIN),
            CLAUDE_SCOPE_FLAG,
            scope,
        ),
        cwd=checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Claude {scope}-scope install in {checkout} failed with exit "
            f"{result.returncode}: {result.stderr}"
        )


def _declared_activation(settings: Path) -> object:
    """Read the activation entries one settings document declares, as written."""
    return _settings_json(settings).get(CLAUDE_ENABLED_PLUGINS_FIELD)


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
        mirror_installation_inputs(checkout, persistent_mirror)
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
        # The seed installs from the canonical marketplace, so it can seed only
        # the plugins that marketplace publishes. A checkout plugin the
        # marketplace has not published can never be installed state, so the
        # persistent run never selects it; the pending-publication carve-out is
        # exercised by the l1 scenario evidence with simulated agent output.
        published = canonical_catalog_plugin_names()
        persistent_subsets = {
            agent: subset & published
            for agent, subset in generated_agent_subsets(
                persistent_mirror,
                include_spec_tree=True,
            ).items()
        }
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
        persistent_claude_marketplaces = _run_claude_marketplace_listing(
            persistent_mirror,
            selected_environment,
        )
        persistent_plan = build_persistent_installation_plan(
            persistent_preflight,
            claude_marketplace_payload=persistent_claude_marketplaces.stdout,
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
        mirror_installation_inputs(checkout, mirror)
        claude_catalog = (mirror / CLAUDE_CATALOG_PATH).read_bytes()
        codex_catalog = (mirror / CODEX_CATALOG_PATH).read_bytes()
        shipped_agents = _shipped_agent_snapshot(mirror)
        persistent_root = temporary_root / "persistent"
        persistent_environment = _persistent_environment(persistent_root)
        _seed_persistent_state(persistent_root)
        persistent_initial = _tree_snapshot(persistent_root)
        unowned = state / "codex" / CODEX_HOME_AGENTS_PATH / UNOWNED_AGENT_FILENAME
        unowned.parent.mkdir(parents=True, exist_ok=True)
        unowned.write_text(UNOWNED_AGENT_CONTENT, encoding="utf-8")
        unowned_initial = unowned.read_bytes()
        placed_initial = _agent_snapshot(state / "codex")
        plan = build_isolated_installation_plan(mirror, state, persistent_environment)
        environment = dict(plan.commands[0].environment)
        claude_target = _registration_target(plan, Agent.CLAUDE)
        codex_target = _registration_target(plan, Agent.CODEX)
        state_roots = _state_roots(plan)
        with _blocked_directory(persistent_root) as read_blocked_mode:
            first = _run_recipe(checkout, mirror, state, environment)
            persistent_mode_first = read_blocked_mode()
        claude_first = _run_listing(Agent.CLAUDE, mirror, environment)
        codex_first = _run_listing(Agent.CODEX, mirror, environment)
        placed_first = _agent_snapshot(state / "codex")
        unowned_first = unowned.read_bytes()
        persistent_first = _tree_snapshot(persistent_root)
        with _blocked_directory(persistent_root) as read_blocked_mode:
            second = _run_recipe(checkout, mirror, state, environment)
            persistent_mode_second = read_blocked_mode()
        claude_second = _run_listing(Agent.CLAUDE, mirror, environment)
        codex_second = _run_listing(Agent.CODEX, mirror, environment)
        placed_second = _agent_snapshot(state / "codex")
        unowned_second = unowned.read_bytes()
        persistent_second = _tree_snapshot(persistent_root)
        subset_mirror = temporary_root / "subset-checkout"
        subset_state = temporary_root / "subset-state"
        mirror_installation_inputs(checkout, subset_mirror)
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


@dataclass(frozen=True)
class CodexSubagentDiscoveryObservation:
    """One fresh non-interactive Codex session's subagent discovery over a home.

    Observations only: the isolated installation result that populated the
    disposable home, the login and session command results, the parsed subagent names
    the session reported, and the canonical subagent names placed under that home.
    The linked test owns every predicate.
    """

    install_exit_code: int
    install_stderr: str
    login_exit_code: int
    login_stderr: str
    session_exit_code: int
    session_stderr: str
    session_last_message: str
    discovered_subagent_names: frozenset[str] | None
    placed_subagent_names: frozenset[str]
    codex_home: Path


def observe_codex_subagent_discovery(
    *,
    environment: Mapping[str, str] | None = None,
    runner: ProbeRunner = run_probe_process,
) -> CodexSubagentDiscoveryObservation:
    """Install disposable state, authenticate explicitly, and read the registry."""
    original_environment = os.environ if environment is None else environment
    auth = DiscoveryAuthentication(select_authentication(original_environment), runner)
    checkout = repository_root()
    _require_binaries(REQUIRED_BINARIES)
    with TemporaryDirectory() as temporary_directory:
        temporary_root = Path(temporary_directory)
        mirror = temporary_root / "checkout"
        state = temporary_root / "state"
        mirror_installation_inputs(checkout, mirror)
        plan = build_isolated_installation_plan(
            mirror, state, credential_free_environment(original_environment)
        )
        child_environment = dict(plan.commands[0].environment)
        install = auth.run(
            (
                JUST_BINARY,
                "install-marketplace",
                CHECKOUT_OPTION,
                str(mirror),
                STATE_ROOT_OPTION,
                str(state),
                JSON_OUTPUT_OPTION,
            ),
            cwd=checkout,
            env=child_environment,
        )
        if install.returncode != 0:
            raise DiscoveryAuthenticationError(
                f"Discovery installation failed ({install.returncode}): {install.stderr}"
            )
        codex_home = state / "codex"
        placed_subagent_names = _placed_subagent_names(codex_home)
        schema_path = temporary_root / "subagent-discovery-schema.json"
        schema_path.write_text(
            json.dumps(SUBAGENT_DISCOVERY_OUTPUT_SCHEMA), encoding="utf-8"
        )
        last_message_path = temporary_root / "subagent-discovery-last-message.json"
        with auth.authenticated_home(
            codex_home, cwd=mirror, env=child_environment
        ) as login:
            session = auth.run(
                (
                    CODEX_EXECUTABLE,
                    *FILE_STORE_ARGS,
                    CODEX_EXEC_SUBCOMMAND,
                    "--ephemeral",
                    "--skip-git-repo-check",
                    "-C",
                    str(mirror),
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(last_message_path),
                    SUBAGENT_DISCOVERY_PROMPT,
                ),
                cwd=mirror,
                env=child_environment,
            )
            last_message = (
                last_message_path.read_text(encoding="utf-8")
                if last_message_path.exists()
                else ""
            )
        scrubbed_last_message = auth.redactor.clean(last_message)
        return CodexSubagentDiscoveryObservation(
            install_exit_code=install.returncode,
            install_stderr=auth.redactor.clean(install.stderr),
            login_exit_code=login.returncode,
            login_stderr=auth.redactor.clean(login.stderr),
            session_exit_code=session.returncode,
            session_stderr=auth.redactor.clean(session.stderr),
            session_last_message=scrubbed_last_message,
            discovered_subagent_names=_discovered_subagent_names(scrubbed_last_message),
            placed_subagent_names=placed_subagent_names,
            codex_home=codex_home,
        )


def racing_digest_reader(
    target: Path,
    inject: Callable[[], None],
    real: Callable[[Path], str | None],
) -> Callable[[Path], str | None]:
    """Digest reader whose second read of ``target`` runs ``inject`` first.

    Controlled collaborator under `/test` Stage 5 exception 3 (Time and
    concurrency): a writer racing the run between preflight and mutation
    cannot be scheduled deterministically against the real filesystem.
    """
    calls: dict[Path, int] = {}

    def reader(path: Path) -> str | None:
        calls[path] = calls.get(path, 0) + 1
        if path == target and calls[path] == 2:
            inject()
        return real(path)

    return reader


def _placed_subagent_names(codex_home: Path) -> frozenset[str]:
    """Read the subagent name each placed definition declares under the home."""
    names: set[str] = set()
    for _, content in _agent_snapshot(codex_home):
        document = tomllib.loads(content.decode("utf-8"))
        name = document.get(AGENT_NAME_FIELD)
        if isinstance(name, str):
            names.add(name)
    return frozenset(names)


def _discovered_subagent_names(last_message: str) -> frozenset[str] | None:
    """Parse the session's structured answer; ``None`` when it is not the schema."""
    try:
        document = json.loads(last_message)
    except json.JSONDecodeError:
        return None
    if not isinstance(document, dict):
        return None
    subagents = document.get(SUBAGENT_DISCOVERY_NAMES_FIELD)
    if not isinstance(subagents, list) or not all(
        isinstance(name, str) for name in subagents
    ):
        return None
    return frozenset(subagents)


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
    installed: set[str] = set()
    enabled_names: set[str] = set()
    for entry in _listing_entries(agent, payload):
        plugin_id, enabled = _listed_identity(agent, entry)
        name = marketplace_plugin_name(plugin_id)
        if name is None:
            continue
        installed.add(name)
        if enabled:
            enabled_names.add(name)
    return PluginListing(
        installed=frozenset(installed),
        enabled=frozenset(enabled_names),
    )


def mirror_installation_inputs(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative_path in (CODEX_CATALOG_PATH, CLAUDE_CATALOG_PATH):
        target = destination / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative_path, target)
    shutil.copytree(
        source / DIST_CODEX_PLUGINS_DIR, destination / DIST_CODEX_PLUGINS_DIR
    )
    shutil.copytree(source / CLAUDE_DIST_RELATIVE, destination / CLAUDE_DIST_RELATIVE)


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
    return frozenset(
        plugin
        for identifier, active in enabled.items()
        if active is True
        and (plugin := marketplace_plugin_name(identifier)) is not None
    )


def _write_project_marketplace(
    checkout: Path, repository: str, *, local: bool = False
) -> None:
    """Declare the marketplace source in a checkout's project or local settings."""
    settings = checkout / (
        CLAUDE_LOCAL_SETTINGS_PATH if local else CLAUDE_PROJECT_SETTINGS_PATH
    )
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
            JUST_BINARY,
            "install-marketplace",
            CHECKOUT_OPTION,
            str(mirror),
            STATE_ROOT_OPTION,
            str(state),
            JSON_OUTPUT_OPTION,
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
            JUST_BINARY,
            "install-marketplace",
            CHECKOUT_OPTION,
            str(mirror),
            JSON_OUTPUT_OPTION,
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
            CLAUDE_EXECUTABLE,
            "plugin",
            "marketplace",
            "add",
            CANONICAL_MARKETPLACE_SOURCE,
            CLAUDE_SCOPE_FLAG,
            CLAUDE_PROJECT_SCOPE,
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
            CODEX_EXECUTABLE,
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
                CLAUDE_EXECUTABLE,
                "plugin",
                "install",
                marketplace_plugin_identifier(plugin),
                CLAUDE_SCOPE_FLAG,
                CLAUDE_PROJECT_SCOPE,
            ),
        )
        for plugin in sorted(selections[Agent.CLAUDE])
    ) + tuple(
        (
            Agent.CODEX,
            (
                CODEX_EXECUTABLE,
                "plugin",
                "add",
                marketplace_plugin_identifier(plugin),
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
    argv = CLAUDE_LIST_COMMAND if agent is Agent.CLAUDE else CODEX_LIST_COMMAND
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


def _run_claude_marketplace_listing(
    checkout: Path,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        CLAUDE_MARKETPLACE_LIST_COMMAND,
        cwd=checkout,
        env=dict(environment),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude marketplace listing failed: {result.stderr.strip()}"
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


def _agent_snapshot(codex_home: Path) -> tuple[tuple[str, bytes], ...]:
    directory = codex_home / CODEX_HOME_AGENTS_PATH
    return tuple(
        (path.name, path.read_bytes()) for path in sorted(directory.glob("*.toml"))
    )


def _shipped_agent_snapshot(checkout: Path) -> tuple[tuple[str, bytes], ...]:
    """Read the shipped Codex agent definitions straight from the generated tree.

    The snapshot is independent of the production preflight, so a narrowed
    definition collection there cannot narrow the expectation with it.
    """
    shipped: dict[str, bytes] = {}
    definitions = (checkout / DIST_CODEX_PLUGINS_DIR).glob("*/skills/*/agents/*.toml")
    for definition in sorted(definitions):
        if definition.name in shipped:
            raise RuntimeError(
                f"duplicate shipped Codex agent definition: {definition.name}"
            )
        shipped[definition.name] = definition.read_bytes()
    return tuple(sorted(shipped.items()))


# Transcribed verbatim from each real agent CLI's install failure against a
# canonical marketplace that had not published the named plugin; independent of
# the production fragment constant so a drifted constant fails the linked tests.
_CAPTURED_UNPUBLISHED_PLUGIN_STDERR: Mapping[Agent, str] = {
    Agent.CLAUDE: (
        'Failed to install plugin "{plugin}@{marketplace}": '
        'Plugin "{plugin}" not found in marketplace "{marketplace}".'
    ),
    Agent.CODEX: (
        "Error: plugin `{plugin}` was not found in marketplace `{marketplace}`"
    ),
}


def captured_unpublished_plugin_stderr(agent: Agent, plugin: str) -> str:
    """One agent CLI's observed unpublished-plugin install failure wording."""
    return _CAPTURED_UNPUBLISHED_PLUGIN_STDERR[agent].format(
        plugin=plugin,
        marketplace=MARKETPLACE_NAME,
    )


@contextmanager
def _blocked_directory(path: Path) -> Iterator[Callable[[], int]]:
    original_mode = stat.S_IMODE(path.stat().st_mode)
    path.chmod(0)
    try:
        yield lambda: stat.S_IMODE(path.stat().st_mode)
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
    "AgentHomeCollisionObservation",
    "InterruptedReconciliationObservation",
    "AgentHomeReconciliationObservation",
    "CodexSubagentDiscoveryObservation",
    "CollisionObservation",
    "ConfigObservation",
    "FailureObservation",
    "PersistentExecutionObservation",
    "PersistentPlanObservation",
    "PlanObservation",
    "PluginLifecycleHarness",
    "PluginLifecycleRun",
    "DesignatedFailureRunner",
    "RealInstallationObservation",
    "RecordingRunner",
    "ScopeSplitClassification",
    "ScopeSplitObservation",
    "UnpublishedPluginObservation",
    "UnpublishedPluginRunner",
    "VerificationRecipeObservation",
    "canonical_catalog_plugin_names",
    "committed_catalog_plugin_names",
    "observe_agent_home_collision",
    "observe_interrupted_reconciliation",
    "observe_agent_home_reconciliation",
    "observe_claude_user_collision",
    "observe_codex_config_independence",
    "observe_codex_subagent_discovery",
    "observe_designated_failure",
    "observe_first_failure",
    "observe_failure_operation_domains",
    "observe_inspection_failure",
    "observe_invalid_isolated_selection",
    "observe_invalid_persistent_selection",
    "observe_invalid_persistent_selections",
    "observe_missing_codex_home",
    "observe_persistent_execution",
    "observe_persistent_catalog_subset_plans",
    "observe_persistent_plan",
    "observe_record_refresh_plan",
    "observe_local_record_bootstrap_plan",
    "observe_noncanonical_registry_plan",
    "RecordRefreshObservation",
    "observe_planned_operations",
    "observe_real_installation",
    "observe_real_record_refresh",
    "observe_repository_plan",
    "observe_scope_split",
    "racing_digest_reader",
    "skill_enabling_definition",
    "RENAMED_CHECKOUT_AGENT_NAME",
    "FOREIGN_DEFINITION_CONTENT",
    "EXTERNAL_DEFINITION_CONTENT",
    "CONCURRENT_EDIT_CONTENT",
    "MALFORMED_OWNERSHIP_DIGEST",
    "RENAMED_CHECKOUT_SKILL_NAME",
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
                stderr=captured_unpublished_plugin_stderr(
                    command.agent,
                    command.plugin,
                ),
            )
        stdout = (
            _marketplace_listing_payload(command.agent)
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
            _marketplace_listing_payload(command.agent)
            if command.operation is Operation.MARKETPLACE_INSPECT
            else ""
        )
        return CommandResult(argv=command.argv, exit_code=0, stdout=stdout, stderr="")


def _build_run_plan(
    temporary_root: Path, *, isolated: bool, source: str | None
) -> InstallationPlan:
    """One installation plan of the selected mode and configured source.

    `None` is the registration-bootstrap variant: the checkout declares no
    marketplace and neither agent's live listing carries it.
    """
    mirror = temporary_root / "checkout"
    mirror_installation_inputs(repository_root(), mirror)
    if isolated:
        return build_isolated_installation_plan(
            mirror, temporary_root / "state", os.environ
        )
    if source is not None:
        _write_project_marketplace(mirror, source)
    environment = _persistent_environment(temporary_root)
    preflight = build_persistent_preflight(mirror, environment)
    codex_source = (
        CANONICAL_CODEX_SOURCE if source == CANONICAL_MARKETPLACE_SOURCE else source
    )
    return _persistent_plan_with_catalog_inventories(preflight, codex_source)


def observe_failure_operation_domains() -> tuple[
    tuple[InstallationMode, str | None, tuple[Operation, ...]], ...
]:
    """Expose reachable operations for every mode and source plan variant.

    The persistent variants are an absent registration, which the plan adds,
    and the canonical source, which it refreshes.
    """
    sources: tuple[str | None, ...] = (None, CANONICAL_MARKETPLACE_SOURCE)
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
    source: str | None = CANONICAL_MARKETPLACE_SOURCE,
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
    source: str | None = CANONICAL_MARKETPLACE_SOURCE,
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
