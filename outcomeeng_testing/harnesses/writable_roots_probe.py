"""Attested-run runner for the writable-roots probe of native agent recovery.

The runner executes the Codex form of the protocol in
``probes/writable-roots/probe.md``. It provisions a disposable Codex home whose
configuration holds a workspace-write sandbox and no background server, starts
one fresh seed thread in a reserved Prowl pane, then recovers that thread twice
through ``recover_agents.py``: first with no writable root, and after a full
exit with one fresh root. It captures the ``/status`` screen of each recovery.

The runner exposes observations and the first stop condition. It judges no
verdict: the Author reads the captures and records the verdict in the probe.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shlex
import stat
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

from outcomeeng.distribution.installation import (
    CODEX_EXECUTABLE,
    CODEX_HOME_ENV,
    HOME_ENV,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    AUTH_FILENAME,
    DiscoveryAuthentication,
    DiscoveryAuthenticationError,
    ProbeRunner,
    credential_free_environment,
    run_probe_process,
    select_authentication,
)
from outcomeeng_testing.harnesses.prowl_environment import load_prowl_environment

ROOT = Path(__file__).parents[2]
RECOVERY_SCRIPT_PATH = (
    ROOT
    / "src/plugins/coding-agents/skills/recover-prowl-agents/scripts/recover_agents.py"
)
CONFIG_FILENAME = "config.toml"
SANDBOX_MODE_KEY = "sandbox_mode"
SANDBOX_MODE_WORKSPACE_WRITE = "workspace-write"
DAEMON_AUTO_START_KEY = "daemon_auto_start"
CREDENTIAL_STORE_KEY = "cli_auth_credentials_store"
CREDENTIAL_STORE_FILE = "file"
PROJECT_TRUST_LEVEL = "trusted"
NO_DAEMON_FLAG = "--no-daemon"
VERSION_FLAG = "--version"
STATUS_COMMAND = "/status"
EXIT_COMMAND = "/exit"
SEED_PROMPT = "Reply with the single word ready. Take no other action."
SEED_REPLY_MARKER = "• ready"
SEED_FINISHED_MARKER = "Worked for"
INPUT_PROMPT_MARKER = "›"
INPUT_PLACEHOLDER = "Ask Codex to do anything"
ENTER_KEY = "Enter"
SERVER_ATTACHMENT_MARKERS = ("background", "remote")
SCREEN_LAST_LINES = 200
SCREEN_WAIT_TIMEOUT_SECONDS = 10
STATUS_FIELDS = ("Session", "Directory", "Permissions", "Server")
STATUS_LINE_PATTERN = re.compile(
    r"^\s*(?P<label>" + "|".join(STATUS_FIELDS) + r"):\s+(?P<value>\S.*?)\s*$",
    re.MULTILINE,
)
SESSION_ID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)
HOME_PREFIX = "~/"
SYSTEM_TEMPORARY_ROOTS = ("/tmp", "/private/tmp", "/var/tmp", "/private/var/tmp")
SOCKET_SEARCH_DEPTH = 4
PROWL_SUCCEEDED_STATUS = "succeeded"


class ProbeStopCondition(StrEnum):
    """The conditions on which the protocol stops without a decided observation."""

    INVALID = "invalid"
    UNDECIDED = "undecided"


class RecoveryLabel(StrEnum):
    """The three captured moments of one run, in protocol order."""

    SEED = "seed"
    CONTROL = "control"
    TREATMENT = "treatment"


ARTIFACT_NAMES: dict[RecoveryLabel, str] = {
    RecoveryLabel.SEED: "codex-status-seed.txt",
    RecoveryLabel.CONTROL: "codex-status-control-no-root.txt",
    RecoveryLabel.TREATMENT: "codex-status-treatment-with-root.txt",
}


class ProbeStopped(RuntimeError):
    """The first invalid or undecided condition, with the evidence it left."""

    def __init__(
        self,
        condition: ProbeStopCondition,
        step: str,
        reason: str,
        evidence: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(f"{condition.value} at {step}: {reason}")
        self.condition = condition
        self.step = step
        self.reason = reason
        self.evidence = dict(evidence or {})


class PaneTerminal(Protocol):
    """Prowl pane operations the protocol needs, each returning its checked result."""

    def list_panes(self) -> dict[str, object]: ...

    def list_agents(self) -> dict[str, object]: ...

    def read(self, pane_id: str) -> dict[str, object]: ...

    def send(self, pane_id: str, text: str) -> dict[str, object]: ...

    def press(self, pane_id: str, key: str) -> dict[str, object]: ...

    def create_tab(self, worktree_id: str) -> dict[str, object]: ...


class ProwlTerminal:
    """Production binding of the pane operations to the shipped Prowl adapter."""

    def __init__(self, prowl: ModuleType, runner: object) -> None:
        self._prowl = prowl
        self._runner = runner

    def _run(self, operation: str, **arguments: object) -> dict[str, object]:
        request = self._prowl.operation_request(operation, **arguments)
        result = self._prowl.execute(request, self._runner)
        return cast(dict[str, object], json.loads(json.dumps(result)))

    def list_panes(self) -> dict[str, object]:
        return self._run("list")

    def list_agents(self) -> dict[str, object]:
        return self._run("agents")

    def read(self, pane_id: str) -> dict[str, object]:
        return self._run(
            "read",
            pane=pane_id,
            last=SCREEN_LAST_LINES,
            wait_stable=True,
            wait_timeout=SCREEN_WAIT_TIMEOUT_SECONDS,
        )

    def send(self, pane_id: str, text: str) -> dict[str, object]:
        return self._run("send", pane=pane_id, text=text, no_wait=True)

    def press(self, pane_id: str, key: str) -> dict[str, object]:
        return self._run("key", pane=pane_id, key=key, mutation_authorized=True)

    def create_tab(self, worktree_id: str) -> dict[str, object]:
        return self._run("tab-create", worktree=worktree_id, mutation_authorized=True)


@dataclass(frozen=True)
class Pacing:
    """Bounded waits for a screen or an agent roster to reach an expected state."""

    attempts: int = 20
    pause_seconds: float = 3.0
    pause: Callable[[float], None] = time.sleep


@dataclass(frozen=True)
class ControllerIdentity:
    """The running session that serves as the protocol's current-session controller."""

    pane_id: str
    worktree_path: Path
    session_id: str
    agent_type: str


