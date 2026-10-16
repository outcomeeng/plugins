#!/usr/bin/env python3
"""Configuration, state, adapter access, and pane guards for position direction."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
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
    {
        "name",
        "environment",
        "cwd",
        "mail_name",
        "stall_minutes",
        "context_percent",
    }
)
POSITION_OPTIONAL: frozenset[str] = frozenset()
POSITION_NUMBERS = frozenset({"stall_minutes", "context_percent"})
POSITION_TEXTS = frozenset({"name", "cwd", "mail_name"})
GROUP_FIELDS = frozenset({"label", "environment", "cwd_prefix", "exclusions"})
GROUP_OPTIONAL = frozenset({"exclusions"})
GROUP_TEXTS = frozenset({"label", "cwd_prefix"})
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
    if not path.is_file():
        raise DirectionError(
            f"The provider script {path} does not exist; install the sibling skill "
            f"coding-agents:{skill} in the same plugin so that {module}.py sits "
            "under its scripts directory."
        )
    spec = importlib.util.spec_from_file_location(f"_direction_{module}", path)
    if spec is None or spec.loader is None:
        raise DirectionError(
            f"The provider script {path} cannot be loaded as a Python module; "
            f"reinstall the sibling skill coding-agents:{skill} so that {module}.py "
            "is a readable Python 3.13 or 3.14 file."
        )
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
        raise DirectionError(
            f"the common Git directory cannot be resolved: {error}; run the skill "
            "from inside a Git checkout of the repository."
        ) from error


def invocation_checkout() -> Path:
    """The top-level directory of the checkout the skill runs from."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        raise DirectionError(
            f"the invocation checkout cannot be resolved: {error}; run the skill "
            "from inside a Git checkout of the repository."
        ) from error
    if result.returncode != 0 or not result.stdout.strip():
        detail = result.stderr.strip() or "no command detail"
        raise DirectionError(
            f"the invocation checkout cannot be resolved: {detail}; run the skill "
            "from inside a Git checkout of the repository."
        )
    return Path(result.stdout.strip())


def split_front_matter(text: str) -> tuple[str, str]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FRONT_MATTER_FENCE:
        return "", text
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONT_MATTER_FENCE:
            return "".join(lines[1:index]), "".join(lines[index + 1 :])
    raise ValueError(
        "the front matter opens with +++ and never closes; add a closing +++ line "
        "after the TOML keys"
    )


def _require_fields(
    entry: object,
    fields: frozenset[str],
    optional: frozenset[str],
    label: str,
    source: Path,
) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise DirectionError(
            f"{source}: {label} is a {type(entry).__name__}, not a table; write it "
            f"as a table with the fields {sorted(fields)}."
        )
    unknown = sorted(set(entry) - fields)
    missing = sorted(fields - set(entry) - optional)
    if unknown or missing:
        raise DirectionError(
            f"{source}: {label} has unknown fields {unknown} and missing fields "
            f"{missing}; the valid fields are {sorted(fields)} and only "
            f"{sorted(optional)} may be omitted. "
            "Remove the unknown fields and add the missing ones."
        )
    return entry


def _require_environment(entry: Mapping[str, Any], label: str, source: Path) -> None:
    if entry["environment"] not in ENVIRONMENTS:
        raise DirectionError(
            f"{source}: {label}.environment is {entry['environment']!r}; set it to "
            f"one of {list(ENVIRONMENTS)}."
        )


def _type_stop(
    source: Path, label: str, value: object, accepted: str
) -> DirectionError:
    return DirectionError(
        f"{source}: {label} is {value!r} ({type(value).__name__}); write it as "
        f"{accepted}."
    )


