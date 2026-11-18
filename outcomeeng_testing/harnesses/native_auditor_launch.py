"""Drive every native auditor-dispatch row at the process boundary.

The runner completes every installation and parent-session command it receives
and records each one, under the `/test` Stage 5 interaction-protocols and
failure-simulation exceptions: the evidence concerns the shape and environment
of the commands the producer issues and the state it materializes, which a real
dispatch would hide behind a model turn and a credentialed account. Saved-login
writes go to the credential runner the authentication case already owns. The
harness exposes observations only.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final, cast

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    CLAUDE_EXECUTABLE,
    CODEX_HOME_CONFIG_PATH,
    CODEX_HOME_ENV,
)
from outcomeeng.distribution.native_auditor_dispatch import (
    AGENTS_DIRECTORY,
    BLOCKED_MARKER,
    FIXTURE_DIRECTORY,
    GIT_EXECUTABLE,
    NativeAuditorDispatchObservation,
    NativeAuditorRow,
    materialize_native_auditor,
    native_auditor_rows,
    record_native_auditor_failure,
    run_native_auditor_row,
)
from outcomeeng.validation.implementation_audit_contract import (
    EVENT_RUN_ID_FIELD,
    RUN_EVENTS_FIELD,
    RUN_TERMINAL_STATUS_FIELD,
    RUN_TOKEN_FIELD,
    AuditTerminalStatus,
)
from outcomeeng_testing.harnesses.discovery_auth import AUTH_FILENAME
from outcomeeng_testing.harnesses.discovery_auth_cases import (
    NativeCall,
    NativeCredentialRunner,
    NativeFault,
)
from outcomeeng_testing.harnesses.installation import repository_root
from outcomeeng_testing.harnesses.native_auditor_dispatch import (
    run_native_auditor_dispatch,
)
from outcomeeng_testing.generators.native_auditor_dispatch import (
    UnboundedGrant,
    definition_with_tool_grants,
    definition_with_unbounded_grant,
)
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
    NativeProfileInterval,
    run_native_rows,
)
from outcomeeng_testing.harnesses.native_profile_failures import NativeFailureRunner
from outcomeeng_testing.harnesses.native_profile_launch import (
    RecordingRunner,
    RowLaunch,
    ambient_environment,
    launch_case,
    row_launches,
)


GIT_DIRECTORY: Final = ".git"
"""The fixture repository's own store, left out of the materialized state."""
GIT_READ_TIMEOUT_SECONDS: Final = 30

PLANTED_RUN_TOKEN = "2026-01-02_03-04-05-678-0123456789ab"
PLANTED_RUN_FILE_NAME = f"run-{PLANTED_RUN_TOKEN}.jsonl"
PLANTED_RUN_FILE = f"runs/{PLANTED_RUN_FILE_NAME}"
PLANTED_TERMINAL_STATUS = AuditTerminalStatus.APPROVED.value
PLANTED_PROJECTION: Final[Mapping[str, object]] = {
    RUN_TOKEN_FIELD: PLANTED_RUN_TOKEN,
    RUN_TERMINAL_STATUS_FIELD: PLANTED_TERMINAL_STATUS,
    RUN_EVENTS_FIELD: [{EVENT_RUN_ID_FIELD: PLANTED_RUN_FILE_NAME}],
}
PLANTED_PROJECTION_QUOTING_BLOCKED: Final[Mapping[str, object]] = {
    **PLANTED_PROJECTION,
    "summary": f"A finding quotes the word {BLOCKED_MARKER}.",
}


class LaunchReturn(Enum):
    """What the dispatched auditor returns to the parent session."""

    RUN_TOKEN = "run-token"
    FREE_FORM = "free-form"
    PROJECTION_QUOTING_BLOCKED = "projection-quoting-blocked"
    PROJECTION_ONLY = "projection-only"
    UNSTRUCTURED = "unstructured"
    BLOCKED = "blocked"


def _returned_message(returned: LaunchReturn) -> str:
    projection = json.dumps(PLANTED_PROJECTION)
    if returned is LaunchReturn.RUN_TOKEN:
        return (
            f"run token {PLANTED_RUN_TOKEN}\nrun file {PLANTED_RUN_FILE}\n{projection}"
        )
    if returned is LaunchReturn.FREE_FORM:
        return (
            f"The audit is sealed under token {PLANTED_RUN_TOKEN}. Its record is "
            f"{PLANTED_RUN_FILE}.\nThe rendered verdict follows.\n{projection}"
        )
    if returned is LaunchReturn.PROJECTION_QUOTING_BLOCKED:
        return f"Here is the verdict.\n{json.dumps(PLANTED_PROJECTION_QUOTING_BLOCKED)}"
    if returned is LaunchReturn.PROJECTION_ONLY:
        return f"Here is the verdict.\n```json\n{projection}\n```"
    if returned is LaunchReturn.UNSTRUCTURED:
        return f"The audit finished with token {PLANTED_RUN_TOKEN} and file {PLANTED_RUN_FILE}."
    return f"{BLOCKED_MARKER}: the auditor could not start the run"