@dataclass(frozen=True)
class CodexProbeRequest:
    """Every caller-supplied input of one Codex run."""

    environment: Mapping[str, str]
    candidate_worktree: Path
    controller: ControllerIdentity
    probe_home: Path
    writable_root: Path
    artifact_directory: Path


@dataclass(frozen=True)
class StatusScreen:
    """The fields one Codex status card reports; the last card on a screen wins."""

    session_id: str | None
    directory: str | None
    permissions: str | None
    server: str | None


@dataclass
class ProbeRecord:
    """The observations of one run, filled in protocol order."""

    shared_config_digest_before: str | None = None
    shared_config_digest_after: str | None = None
    codex_version: str | None = None
    recovery_source_digest: str | None = None
    candidate_pane_id: str | None = None
    session_id: str | None = None
    captures: dict[str, dict[str, object]] = field(default_factory=dict)
    recoveries: dict[str, dict[str, object]] = field(default_factory=dict)
    exits: list[dict[str, object]] = field(default_factory=list)
    stop: dict[str, object] | None = None

    def as_json(self) -> dict[str, object]:
        return {
            "sharedConfigDigestBefore": self.shared_config_digest_before,
            "sharedConfigDigestAfter": self.shared_config_digest_after,
            "codexVersion": self.codex_version,
            "recoverySourceDigest": self.recovery_source_digest,
            "candidatePaneId": self.candidate_pane_id,
            "sessionId": self.session_id,
            "captures": self.captures,
            "recoveries": self.recoveries,
            "exits": self.exits,
            "stop": self.stop,
        }