def _require_entry_types(
    entry: Mapping[str, Any],
    texts: frozenset[str],
    numbers: frozenset[str],
    label: str,
    source: Path,
) -> None:
    for field in sorted(texts):
        value = entry[field]
        if not isinstance(value, str) or not value:
            raise _type_stop(source, f"{label}.{field}", value, "a non-empty string")
    for field in sorted(numbers):
        value = entry[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            raise _type_stop(
                source, f"{label}.{field}", value, "a non-negative number such as 30"
            )
    exclusions = entry.get("exclusions", [])
    if not isinstance(exclusions, list) or not all(
        isinstance(x, str) for x in exclusions
    ):
        raise _type_stop(
            source,
            f"{label}.exclusions",
            exclusions,
            'a list of directory-prefix strings such as ["<directory prefix>"]',
        )


def _require_list(settings: Mapping[str, Any], key: str, source: Path) -> list[Any]:
    value = settings.get(key, [])
    if not isinstance(value, list):
        raise _type_stop(
            source,
            f"key {key}",
            value,
            f"an array of tables, each written as [[{key}]]",
        )
    return value


def _require_text_or_none(value: object, label: str, source: Path) -> None:
    if value is not None and not isinstance(value, str):
        raise _type_stop(source, label, value, "a string")


def _validate_mail(settings: Mapping[str, Any], source: Path) -> None:
    mail = settings.get("mail", {})
    if not isinstance(mail, dict):
        raise DirectionError(
            f"{source}: key mail is a {type(mail).__name__}, not a table; write "
            f"[mail] with the keys {sorted(MAIL_KEYS)}."
        )
    unknown_mail = sorted(set(mail) - MAIL_KEYS)
    if unknown_mail:
        raise DirectionError(
            f"{source}: unknown mail keys {unknown_mail}; the valid mail keys are "
            f"{sorted(MAIL_KEYS)}. Remove or rename each unknown key."
        )
    for key in ("channel", "agent"):
        _require_text_or_none(mail.get(key), f"mail.{key}", source)


def _validate_entries(settings: Mapping[str, Any], source: Path) -> None:
    for index, entry in enumerate(_require_list(settings, "positions", source)):
        label = f"positions[{index}]"
        position = _require_fields(
            entry, POSITION_FIELDS, POSITION_OPTIONAL, label, source
        )
        _require_environment(position, label, source)
        _require_entry_types(position, POSITION_TEXTS, POSITION_NUMBERS, label, source)
    for index, entry in enumerate(_require_list(settings, "executor_groups", source)):
        label = f"executor_groups[{index}]"
        group = _require_fields(entry, GROUP_FIELDS, GROUP_OPTIONAL, label, source)
        _require_environment(group, label, source)
        _require_entry_types(group, GROUP_TEXTS, frozenset(), label, source)


def _validate_collections(settings: Mapping[str, Any], source: Path) -> None:
    launchers = settings.get("launchers", {})
    if not isinstance(launchers, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in launchers.items()
    ):
        raise _type_stop(
            source,
            "key launchers",
            launchers,
            'a table mapping a checkout path to a position name, such as [launchers] "<checkout path>" = "<position display name>"',
        )
    untouchable = settings.get("untouchable_panes", [])
    if not isinstance(untouchable, list) or not all(
        isinstance(x, str) for x in untouchable
    ):
        raise _type_stop(
            source,
            "key untouchable_panes",
            untouchable,
            'a list of pane ids or names such as ["w1:p1"]',
        )


def _validate_scalars(settings: Mapping[str, Any], source: Path) -> None:
    for key in ("advisor", "resume_line"):
        _require_text_or_none(settings.get(key), f"key {key}", source)
    for key in (
        "interval_seconds",
        "compact_at_percent",
        "doorbell_start_delay_seconds",
    ):
        value = settings.get(key, DEFAULTS[key])
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise DirectionError(
                f"{source}: key {key} is {value!r}; set it to a positive integer "
                f"such as {DEFAULTS[key]}."
            )


def _validated(settings: dict[str, Any], source: Path) -> dict[str, Any]:
    unknown = sorted(set(settings) - set(DEFAULTS))
    if unknown:
        raise DirectionError(
            f"{source}: unknown keys {unknown}; the valid keys are "
            f"{sorted(DEFAULTS)}. Remove or rename each unknown key."
        )
    _validate_mail(settings, source)
    _validate_entries(settings, source)
    _validate_collections(settings, source)
    _validate_scalars(settings, source)
    return settings


def compose_configuration(
    common_dir: Path, checkout: Path, display_name: str
) -> dict[str, Any]:
    """Compose a position's override file over the shipped defaults.

    The override file is read from the common Git directory; the runtime state
    and the resume note belong to the invocation checkout.
    """
    source = common_dir / ORCHESTRATION_DIRECTORY / override_file_name(display_name)
    state_directory = checkout / ORCHESTRATION_DIRECTORY / STATE_DIRECTORY
    settings: dict[str, Any] = {}
    expectations = ""
    present = source.is_file()
    if present:
        try:
            front, expectations = split_front_matter(source.read_text(encoding="utf-8"))
            settings = tomllib.loads(front)
        except (ValueError, OSError) as error:
            raise DirectionError(
                f"{source}: malformed file: {error}. Fix the front matter between "
                "the +++ lines so that it parses as TOML, or move the file aside "
                "to compose the defaults alone."
            ) from error
        _validated(settings, source)
    composed: dict[str, Any] = {
        key: settings.get(key, default) for key, default in DEFAULTS.items()
    }
    composed["mail"] = {**DEFAULTS["mail"], **settings.get("mail", {})}
    if composed["mail"]["channel"] is None:
        composed["mail"]["channel"] = str(common_dir)
    resume_note = state_directory / RESUME_NOTE_FILE
    if composed["resume_line"] is None:
        composed["resume_line"] = DEFAULT_RESUME_LINE.format(
            resume_note=resume_note,
            expectations=source,
            channel=composed["mail"]["channel"],
        )
    composed["expectations"] = expectations
    composed["overrideFile"] = {"path": str(source), "present": present}
    composed["stateDirectory"] = str(state_directory)
    composed["resumeNote"] = str(resume_note)
    return composed


def read_state(state_dir: Path, name: str) -> dict[str, Any]:
    path = state_dir / name
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise DirectionError(
            f"{path}: unreadable state: {error}. Repair the JSON in the file or "
            "move it to the trash so that the next pass writes it afresh; state "
            "is never configuration."
        ) from error
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
    pane_id: str
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
                raise DirectionError(
                    f"herdr inventory failed with status {result.get('status')!r}: "
                    f"{result.get('detail')}; confirm herdr is running through "
                    "coding-agents:operate-herdr and run the roster again."
                )
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
            raise DirectionError(
                f"prowl agents failed with status {result.get('status')!r}: "
                f"{result.get('detail')}; confirm Prowl is running through "
                "coding-agents:operate-prowl and run the roster again."
            )
        try:
            participants = self._modules[environment].participants_from_agents(
                result["response"]
            )
        except self._modules[environment].ProwlEnvironmentError as error:
            raise DirectionError(
                f"prowl agents returned a response the adapter cannot read: {error}; "
                "run the Prowl agents operation through coding-agents:operate-prowl "
                "and compare its response."
            ) from error
        return [
            Pane(environment, p["pane"], p["worktree"], None, p["agent"], None)
            for p in participants
        ]

    def read(self, pane: Pane) -> str:
        if pane.environment == ENVIRONMENT_HERDR:
            result = self._execute(pane.environment, "read", pane=pane.pane_id)
            body = result.get("response", {}).get("output", "")
        else:
            result = self._execute(pane.environment, "read", pane=pane.pane_id)
            body = _screen_text(result.get("response", {}))
        if result.get("status") != "succeeded":
            raise DirectionError(
                f"{pane.environment} read of pane {pane.pane_id} failed with status "
                f"{result.get('status')!r}: {result.get('detail')}; confirm the pane "
                "still exists in the roster subcommand's output."
            )
        return body

    def prompt(self, pane: Pane, text: str) -> dict[str, Any]:
        operation = "prompt" if pane.environment == ENVIRONMENT_HERDR else "send"
        return self._execute(pane.environment, operation, pane=pane.pane_id, text=text)

    def restart(self, pane: Pane, timeout_ms: int) -> dict[str, Any]:
        """Stop and relaunch a herdr session as the same agent kind, with no launch arguments."""
        if pane.environment != ENVIRONMENT_HERDR or pane.kind is None:
            return {
                "status": "unavailable",
                "detail": f"restart of pane {pane.pane_id} needs a herdr session whose "
                f"inventory item names its agent kind; pane {pane.pane_id} is hosted by "
                f"{pane.environment} with agent kind {pane.kind!r}. Restart it by "
                "hand through its environment skill.",
            }
        stopped = self._execute(
            pane.environment, "stop", pane=pane.pane_id, mutationAuthorized=True
        )
        if stopped.get("status") != "succeeded":
            return stopped
        return self._execute(
            pane.environment,
            "relaunch",
            name=pane.name or pane.kind,
            kind=pane.kind,
            pane=pane.pane_id,
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
    if pane.pane_id in untouchable or (pane.name or "") in untouchable:
        reasons.append("untouchable")
    if last_prompt_origin == OPERATOR_ORIGIN:
        reasons.append("operator-prompt")
    if at_question_screen(screen, pane.status):
        reasons.append("question-or-approval-screen")
    return reasons


def resolve_pane(panes: list[Pane], cwd: str) -> Pane | None:
    matches = [pane for pane in panes if pane.cwd == cwd]
    return matches[0] if len(matches) == 1 else None


def unresolved_pane_detail(
    panes: list[Pane], cwd: str, label: str, environment: str
) -> str:
    """Why a configured working directory resolved to no single pane, and the fix."""
    matched = [pane.pane_id for pane in panes if pane.cwd == cwd]
    available = sorted({pane.cwd for pane in panes})
    found = (
        f"{len(matched)} {environment} panes matched ({matched})"
        if matched
        else f"no {environment} pane matched"
    )
    return (
        f"{label}: configured cwd {cwd!r}: {found}; the cwds available are "
        f"{available}. Set the cwd of the position to exactly one of them, or "
        "start the position's session in that directory."
    )


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