def _machine_stream(argv: Sequence[str], message: str) -> str:
    """The parent session's machine stream carrying `message` as its last assistant text."""
    if argv[0] == CLAUDE_EXECUTABLE:
        event: dict[str, object] = {"type": "result", "result": message}
    else:
        event = {
            "type": "item.completed",
            "item": {"type": "agent_message", "text": message},
        }
    return json.dumps(event) + "\n"


@dataclass(frozen=True)
class GitRead:
    """One git read of the fixture directory: its exit code and stripped output."""

    exit_code: int
    output: str


@dataclass(frozen=True)
class FixtureRepository:
    """The reads a dispatched auditor makes of its fixture's checkout, taken when the launch ran."""

    toplevel: GitRead
    """`rev-parse --show-toplevel` in the fixture directory."""
    base: GitRead
    """`rev-parse --verify origin/HEAD^{commit}`, the auditor's default base."""
    head: GitRead
    """`rev-parse --verify HEAD^{commit}`."""
    status: GitRead
    """`status --porcelain --untracked-files=all`."""
    changed: GitRead
    """`diff --name-status --no-renames origin/HEAD...HEAD`."""


FIXTURE_GIT_READS: Final[Mapping[str, tuple[str, ...]]] = {
    "toplevel": ("rev-parse", "--show-toplevel"),
    "base": ("rev-parse", "--verify", "--end-of-options", "origin/HEAD^{commit}"),
    "head": ("rev-parse", "--verify", "--end-of-options", "HEAD^{commit}"),
    "status": ("status", "--porcelain", "--untracked-files=all"),
    "changed": ("diff", "--name-status", "--no-renames", "origin/HEAD...HEAD"),
}


@dataclass(frozen=True)
class DispatchCall:
    """One recorded command and the materialized state present when it ran."""

    argv: tuple[str, ...]
    home: Path
    environment: Mapping[str, str]
    state_files: Mapping[Path, bytes] = field(repr=False)
    """Bytes of every file under an `agents` or `fixture` directory of the row's state, keyed relative to it."""
    saved_login: bytes | None = field(default=None, repr=False)
    """Bytes the command's Codex home resolves its saved login to, when it holds one."""
    input_text: str | None = field(default=None, repr=False)
    """The stdin the command received."""
    fixture_repository: FixtureRepository | None = None
    """The fixture checkout as git reads it, for a command that names the fixture directory."""
    codex_config: bytes | None = field(default=None, repr=False)
    """Bytes of the `config.toml` the command's Codex home held, when it holds one."""
    directories: frozenset[Path] = frozenset()
    """Every directory of the row's state outside a git store, keyed relative to it."""


def _saved_login(home: Path) -> bytes | None:
    login = home / AUTH_FILENAME
    return login.read_bytes() if login.is_file() else None


def _codex_config(home: Path) -> bytes | None:
    config = home / CODEX_HOME_CONFIG_PATH
    return config.read_bytes() if config.is_file() else None


def _state_directories(state_root: Path) -> frozenset[Path]:
    return frozenset(
        path.relative_to(state_root)
        for path in state_root.rglob("*")
        if path.is_dir() and GIT_DIRECTORY not in path.parts
    )


def _materialized_state(state_root: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(state_root): path.read_bytes()
        for path in state_root.rglob("*")
        if path.is_file()
        and {AGENTS_DIRECTORY, FIXTURE_DIRECTORY} & set(path.parts)
        and GIT_DIRECTORY not in path.parts
    }


def _git_read(directory: Path, arguments: Sequence[str]) -> GitRead:
    result = subprocess.run(
        (GIT_EXECUTABLE, "-C", str(directory), *arguments),
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_READ_TIMEOUT_SECONDS,
    )
    return GitRead(result.returncode, result.stdout.strip())


def _fixture_repository(
    state_root: Path, argv: Sequence[str], input_text: str | None
) -> FixtureRepository | None:
    """Read the fixture checkout when the command names the fixture directory."""
    fixture = state_root / FIXTURE_DIRECTORY
    if not fixture.is_dir():
        return None
    named = " ".join((*argv, input_text or ""))
    if f"/{state_root.name}/{FIXTURE_DIRECTORY}/" not in named:
        return None
    reads = {
        name: _git_read(fixture, arguments)
        for name, arguments in FIXTURE_GIT_READS.items()
    }
    return FixtureRepository(**reads)


