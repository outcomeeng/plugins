#!/usr/bin/env python3
"""Configuration, state, adapter access, and pane guards for position direction."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import tempfile
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

SKILLS_ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATION_DIRECTORY = Path(".spx") / "orchestration"
STATE_DIRECTORY = "state"
FRONT_MATTER_FENCE = "+++"
RESUME_NOTE_FILE = "resume-note.md"
RUNGS_FILE = "rungs.json"
QUIET_FILE = "quiet.json"
OBSERVATIONS_FILE = "observations.json"

ENVIRONMENT_HERDR = "herdr"
ENVIRONMENT_PROWL = "prowl"
ENVIRONMENTS = (ENVIRONMENT_HERDR, ENVIRONMENT_PROWL)

MAIL_KEYS = frozenset({"channel", "agent"})
POSITION_FIELDS = frozenset(
    {"name", "environment", "cwd", "mail_name", "stall_minutes", "context_percent"}
)
GROUP_FIELDS = frozenset({"label", "environment", "cwd_prefix", "exclusions"})
DEFAULT_RESUME_LINE = (
    "Run /spec-tree:understand, read the resume note at {resume_note}, "
    "read the expectations at {expectations}, and read the mail on {channel}."
)
DEFAULTS: Mapping[str, Any] = {
    "mail": {"channel": None, "agent": None},
    "positions": [],
    "executor_groups": [],
    "launchers": {},
    "untouchable_panes": [],
    "advisor": None,
    "interval_seconds": 1800,
    "compact_at_percent": 30,
    "doorbell_start_delay_seconds": 300,
    "pace": None,
    "resume_line": None,
}

QUESTION_SCREEN_PATTERNS = (
    re.compile(r"\(y/n\)", re.IGNORECASE),
    re.compile(r"do you want to", re.IGNORECASE),
    re.compile(r"❯\s*1\.\s*yes", re.IGNORECASE),
    re.compile(r"\bapprove\b.*\?", re.IGNORECASE),
    re.compile(r"\ballow\b.*\?", re.IGNORECASE),
)
OPERATOR_ORIGIN = "operator"


class DirectionError(RuntimeError):
    """A stop the skill reports verbatim: it names what failed and changes nothing."""


def load_sibling(skill: str, module: str) -> ModuleType:
    """Import a same-plugin provider script by a path relative to this file."""
    path = SKILLS_ROOT / skill / "scripts" / f"{module}.py"
    spec = importlib.util.spec_from_file_location(f"_direction_{module}", path)
    if spec is None or spec.loader is None:
        raise DirectionError(f"The provider script {module} cannot be loaded.")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def override_file_name(display_name: str) -> str:
    return display_name.lower().replace(" ", "-") + ".md"


def common_directory(mail: ModuleType) -> Path:
    """The repository's common Git directory, resolved by the mail adapter."""
    try:
        return Path(mail.resolve_project_key(mail.SubprocessRunner()))
    except mail.AgentMailError as error:
        raise DirectionError(str(error)) from error


def split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FRONT_MATTER_FENCE:
        return "", text
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONT_MATTER_FENCE:
            return "".join(lines[1:index]), "".join(lines[index + 1 :])
    raise ValueError("the front matter opens with +++ and never closes")


def _require_fields(
    entry: object, fields: frozenset[str], label: str, source: Path
) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise DirectionError(f"{source}: {label} must be a table.")
    unknown = sorted(set(entry) - fields)
    missing = sorted(fields - set(entry) - {"exclusions"})
    if unknown or missing:
        raise DirectionError(
            f"{source}: {label} has unknown {unknown} and missing {missing}."
        )
    return entry