def load_recovery_module() -> ModuleType:
    """Load the shipped recovery script so the run calls its source-owned planner."""
    spec = importlib.util.spec_from_file_location(
        "coding_agents_writable_roots_probe_recovery", RECOVERY_SCRIPT_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load recovery module: {RECOVERY_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def file_digest(path: Path) -> str:
    """The SHA-256 of one file's bytes, in hexadecimal."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe_home_configuration(candidate_worktree: Path) -> str:
    """The disposable home's configuration: workspace-write, no daemon, one trusted project."""
    return (
        "\n".join(
            (
                f"{CREDENTIAL_STORE_KEY} = {json.dumps(CREDENTIAL_STORE_FILE)}",
                f"{SANDBOX_MODE_KEY} = {json.dumps(SANDBOX_MODE_WORKSPACE_WRITE)}",
                "",
                "[features]",
                f"{DAEMON_AUTO_START_KEY} = false",
                "",
                f"[projects.{json.dumps(str(candidate_worktree))}]",
                f"trust_level = {json.dumps(PROJECT_TRUST_LEVEL)}",
            )
        )
        + "\n"
    )


def seed_launch_command(probe_home: Path) -> str:
    """The command that starts the seed thread, in the disposable home with no server."""
    return shlex.join(
        ("env", f"{CODEX_HOME_ENV}={probe_home}", CODEX_EXECUTABLE, NO_DAEMON_FLAG)
    )


def parse_status(screen: str) -> StatusScreen:
    """Read the status fields from the last card on a screen."""
    last: dict[str, str] = {}
    for match in STATUS_LINE_PATTERN.finditer(screen):
        last[match.group("label")] = match.group("value")
    session = last.get("Session")
    return StatusScreen(
        session_id=(
            session
            if session is not None and SESSION_ID_PATTERN.fullmatch(session)
            else None
        ),
        directory=last.get("Directory"),
        permissions=last.get("Permissions"),
        server=last.get("Server"),
    )


def _squeeze(text: str) -> str:
    return "".join(text.split())


def root_listed(screen: str, root: Path) -> bool:
    """Whether the screen names the root, even where the terminal wrapped its line."""
    return _squeeze(str(root)) in _squeeze(screen)


def workspace_policy(permissions: str | None) -> bool:
    """Whether the permissions line reports a workspace sandbox."""
    return permissions is not None and "workspace" in permissions.lower()


def server_attached(server: str | None) -> bool:
    """Whether the status card reports a background or remote server."""
    return server is not None and any(
        marker in server.lower() for marker in SERVER_ATTACHMENT_MARKERS
    )


def expand_home(directory: str, home: Path) -> Path:
    """Expand the leading home marker the status card abbreviates a directory with."""
    if directory.startswith(HOME_PREFIX):
        return home / directory[len(HOME_PREFIX) :]
    return Path(directory)


def condense_screen(screen: str) -> str:
    """Trim trailing spaces and collapse runs of blank padding rows to one blank row."""
    condensed: list[str] = []
    for line in (row.rstrip() for row in screen.splitlines()):
        if not line and (not condensed or not condensed[-1]):
            continue
        condensed.append(line)
    while condensed and not condensed[-1]:
        condensed.pop()
    return "\n".join(condensed) + "\n"


def input_ready(screen: str) -> bool:
    """Whether the screen shows the empty Codex input prompt among its last rows.

    A dialog marks its selected option with the same prompt character, so the
    input placeholder must show as well.
    """
    tail = [row for row in screen.splitlines() if row.strip()][-6:]
    return any(
        row.lstrip().startswith(INPUT_PROMPT_MARKER) and INPUT_PLACEHOLDER in row
        for row in tail
    )


def command_pending(screen: str, command: str) -> bool:
    """Whether a slash command still sits in the input line, unsubmitted."""
    return any(
        row.lstrip().startswith(f"{INPUT_PROMPT_MARKER} {command}")
        for row in screen.splitlines()
    )


def socket_paths(home: Path) -> list[Path]:
    """Every socket under the home, to a bounded depth, without following links."""
    found: list[Path] = []
    pending = [(home, 0)]
    while pending:
        directory, depth = pending.pop()
        try:
            entries = list(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            mode = entry.lstat().st_mode
            if stat.S_ISSOCK(mode):
                found.append(entry)
            elif stat.S_ISDIR(mode) and depth < SOCKET_SEARCH_DEPTH:
                pending.append((entry, depth + 1))
    return sorted(found)


def _is_within(path: Path, ancestor: Path) -> bool:
    return path == ancestor or ancestor in path.parents


def _stop(
    condition: ProbeStopCondition,
    step: str,
    reason: str,
    evidence: Mapping[str, object] | None = None,
) -> ProbeStopped:
    return ProbeStopped(condition, step, reason, evidence)


def _pane_id(item: Mapping[str, object]) -> str:
    return str(cast(Mapping[str, object], item["pane"])["id"])


def _worktree_field(item: Mapping[str, object], name: str) -> str:
    return str(cast(Mapping[str, object], item["worktree"])[name])


def _data(result: Mapping[str, object]) -> Mapping[str, object]:
    response = cast(Mapping[str, object], result.get("response") or {})
    return cast(Mapping[str, object], response.get("data") or {})


class CodexWritableRootProbe:
    """One run of the protocol; its collaborators are injected at the boundary."""

    def __init__(
        self,
        request: CodexProbeRequest,
        *,
        terminal: PaneTerminal,
        recovery: ModuleType,
        authentication: DiscoveryAuthentication,
        runner: ProbeRunner = run_probe_process,
        pacing: Pacing | None = None,
    ) -> None:
        self.request = request
        self.terminal = terminal
        self.recovery = recovery
        self.authentication = authentication
        self.runner = runner
        self.pacing = pacing if pacing is not None else Pacing()
        self.record = ProbeRecord()
        self.candidate_key: str | None = None
        self.controller_key: str | None = None

    @property
    def shared_config(self) -> Path:
        return (
            Path(self.request.environment[CODEX_HOME_ENV]).resolve() / CONFIG_FILENAME
        )

    def run(self) -> ProbeRecord:
        """Run the protocol once; the record carries the first stop, if any."""
        record = self.record
        try:
            try:
                record.shared_config_digest_before = self._shared_digest()
                self._admit()
                self._provision_home()
                with self.authentication.authenticated_home(
                    self.request.probe_home,
                    cwd=self.request.candidate_worktree,
                    env=self.request.environment,
                ):
                    self._protocol()
            except DiscoveryAuthenticationError as error:
                raise _stop(
                    ProbeStopCondition.UNDECIDED,
                    "authentication",
                    str(error),
                ) from None
        except ProbeStopped as stopped:
            record.stop = {
                "condition": stopped.condition.value,
                "step": stopped.step,
                "reason": stopped.reason,
                "evidence": stopped.evidence,
            }
        finally:
            self._release_credential_link()
            try:
                record.shared_config_digest_after = self._shared_digest()
            except ProbeStopped:
                record.shared_config_digest_after = None
        if (
            record.stop is None
            and record.shared_config_digest_after != record.shared_config_digest_before
        ):
            record.stop = {
                "condition": ProbeStopCondition.INVALID.value,
                "step": "shared-home-digest",
                "reason": "The shared home's configuration changed during the run.",
                "evidence": {},
            }
        return record

    def _shared_digest(self) -> str:
        try:
            return file_digest(self.shared_config)
        except OSError as error:
            raise _stop(
                ProbeStopCondition.INVALID,
                "shared-home-digest",
                f"The shared home's configuration is unreadable: {error.strerror}.",
            ) from None

    def _release_credential_link(self) -> None:
        link = self.request.probe_home / AUTH_FILENAME
        if link.is_symlink():
            link.unlink()

    def _admit(self) -> None:
        request = self.request
        for name, path in (
            ("probe home", request.probe_home),
            ("writable root", request.writable_root),
        ):
            if path.exists() or path.is_symlink():
                raise _stop(
                    ProbeStopCondition.INVALID,
                    "admission",
                    f"The {name} {path} exists before the run.",
                )
            if not path.is_absolute():
                raise _stop(
                    ProbeStopCondition.INVALID,
                    "admission",
                    f"The {name} {path} is not absolute.",
                )
        root = request.writable_root.parent.resolve() / request.writable_root.name
        excluded = (
            request.candidate_worktree.resolve(),
            request.probe_home.parent.resolve() / request.probe_home.name,
            Path(tempfile.gettempdir()).resolve(),
            *(Path(item).resolve() for item in SYSTEM_TEMPORARY_ROOTS),
        )
        if any(_is_within(root, ancestor) for ancestor in excluded):
            raise _stop(
                ProbeStopCondition.INVALID,
                "admission",
                "The writable root lies inside the candidate worktree, the probe home, or a temporary directory.",
                {"root": str(root)},
            )
        if not request.candidate_worktree.is_dir():
            raise _stop(
                ProbeStopCondition.INVALID,
                "admission",
                f"The candidate worktree {request.candidate_worktree} is absent.",
            )
        if not request.artifact_directory.is_dir():
            raise _stop(
                ProbeStopCondition.INVALID,
                "admission",
                f"The artifact directory {request.artifact_directory} is absent.",
            )
        self.record.recovery_source_digest = file_digest(RECOVERY_SCRIPT_PATH)
        version = self.runner(
            (CODEX_EXECUTABLE, VERSION_FLAG),
            cwd=request.candidate_worktree,
            env=credential_free_environment(request.environment),
            input_text=None,
            timeout=self.pacing.pause_seconds * self.pacing.attempts,
        )
        if version.returncode != 0:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                "admission",
                "The Codex version command failed.",
                {"stderr": version.stderr},
            )
        self.record.codex_version = version.stdout.strip()

    def _provision_home(self) -> None:
        request = self.request
        request.probe_home.mkdir(parents=True)
        request.probe_home.chmod(0o700)
        (request.probe_home / CONFIG_FILENAME).write_text(
            probe_home_configuration(request.candidate_worktree), encoding="utf-8"
        )
        request.writable_root.mkdir(parents=True)

    def _checked(self, step: str, result: dict[str, object]) -> dict[str, object]:
        if result.get("status") != PROWL_SUCCEEDED_STATUS:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                step,
                "A Prowl operation did not succeed.",
                {"result": result},
            )
        return result

    def _screen(self, step: str, pane_id: str) -> str:
        result = self._checked(step, self.terminal.read(pane_id))
        return str(_data(result).get("text", ""))

    def _send(self, step: str, pane_id: str, text: str) -> dict[str, object]:
        result = self._checked(step, self.terminal.send(pane_id, text))
        input_record = cast(Mapping[str, object], _data(result).get("input") or {})
        if input_record.get(self.recovery.TRAILING_ENTER_SENT_FIELD) is not True:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                step,
                "The send carries no trailing Enter evidence.",
                {"result": result},
            )
        return result

    def _wait_for_screen(
        self, step: str, pane_id: str, ready: Callable[[str], bool]
    ) -> str:
        screen = ""
        for _ in range(self.pacing.attempts):
            screen = self._screen(step, pane_id)
            if ready(screen):
                return screen
            self.pacing.pause(self.pacing.pause_seconds)
        raise _stop(
            ProbeStopCondition.UNDECIDED,
            step,
            "The screen never reached the expected state.",
            {"screen": self.authentication.redactor.clean(screen)},
        )

    def _inventory(
        self, step: str
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        panes = self._checked(step, self.terminal.list_panes())
        agents = self._checked(step, self.terminal.list_agents())
        return (
            cast(list[dict[str, object]], _data(panes).get("items", [])),
            cast(list[dict[str, object]], _data(agents).get("agents", [])),
        )

    def _scoped(
        self, step: str, pane_ids: Sequence[str]
    ) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        items, agents = self._inventory(step)
        scoped_items = [item for item in items if _pane_id(item) in pane_ids]
        scoped_agents = [agent for agent in agents if agent["id"] in pane_ids]
        return scoped_items, scoped_agents

    def _protocol(self) -> None:
        request = self.request
        pane_id = self._reserve_candidate()
        self.record.candidate_pane_id = pane_id
        self._send("seed-launch", pane_id, seed_launch_command(request.probe_home))
        self._wait_for_screen("seed-launch", pane_id, input_ready)
        self._send("seed-prompt", pane_id, SEED_PROMPT)
        self._wait_for_screen(
            "seed-prompt",
            pane_id,
            lambda screen: (
                SEED_REPLY_MARKER in screen and SEED_FINISHED_MARKER in screen
            ),
        )
        seed = self._capture(RecoveryLabel.SEED, pane_id)
        if seed.session_id is None:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                "seed-status",
                "The seed status card names no session.",
            )
        self.record.session_id = seed.session_id
        prepared = self._prepare(pane_id, seed.session_id)
        self._exit(pane_id)
        self._recover(RecoveryLabel.CONTROL, pane_id, prepared, None)
        self._exit(pane_id)
        self._recover(
            RecoveryLabel.TREATMENT,
            pane_id,
            prepared,
            {cast(str, self.candidate_key): [str(request.writable_root)]},
        )
        self._exit(pane_id)

    def _reserve_candidate(self) -> str:
        step = "reserve-candidate"
        items, _ = self._inventory(step)
        known = {_pane_id(item) for item in items}
        worktrees = {
            (_worktree_field(item, "id"), _worktree_field(item, "path"))
            for item in items
            if Path(_worktree_field(item, "path")) == self.request.candidate_worktree
        }
        if len(worktrees) != 1:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                step,
                "The Prowl inventory holds no single worktree for the candidate path.",
                {"worktrees": sorted(worktrees)},
            )
        worktree_id, self.candidate_key = next(iter(worktrees))
        self._checked(step, self.terminal.create_tab(worktree_id))
        items, _ = self._inventory(step)
        created = [item for item in items if _pane_id(item) not in known]
        if len(created) != 1:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                step,
                "Tab creation did not yield exactly one new pane.",
                {"newPanes": [_pane_id(item) for item in created]},
            )
        if _worktree_field(created[0], "path") != self.candidate_key:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                step,
                "The new pane lies in another worktree.",
                {
                    "pane": _pane_id(created[0]),
                    "worktree": _worktree_field(created[0], "path"),
                },
            )
        pane_id = _pane_id(created[0])
        self._wait_for_screen(step, pane_id, lambda screen: bool(screen.strip()))
        return pane_id

    def _capture(self, label: RecoveryLabel, pane_id: str) -> StatusScreen:
        step = f"{label.value}-status"
        self._send(step, pane_id, STATUS_COMMAND)
        screen = ""
        for _ in range(self.pacing.attempts):
            screen = self._screen(step, pane_id)
            if parse_status(screen).session_id is not None:
                break
            if command_pending(screen, STATUS_COMMAND):
                self._checked(step, self.terminal.press(pane_id, ENTER_KEY))
            self.pacing.pause(self.pacing.pause_seconds)
        status = parse_status(screen)
        cleaned = self.authentication.redactor.clean(screen)
        artifact = self.request.artifact_directory / ARTIFACT_NAMES[label]
        artifact.write_text(
            self._header(label, pane_id) + condense_screen(cleaned),
            encoding="utf-8",
        )
        listed = root_listed(screen, self.request.writable_root)
        self.record.captures[label.value] = {
            "paneId": pane_id,
            "sessionId": status.session_id,
            "directory": status.directory,
            "permissions": status.permissions,
            "server": status.server,
            "rootListed": listed,
            "artifact": str(artifact),
        }
        if status.session_id is None:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                step,
                "No status card appeared.",
                {"screen": cleaned},
            )
        directory = expand_home(
            status.directory or "", Path(self.request.environment[HOME_ENV])
        )
        if directory != self.request.candidate_worktree:
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "The status card reports another directory.",
                {"directory": status.directory},
            )
        if not workspace_policy(status.permissions):
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "The status card reports no workspace policy.",
                {"permissions": status.permissions},
            )
        if server_attached(status.server):
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "The status card reports a server attachment.",
                {"server": status.server},
            )
        if label is not RecoveryLabel.TREATMENT and listed:
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "The root is listed before any recovery supplies it.",
                {"permissions": status.permissions},
            )
        return status

    def _header(self, label: RecoveryLabel, pane_id: str) -> str:
        recovery = self.record.recoveries.get(label.value, {})
        lines = [
            f"Capture: Codex /status, {label.value}, session {self.record.session_id}, pane {pane_id}, worktree {self.request.candidate_worktree}",
            f"Sandbox: {SANDBOX_MODE_KEY} = {json.dumps(SANDBOX_MODE_WORKSPACE_WRITE)} in the {CONFIG_FILENAME} of the disposable {CODEX_HOME_ENV} {self.request.probe_home}",
            f"Writable root: {self.request.writable_root}",
        ]
        if recovery:
            lines.append(f"Recovery: {recovery['command']}")
        lines.append(
            "Source: Prowl read of the pane screen, stable-screen mode; credentials scrubbed, trailing spaces trimmed, runs of blank padding rows collapsed to one, every other row verbatim."
        )
        return "\n".join(lines) + "\n\n"

    def _prepare(self, pane_id: str, session_id: str) -> dict[str, object]:
        step = "prepare"
        recovery = self.recovery
        controller = self.request.controller
        panes = (controller.pane_id, pane_id)
        items, agents = self._scoped(step, panes)
        reported = {_pane_id(item): _worktree_field(item, "path") for item in items}
        self.controller_key = reported.get(controller.pane_id)
        if (
            self.controller_key is None
            or Path(self.controller_key) != controller.worktree_path
        ):
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "The controller pane lies in another worktree than the supplied one.",
                {"reported": reported.get(controller.pane_id)},
            )
        candidates = [
            {
                recovery.PANE_ID_FIELD: controller.pane_id,
                recovery.WORKTREE_PATH_FIELD: self.controller_key,
                recovery.SESSION_ID_FIELD: controller.session_id,
                recovery.RESUME_LOCATOR_FIELD: controller.session_id,
                recovery.NATIVE_HOME_FIELD: None,
                recovery.AGENT_TYPE_FIELD: controller.agent_type,
                recovery.EVIDENCE_FIELD: recovery.EvidenceSource.CURRENT_SESSION,
                recovery.ROLE_FIELD: recovery.RecoveryRole.PRIMARY,
                recovery.SECONDARY_AUTHORIZED_FIELD: False,
            },
            {
                recovery.PANE_ID_FIELD: pane_id,
                recovery.WORKTREE_PATH_FIELD: self.candidate_key,
                recovery.SESSION_ID_FIELD: session_id,
                recovery.RESUME_LOCATOR_FIELD: session_id,
                recovery.NATIVE_HOME_FIELD: str(self.request.probe_home),
                recovery.AGENT_TYPE_FIELD: recovery.AgentType.CODEX,
                recovery.EVIDENCE_FIELD: recovery.EvidenceSource.NATIVE_STATUS,
                recovery.ROLE_FIELD: recovery.RecoveryRole.PRIMARY,
                recovery.SECONDARY_AUTHORIZED_FIELD: False,
            },
        ]
        try:
            prepared = cast(
                dict[str, object],
                json.loads(
                    json.dumps(
                        recovery.prepare(
                            panes,
                            items,
                            agents,
                            candidates,
                            [
                                self._evidence(candidate, candidate_source)
                                for candidate, candidate_source in zip(
                                    candidates,
                                    (
                                        recovery.EvidenceSource.CURRENT_SESSION,
                                        recovery.EvidenceSource.NATIVE_STATUS,
                                    ),
                                    strict=True,
                                )
                            ],
                        )
                    )
                ),
            )
        except recovery.AdapterError as error:
            raise _stop(
                ProbeStopCondition.INVALID, step, str(error), {"status": error.status}
            ) from None
        if prepared.get(recovery.STATUS_FIELD) != recovery.ResultStatus.PREPARED:
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "Preparation did not return a prepared manifest.",
                {"result": prepared},
            )
        return prepared

    def _evidence(
        self, candidate: Mapping[str, object], source: object
    ) -> dict[str, object]:
        recovery = self.recovery
        return {
            recovery.PANE_ID_FIELD: candidate[recovery.PANE_ID_FIELD],
            recovery.WORKTREE_PATH_FIELD: candidate[recovery.WORKTREE_PATH_FIELD],
            recovery.SESSION_ID_FIELD: candidate[recovery.SESSION_ID_FIELD],
            recovery.AGENT_TYPE_FIELD: candidate[recovery.AGENT_TYPE_FIELD],
            recovery.SOURCE_FIELD: source,
        }

    def _recover(
        self,
        label: RecoveryLabel,
        pane_id: str,
        prepared: dict[str, object],
        writable_roots: dict[str, list[str]] | None,
    ) -> None:
        recovery = self.recovery
        step = f"{label.value}-recovery"
        panes = (self.request.controller.pane_id, pane_id)
        self._require_socket_absent(step)
        items, agents = self._scoped(step, panes)
        try:
            activation = recovery.plan_activation(prepared, items, agents)
            if activation.get(recovery.STATUS_FIELD) != recovery.ResultStatus.READY:
                raise _stop(
                    ProbeStopCondition.INVALID,
                    step,
                    "Activation is not ready with existing panes.",
                    {"activation": json.loads(json.dumps(activation))},
                )
            bindings = activation[recovery.BINDINGS_FIELD]
            plan = recovery.recover(prepared, bindings, items, agents, writable_roots)
        except recovery.AdapterError as error:
            raise _stop(
                ProbeStopCondition.INVALID, step, str(error), {"status": error.status}
            ) from None
        deliveries = plan.get(recovery.DELIVERIES_FIELD, [])
        statuses = {
            target[recovery.PANE_ID_FIELD]: target[recovery.STATUS_FIELD]
            for target in plan.get(recovery.TARGETS_FIELD, [])
        }
        if (
            plan.get(recovery.STATUS_FIELD) != recovery.ResultStatus.RESUMED
            or len(deliveries) != 1
            or deliveries[0][recovery.PANE_ID_FIELD] != pane_id
            or statuses.get(self.request.controller.pane_id)
            != recovery.Resolution.ALREADY_CORRELATED
            or statuses.get(pane_id) != recovery.Resolution.RESUMED
        ):
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "Recovery did not plan exactly one launch for the candidate.",
                {"plan": json.loads(json.dumps(plan))},
            )
        command = str(deliveries[0][recovery.TEXT_FIELD])
        self.record.recoveries[label.value] = {
            "command": command,
            "writableRoots": writable_roots or {},
        }
        transport = self._send(step, pane_id, command)
        try:
            settled = recovery.settle_recovery(
                json.loads(json.dumps(plan)),
                [
                    {
                        recovery.PANE_ID_FIELD: pane_id,
                        recovery.TRANSPORT_FIELD: transport,
                    }
                ],
            )
        except recovery.AdapterError as error:
            raise _stop(
                ProbeStopCondition.UNDECIDED, step, str(error), {"status": error.status}
            ) from None
        if settled.get(recovery.STATUS_FIELD) != recovery.ResultStatus.RESUMED:
            raise _stop(
                ProbeStopCondition.UNDECIDED,
                step,
                "Settlement did not report the launch as resumed.",
                {"settled": json.loads(json.dumps(settled))},
            )
        self._wait_for_screen(step, pane_id, input_ready)
        status = self._capture(label, pane_id)
        self._verify(step, pane_id, prepared, bindings, status)
        self.record.recoveries[label.value]["verification"] = "verified"

    def _verify(
        self,
        step: str,
        pane_id: str,
        prepared: dict[str, object],
        bindings: object,
        status: StatusScreen,
    ) -> None:
        recovery = self.recovery
        panes = (self.request.controller.pane_id, pane_id)
        items, agents = self._scoped(step, panes)
        controller = self.request.controller
        evidence = [
            {
                recovery.PANE_ID_FIELD: controller.pane_id,
                recovery.WORKTREE_PATH_FIELD: self.controller_key,
                recovery.SESSION_ID_FIELD: controller.session_id,
                recovery.AGENT_TYPE_FIELD: controller.agent_type,
                recovery.SOURCE_FIELD: recovery.EvidenceSource.CURRENT_SESSION,
            },
            {
                recovery.PANE_ID_FIELD: pane_id,
                recovery.WORKTREE_PATH_FIELD: self.candidate_key,
                recovery.SESSION_ID_FIELD: status.session_id,
                recovery.AGENT_TYPE_FIELD: recovery.AgentType.CODEX,
                recovery.SOURCE_FIELD: recovery.EvidenceSource.NATIVE_STATUS,
            },
        ]
        try:
            verified = recovery.verify(prepared, bindings, items, agents, evidence)
        except recovery.AdapterError as error:
            raise _stop(
                ProbeStopCondition.INVALID, step, str(error), {"status": error.status}
            ) from None
        if (
            verified.get(recovery.STATUS_FIELD) != recovery.ResultStatus.VERIFIED
            or verified.get(recovery.MISSING_PANE_IDS_FIELD)
            or verified.get(recovery.DUPLICATE_PANE_IDS_FIELD)
            or verified.get(recovery.UNEXPECTED_AGENT_PANE_IDS_FIELD)
        ):
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "Verification did not find the exact prepared session in the candidate pane.",
                {"verification": json.loads(json.dumps(verified))},
            )

    def _require_socket_absent(self, step: str) -> None:
        sockets = socket_paths(self.request.probe_home)
        if sockets:
            raise _stop(
                ProbeStopCondition.INVALID,
                step,
                "The disposable home holds a server socket.",
                {"sockets": [str(path) for path in sockets]},
            )

    def _exit(self, pane_id: str) -> None:
        step = "exit"
        self._send(step, pane_id, EXIT_COMMAND)
        for _ in range(self.pacing.attempts):
            _, agents = self._scoped(step, (pane_id,))
            if not agents:
                self._require_socket_absent(step)
                self.record.exits.append({"paneId": pane_id, "agentRoster": "empty"})
                return
            if command_pending(self._screen(step, pane_id), EXIT_COMMAND):
                self._checked(step, self.terminal.press(pane_id, ENTER_KEY))
            self.pacing.pause(self.pacing.pause_seconds)
        raise _stop(
            ProbeStopCondition.UNDECIDED,
            step,
            "The candidate pane still reports an agent after the exit.",
            {"paneId": pane_id},
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-worktree", type=Path, required=True)
    parser.add_argument("--controller-pane", required=True)
    parser.add_argument("--controller-session", required=True)
    parser.add_argument("--controller-worktree", type=Path, required=True)
    parser.add_argument("--controller-agent-type", default="claude")
    parser.add_argument("--probe-home", type=Path, required=True)
    parser.add_argument("--writable-root", type=Path, required=True)
    parser.add_argument("--artifact-directory", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Codex protocol once through its public recipe and print the record."""
    arguments = _parser().parse_args(argv)
    environment = dict(os.environ)
    prowl = load_prowl_environment()
    try:
        selection = select_authentication(environment)
    except DiscoveryAuthenticationError as error:
        record = ProbeRecord(
            stop={
                "condition": ProbeStopCondition.UNDECIDED.value,
                "step": "authentication",
                "reason": str(error),
                "evidence": {},
            }
        )
        print(json.dumps(record.as_json(), indent=2, sort_keys=True))
        return 2
    probe = CodexWritableRootProbe(
        CodexProbeRequest(
            environment=environment,
            candidate_worktree=arguments.candidate_worktree,
            controller=ControllerIdentity(
                pane_id=arguments.controller_pane,
                worktree_path=arguments.controller_worktree,
                session_id=arguments.controller_session,
                agent_type=arguments.controller_agent_type,
            ),
            probe_home=arguments.probe_home,
            writable_root=arguments.writable_root,
            artifact_directory=arguments.artifact_directory,
        ),
        terminal=ProwlTerminal(prowl, prowl.SubprocessRunner()),
        recovery=load_recovery_module(),
        authentication=DiscoveryAuthentication(selection, run_probe_process),
    )
    record = probe.run()
    print(json.dumps(record.as_json(), indent=2, sort_keys=True))
    return 0 if record.stop is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