def _record_dispatch_call(
    argv: Sequence[str], env: Mapping[str, str], input_text: str | None
) -> DispatchCall:
    home = Path(env[CODEX_HOME_ENV])
    return DispatchCall(
        tuple(argv),
        home,
        dict(env),
        _materialized_state(home.parent),
        _saved_login(home),
        input_text,
        _fixture_repository(home.parent, argv, input_text),
        _codex_config(home),
        _state_directories(home.parent),
    )


StatePlant = Callable[[Path], None]
"""Writes planted state into a row before one of its commands runs; it receives the command's Codex home."""


def codex_config_plant(text: str) -> StatePlant:
    """Plant `text` as the `config.toml` of the command's Codex home."""

    def plant(home: Path) -> None:
        (home / CODEX_HOME_CONFIG_PATH).write_text(text, encoding="utf-8")

    return plant


def _row_for_state(state_root: Path) -> NativeAuditorRow:
    """The auditor row whose disposable state is `state_root`."""
    return next(
        row
        for row in native_auditor_rows(repository_root(), Path(), state_root.parent)
        if row.state_root.name == state_root.name
    )


def claude_definition_plant(grant: UnboundedGrant) -> StatePlant:
    """Plant a Claude Code row's materialized definition with its `tools` field in the unbounded form `grant` names."""

    def plant(home: Path) -> None:
        row = _row_for_state(home.parent)
        if row.target is Target.CLAUDE and row.native_definition_path.is_file():
            row.native_definition_path.write_text(  # NOSONAR S2083 - the row's own disposable state root
                definition_with_unbounded_grant(
                    row.shipped_definition_path.read_text(encoding="utf-8"), grant
                ),
                encoding="utf-8",
            )

    return plant


def claude_tool_grants_plant(grants: tuple[str, ...]) -> StatePlant:
    """Plant a Claude Code row's materialized definition with its `tools` field naming exactly `grants`."""

    def plant(home: Path) -> None:
        row = _row_for_state(home.parent)
        if row.target is Target.CLAUDE and row.native_definition_path.is_file():
            row.native_definition_path.write_text(  # NOSONAR S2083 - the row's own disposable state root
                definition_with_tool_grants(
                    row.shipped_definition_path.read_text(encoding="utf-8"), grants
                ),
                encoding="utf-8",
            )

    return plant


def auditor_launch_runner(
    credentials: NativeCredentialRunner,
    launch_exit_code: int,
    launches: frozenset[tuple[str, ...]],
    returned: LaunchReturn = LaunchReturn.RUN_TOKEN,
    plant: StatePlant | None = None,
) -> RecordingRunner[DispatchCall]:
    """A recording runner that completes every command and fails the dispatch launch on request.

    Before every command other than the dispatch launch, `plant` writes its
    state into the row, so the state stands when the producer reads it ahead
    of the launch; the call is recorded after the plant.
    """

    def is_launch(argv: Sequence[str]) -> bool:
        return any(set(launch) <= set(argv) for launch in launches)

    def record(
        argv: Sequence[str], env: Mapping[str, str], input_text: str | None
    ) -> DispatchCall:
        if plant is not None and not is_launch(argv):
            plant(Path(env[CODEX_HOME_ENV]))
        return _record_dispatch_call(argv, env, input_text)

    def complete(argv: Sequence[str]) -> tuple[int, str]:
        if is_launch(argv):
            return launch_exit_code, _machine_stream(argv, _returned_message(returned))
        return 0, ""

    return RecordingRunner(credentials, record, complete)


SELECTED_CLAUDE_CREDENTIAL: Final = min(CLAUDE_CREDENTIAL_VARIABLES)
"""The one Claude Code credential a launch plants unless the case names others: the choice is incidental to every assertion that takes it."""


@dataclass(frozen=True)
class DispatchLaunchObservation:
    rows: tuple[RowLaunch[NativeAuditorDispatchObservation, DispatchCall], ...]
    environment: Mapping[str, str]
    """The ambient environment the run received, every strippable name planted."""
    saved_login: bytes
    """Bytes of the selected Codex authentication's saved login."""


@dataclass(frozen=True)
class DispatchFailureObservation:
    rows: tuple[NativeAuditorDispatchObservation, ...]
    calls: tuple[NativeCall, ...]
    environment: Mapping[str, str]