def _validated(settings: dict[str, Any], source: Path) -> dict[str, Any]:
    unknown = sorted(set(settings) - set(DEFAULTS))
    if unknown:
        raise DirectionError(f"{source}: unknown key {unknown[0]}.")
    mail = settings.get("mail", {})
    if not isinstance(mail, dict) or set(mail) - MAIL_KEYS:
        raise DirectionError(
            f"{source}: key mail must be a table of channel and agent."
        )
    for index, entry in enumerate(settings.get("positions", [])):
        position = _require_fields(
            entry, POSITION_FIELDS, f"positions[{index}]", source
        )
        if position["environment"] not in ENVIRONMENTS:
            raise DirectionError(
                f"{source}: positions[{index}].environment must be one of {ENVIRONMENTS}."
            )
    for index, entry in enumerate(settings.get("executor_groups", [])):
        group = _require_fields(
            entry, GROUP_FIELDS, f"executor_groups[{index}]", source
        )
        if group["environment"] not in ENVIRONMENTS:
            raise DirectionError(
                f"{source}: executor_groups[{index}].environment must be one of {ENVIRONMENTS}."
            )
    for key in (
        "interval_seconds",
        "compact_at_percent",
        "doorbell_start_delay_seconds",
    ):
        value = settings.get(key, DEFAULTS[key])
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise DirectionError(f"{source}: key {key} must be a positive integer.")
    return settings


def compose_configuration(common_dir: Path, display_name: str) -> dict[str, Any]:
    """Compose a position's override file over the shipped defaults."""
    orchestration = common_dir / ORCHESTRATION_DIRECTORY
    source = orchestration / override_file_name(display_name)
    settings: dict[str, Any] = {}
    expectations = ""
    present = source.is_file()
    if present:
        try:
            front, expectations = split_front_matter(source.read_text(encoding="utf-8"))
            settings = tomllib.loads(front)
        except (ValueError, tomllib.TOMLDecodeError, OSError) as error:
            raise DirectionError(f"{source}: malformed file: {error}.") from error
        _validated(settings, source)
    composed: dict[str, Any] = {
        key: settings.get(key, default) for key, default in DEFAULTS.items()
    }
    composed["mail"] = {**DEFAULTS["mail"], **settings.get("mail", {})}
    if composed["mail"]["channel"] is None:
        composed["mail"]["channel"] = str(common_dir)
    resume_note = orchestration / STATE_DIRECTORY / RESUME_NOTE_FILE
    if composed["resume_line"] is None:
        composed["resume_line"] = DEFAULT_RESUME_LINE.format(
            resume_note=resume_note,
            expectations=source,
            channel=composed["mail"]["channel"],
        )
    composed["expectations"] = expectations
    composed["overrideFile"] = {"path": str(source), "present": present}
    composed["stateDirectory"] = str(orchestration / STATE_DIRECTORY)
    composed["resumeNote"] = str(resume_note)
    return composed


def read_state(state_dir: Path, name: str) -> dict[str, Any]:
    path = state_dir / name
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise DirectionError(f"{path}: unreadable state: {error}.") from error
    return value if isinstance(value, dict) else {}


def write_state(state_dir: Path, name: str, value: Mapping[str, Any]) -> None:
    """Replace one state file atomically; the renamed temporary file leaves nothing."""
    state_dir.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=state_dir, prefix=f".{name}.")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, sort_keys=True)
        os.replace(temporary, state_dir / name)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


@dataclass(frozen=True)
class Pane:
    """One pane as an environment adapter reports it."""

    environment: str
    pane: str
    cwd: str
    status: str | None
    name: str | None
    kind: str | None


class Environments:
    """Every pane operation, reached through the coding-agents environment adapters."""

    def __init__(
        self, herdr: ModuleType, prowl: ModuleType, runners: Mapping[str, Any]
    ):
        self._modules = {ENVIRONMENT_HERDR: herdr, ENVIRONMENT_PROWL: prowl}
        self._runners = runners

    def _execute(
        self, environment: str, operation: str, **arguments: Any
    ) -> dict[str, Any]:
        module = self._modules[environment]
        request = {
            "schemaVersion": module.SCHEMA_VERSION,
            "operation": operation,
            "arguments": arguments,
        }
        return module.execute(request, self._runners[environment])

    def panes(self, environment: str) -> list[Pane]:
        if environment == ENVIRONMENT_HERDR:
            result = self._execute(environment, "inventory")
            if result.get("status") != "succeeded":
                raise DirectionError(f"herdr inventory: {result.get('detail')}")
            return [
                Pane(
                    environment,
                    str(item.get("pane_id")),
                    str(item.get("cwd")),
                    item.get("agent_status"),
                    item.get("name"),
                    item.get("agent"),
                )
                for item in result["agents"]
            ]
        result = self._execute(environment, "agents")
        if result.get("status") != "succeeded":
            raise DirectionError(f"prowl agents: {result.get('detail')}")
        try:
            participants = self._modules[environment].participants_from_agents(
                result["response"]
            )
        except self._modules[environment].ProwlEnvironmentError as error:
            raise DirectionError(f"prowl agents: {error}") from error
        return [
            Pane(environment, p["pane"], p["worktree"], None, p["agent"], None)
            for p in participants
        ]

    def read(self, pane: Pane) -> str:
        if pane.environment == ENVIRONMENT_HERDR:
            result = self._execute(pane.environment, "read", pane=pane.pane)
            body = result.get("response", {}).get("output", "")
        else:
            result = self._execute(pane.environment, "read", pane=pane.pane)
            body = _screen_text(result.get("response", {}))
        if result.get("status") != "succeeded":
            raise DirectionError(f"{pane.environment} read: {result.get('detail')}")
        return body

    def prompt(self, pane: Pane, text: str) -> dict[str, Any]:
        operation = "prompt" if pane.environment == ENVIRONMENT_HERDR else "send"
        return self._execute(pane.environment, operation, pane=pane.pane, text=text)

    def restart(self, pane: Pane, timeout_ms: int) -> dict[str, Any]:
        """Stop and relaunch a herdr session; only herdr hosts a restart."""
        if pane.environment != ENVIRONMENT_HERDR or pane.kind is None:
            return {
                "status": "operation-unavailable",
                "detail": "restart needs a herdr session",
            }
        stopped = self._execute(
            pane.environment, "stop", pane=pane.pane, mutationAuthorized=True
        )
        if stopped.get("status") != "succeeded":
            return stopped
        return self._execute(
            pane.environment,
            "relaunch",
            name=pane.name or pane.kind,
            kind=pane.kind,
            pane=pane.pane,
            timeout=timeout_ms,
            mutationAuthorized=True,
        )


def _screen_text(response: object) -> str:
    """Collect the terminal text fields of a Prowl read response."""
    if isinstance(response, dict):
        for key in ("text", "output", "content"):
            if isinstance(response.get(key), str):
                return response[key]
        return "\n".join(_screen_text(value) for value in response.values())
    if isinstance(response, list):
        return "\n".join(_screen_text(value) for value in response)
    return ""


def at_question_screen(screen: str, status: str | None) -> bool:
    return status == "blocked" or any(
        p.search(screen) for p in QUESTION_SCREEN_PATTERNS
    )


def guard_reasons(
    pane: Pane,
    screen: str,
    untouchable: list[str],
    last_prompt_origin: str | None = None,
) -> list[str]:
    """Why no input may reach this pane; an empty list means the pane is open."""
    reasons: list[str] = []
    if pane.pane in untouchable or (pane.name or "") in untouchable:
        reasons.append("untouchable")
    if last_prompt_origin == OPERATOR_ORIGIN:
        reasons.append("operator-prompt")
    if at_question_screen(screen, pane.status):
        reasons.append("question-or-approval-screen")
    return reasons


def resolve_pane(panes: list[Pane], cwd: str) -> Pane | None:
    matches = [pane for pane in panes if pane.cwd == cwd]
    return matches[0] if len(matches) == 1 else None


def quiet_minutes(state: dict[str, Any], key: str, screen: str, now: float) -> float:
    """Minutes the pane's screen has held; records a changed screen as new."""
    digest = hashlib.sha256(screen.encode("utf-8")).hexdigest()
    entry = state.get(key)
    if not isinstance(entry, dict) or entry.get("digest") != digest:
        state[key] = {"digest": digest, "since": now}
        return 0.0
    return round((now - float(entry["since"])) / 60, 1)


def now_seconds() -> float:
    return time.time()