@contextmanager
def native_auditor_launch(
    claude_credentials: Collection[str] | None = None,
    launch_exit_code: int = 0,
    returned: LaunchReturn = LaunchReturn.RUN_TOKEN,
    *,
    target: Target | None = None,
    plant: StatePlant | None = None,
) -> Iterator[DispatchLaunchObservation]:
    """Run every row of `target`, or every row, with `claude_credentials` planted beside every other strippable name.

    A case that names no credentials plants the one `SELECTED_CLAUDE_CREDENTIAL`.

    `plant` writes its state into each row before every command other than
    the dispatch launch.
    """
    planted = (
        {SELECTED_CLAUDE_CREDENTIAL}
        if claude_credentials is None
        else set(claude_credentials)
    )
    with launch_case() as case:
        runner = auditor_launch_runner(
            case.credentials.runner,
            launch_exit_code,
            frozenset(
                row.launch_command for row in native_auditor_rows(repository_root())
            ),
            returned,
            plant,
        )
        environment = ambient_environment(
            case.credentials.original_environment, claude_credentials=planted
        )
        rows = run_native_auditor_dispatch(
            case.artifact_root,
            checkout=repository_root(),
            environment=environment,
            runner=runner,
            target=target,
        )
        yield DispatchLaunchObservation(
            row_launches(rows, runner.calls),
            environment,
            case.credentials.initial.encode("utf-8"),
        )


def parent_launches(
    item: RowLaunch[NativeAuditorDispatchObservation, DispatchCall],
) -> list[DispatchCall]:
    """The recorded commands of `item`'s row that carry the row's parent launch command."""
    return [
        call
        for call in item.calls
        if set(item.observation.row.launch_command) <= set(call.argv)
    ]


def retained_result(row: NativeAuditorRow) -> dict[str, object]:
    """The parsed result artifact the row retained."""
    return cast(dict[str, object], json.loads(row.result_path.read_text("utf-8")))


@dataclass
class ParentRecorder:
    """A parent runner that records each launch it receives and completes it with no output."""

    launches: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(
        self,
        argv: Sequence[str],
        cwd: Path,
        environment: Mapping[str, str],
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, environment, input_text
        self.launches.append(tuple(argv))
        return subprocess.CompletedProcess(argv, 0, "", "")


def _unreached_runner(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    input_text: str | None,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    """The installation runner of a drive that runs no installation: any call is a harness error."""
    del cwd, env, input_text, timeout
    raise RuntimeError(f"unexpected native command {list(argv)}")


@dataclass(frozen=True)
class UnsetCodexHomeObservation:
    rows: tuple[NativeAuditorDispatchObservation, ...]
    launches: tuple[tuple[str, ...], ...]
    """Every parent launch the rows issued."""
    environment: Mapping[str, str]
    """The environment each row's dispatch received."""


@contextmanager
def native_auditor_without_codex_home() -> Iterator[UnsetCodexHomeObservation]:
    """Dispatch every Codex row from an environment that selects no `CODEX_HOME`.

    The installation the full harness performs always selects the row's
    disposable `CODEX_HOME`, so this drive skips it: the shared row driver
    materializes each row and records its failure, and the row's dispatch
    receives an ambient environment, every strippable name planted, that
    names no Codex home.
    """
    with TemporaryDirectory() as temporary_directory:
        artifact_root = Path(temporary_directory) / "artifacts"
        environment = {
            name: value
            for name, value in ambient_environment(
                {}, claude_credentials=CLAUDE_CREDENTIAL_VARIABLES
            ).items()
            if name != CODEX_HOME_ENV
        }
        parent = ParentRecorder()

        def plan(state_root: Path) -> tuple[NativeAuditorRow, ...]:
            return native_auditor_rows(repository_root(), artifact_root, state_root)

        def execute(
            row: NativeAuditorRow, mirror: Path, interval: NativeProfileInterval
        ) -> NativeAuditorDispatchObservation:
            return run_native_auditor_row(
                row,
                checkout=mirror,
                environment=environment,
                parent=parent,
                sanitize=interval.sanitize,
            )

        rows = run_native_rows(
            artifact_root,
            checkout=repository_root(),
            plan=plan,
            materialize=materialize_native_auditor,
            execute=execute,
            record_failure=record_native_auditor_failure,
            runner=_unreached_runner,
            target=Target.CODEX,
        )
        yield UnsetCodexHomeObservation(rows, tuple(parent.launches), environment)


@contextmanager
def native_auditor_failure(fault: NativeFault) -> Iterator[DispatchFailureObservation]:
    """Expose retained evidence after the production harness removes its state."""
    with launch_case() as case:
        runner = NativeFailureRunner(fault)
        environment = ambient_environment(
            case.credentials.original_environment,
            claude_credentials=CLAUDE_CREDENTIAL_VARIABLES,
        )
        rows = run_native_auditor_dispatch(
            case.artifact_root,
            checkout=repository_root(),
            environment=environment,
            runner=runner,
        )
        yield DispatchFailureObservation(rows, tuple(runner.calls), environment)
