"""Plan isolated native auditor-dispatch rows from the shipped auditor definitions."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.agents import (
    FLAT_AGENT_PLUGIN_SEPARATOR,
    NATIVE_AGENT_PLUGIN_SEPARATOR,
)
from outcomeeng.distribution.contracts import CLAUDE_DIST_RELATIVE, Target
from outcomeeng.distribution.installation import (
    CLAUDE_EXECUTABLE,
    CODEX_EXEC_SUBCOMMAND,
    CODEX_EXECUTABLE,
    ISOLATED_CLAUDE_CONFIG_DIRECTORY,
    ISOLATED_CODEX_HOME_DIRECTORY,
    generated_codex_agents_root,
)
from outcomeeng.distribution.native_profile_execution import (
    EvidenceSanitizer,
    NativeCommandRunner,
)

NATIVE_AUDITOR_ARTIFACTS_DIRECTORY: Final = Path("native-auditor-dispatch")
AUDITOR_PLUGIN: Final = "instructions"
"""The plugin whose auditor definitions the marketplace ships for dispatch."""
SHIPPED_AUDITORS: Final = ("skill-auditor", "subagent-auditor")
"""The authored names of the auditors an auditor-dispatch row covers."""
CLAUDE_AGENT_SUFFIX: Final = ".md"
CODEX_AGENT_SUFFIX: Final = ".toml"
AGENTS_DIRECTORY: Final = "agents"
FIXTURE_DIRECTORY: Final = "fixture"
CONFIGURATION_FILENAME: Final = "configuration.json"
LOADING_FILENAME: Final = "loading.json"
RESULT_FILENAME: Final = "result.json"
BLOCKED_MARKER: Final = "BLOCKED"
RUN_TOKEN_PATTERN: Final = re.compile(r"run\s*token\W+([a-z0-9_.:-]+)", re.IGNORECASE)
RUN_FILE_PATTERN: Final = re.compile(r"run\s*file\W+(\S+)", re.IGNORECASE)

NATIVE_LAUNCH_COMMANDS: Final[Mapping[Target, tuple[str, ...]]] = {
    Target.CLAUDE: (
        CLAUDE_EXECUTABLE,
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--forward-subagent-text",
    ),
    Target.CODEX: (
        CODEX_EXECUTABLE,
        CODEX_EXEC_SUBCOMMAND,
        "--json",
        "--strict-config",
        "--skip-git-repo-check",
    ),
}
"""Each harness's headless launch command, before the dispatch prompt is placed."""

RESULT_RUN_TOKEN_KEY: Final = "run_token"
RESULT_RUN_FILE_KEY: Final = "run_file"
RESULT_BLOCKED_KEY: Final = "blocked"
RESULT_TERMINAL_CONDITION_KEY: Final = "terminal_condition"
CONFIGURATION_SHIPPED_SHA256_KEY: Final = "shipped_definition_sha256"

RESULT_DOCUMENT_KEYS: Final = (
    "identifier",
    "parent_command",
    "exit_code",
    "stdout",
    "stderr",
    "returned_message",
    RESULT_RUN_TOKEN_KEY,
    RESULT_RUN_FILE_KEY,
    RESULT_BLOCKED_KEY,
)
"""The fields a dispatched row's result document carries before a failure is recorded."""

AUDITOR_FIXTURES: Final[Mapping[str, tuple[str, str]]] = {
    "skill-auditor": (
        "SKILL.md",
        "---\nname: dispatch-fixture\ndescription: Inert fixture for auditor dispatch.\n---\n\n"
        "Do nothing.\n",
    ),
    "subagent-auditor": (
        "dispatch-fixture.md",
        "---\nname: dispatch-fixture\ndescription: Inert fixture for auditor dispatch.\n---\n\n"
        "Do nothing.\n",
    ),
}
"""Each auditor's inert whole-payload dispatch target: file name and exact content."""


@dataclass(frozen=True)
class NativeAuditorRow:
    """One shipped auditor on one supported harness, rendered into an isolated dispatch."""

    identifier: str
    target: Target
    auditor: str
    native_name: str
    shipped_definition_path: Path
    state_root: Path
    native_definition_path: Path
    fixture_path: Path
    configuration_path: Path
    loading_path: Path
    result_path: Path
    launch_command: tuple[str, ...]


@dataclass(frozen=True)
class NativeAuditorDispatchObservation:
    """Retained paths and terminal condition for one dispatched auditor row."""

    row: NativeAuditorRow
    install_exit_code: int | None
    launch_exit_code: int | None
    terminal_condition: str | None


def shipped_definition_path(checkout: Path, target: Target, auditor: str) -> Path:
    """The generated definition one harness ships for one auditor."""
    if target is Target.CLAUDE:
        return (
            checkout
            / CLAUDE_DIST_RELATIVE
            / AUDITOR_PLUGIN
            / AGENTS_DIRECTORY
            / f"{auditor}{CLAUDE_AGENT_SUFFIX}"
        )
    return (
        generated_codex_agents_root(checkout, AUDITOR_PLUGIN)
        / f"{native_name(target, auditor)}{CODEX_AGENT_SUFFIX}"
    )


def native_name(target: Target, auditor: str) -> str:
    """The name one harness dispatches an auditor by."""
    separator = (
        NATIVE_AGENT_PLUGIN_SEPARATOR
        if target is Target.CLAUDE
        else FLAT_AGENT_PLUGIN_SEPARATOR
    )
    return f"{AUDITOR_PLUGIN}{separator}{auditor}"


def native_auditor_rows(
    checkout: Path,
    artifact_root: Path = NATIVE_AUDITOR_ARTIFACTS_DIRECTORY,
    state_root: Path = Path("native-auditor-state"),
) -> tuple[NativeAuditorRow, ...]:
    """Return one immutable row for every pair of a supported harness and a shipped auditor.

    The rows are a pure projection: a row exists exactly when the checkout's
    generated tree holds the shipped definition it names, and every path derives
    from that definition's identity.
    """
    rows: list[NativeAuditorRow] = []
    for target in Target:
        for auditor in SHIPPED_AUDITORS:
            definition = shipped_definition_path(checkout, target, auditor)
            if not definition.is_file():
                raise FileNotFoundError(
                    f"shipped auditor definition is absent: {definition}"
                )
            identifier = f"{target.value}-{auditor}"
            row_state = state_root / identifier
            row_artifacts = artifact_root / identifier
            fixture_name, _ = AUDITOR_FIXTURES[auditor]
            rows.append(
                NativeAuditorRow(
                    identifier=identifier,
                    target=target,
                    auditor=auditor,
                    native_name=native_name(target, auditor),
                    shipped_definition_path=definition,
                    state_root=row_state,
                    native_definition_path=_native_definition_path(
                        row_state, target, definition.name
                    ),
                    fixture_path=row_state / FIXTURE_DIRECTORY / fixture_name,
                    configuration_path=row_artifacts / CONFIGURATION_FILENAME,
                    loading_path=row_artifacts / LOADING_FILENAME,
                    result_path=row_artifacts / RESULT_FILENAME,
                    launch_command=_native_launch_command(target),
                )
            )
    return tuple(rows)


def _native_definition_path(state_root: Path, target: Target, name: str) -> Path:
    agent_home = (
        ISOLATED_CLAUDE_CONFIG_DIRECTORY
        if target is Target.CLAUDE
        else ISOLATED_CODEX_HOME_DIRECTORY
    )
    return state_root / agent_home / AGENTS_DIRECTORY / name


def _native_launch_command(target: Target) -> tuple[str, ...]:
    return NATIVE_LAUNCH_COMMANDS[target]


def materialize_native_auditor(row: NativeAuditorRow) -> None:
    """Place the shipped definition and the inert fixture in the row's disposable state."""
    row.native_definition_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(row.shipped_definition_path, row.native_definition_path)
    _, fixture_text = AUDITOR_FIXTURES[row.auditor]
    row.fixture_path.parent.mkdir(parents=True, exist_ok=True)
    row.fixture_path.write_text(fixture_text, encoding="utf-8")
    _write_json(
        row.configuration_path,
        {
            "identifier": row.identifier,
            "harness": row.target.value,
            "auditor": row.auditor,
            "native_name": row.native_name,
            "shipped_definition_path": str(row.shipped_definition_path),
            CONFIGURATION_SHIPPED_SHA256_KEY: hashlib.sha256(
                row.shipped_definition_path.read_bytes()
            ).hexdigest(),
            "native_definition_path": str(row.native_definition_path),
            "fixture_path": str(row.fixture_path),
            "launch_command": list(row.launch_command),
        },
    )
    _write_json(
        row.loading_path,
        {
            "identifier": row.identifier,
            "native_definition_path": str(row.native_definition_path),
            "materialized": True,
            "discovered": None,
        },
    )


def _dispatch_prompt(row: NativeAuditorRow) -> str:
    isolation = (
        ' Explicitly set fork_turns to "none".' if row.target is Target.CODEX else ""
    )
    return (
        "Use the native subagent tool exactly once to launch "
        f"`{row.native_name}` with the prompt `{row.fixture_path}`."
        f"{isolation} Wait for its result and reply with that result verbatim. "
        "Do not launch another child."
    )


def _launch_command(row: NativeAuditorRow, checkout: Path) -> tuple[str, ...]:
    prompt = _dispatch_prompt(row)
    if row.target is Target.CLAUDE:
        return (row.launch_command[0], "-p", prompt, *row.launch_command[2:])
    return (*row.launch_command, "-C", str(checkout), prompt)


def run_native_auditor_row(
    row: NativeAuditorRow,
    *,
    checkout: Path,
    environment: Mapping[str, str],
    parent: NativeCommandRunner,
    sanitize: EvidenceSanitizer,
) -> NativeAuditorDispatchObservation:
    """Make the one native dispatch of an auditor from already installed disposable state."""
    result = parent(_launch_command(row, checkout), checkout, dict(environment))
    stdout = sanitize(result.stdout)
    stderr = sanitize(result.stderr)
    message = _returned_message(row.target, stdout)
    run_token = _first_group(RUN_TOKEN_PATTERN, message)
    run_file = _first_group(RUN_FILE_PATTERN, message)
    blocked = BLOCKED_MARKER in message
    terminal_condition: str | None = None
    if result.returncode != 0:
        terminal_condition = f"native parent session exited {result.returncode}"
    elif run_token is None and not blocked:
        terminal_condition = (
            "auditor dispatch returned neither a run token nor a blocked diagnostic"
        )
    _write_json(
        row.loading_path,
        {
            "identifier": row.identifier,
            "native_definition_path": str(row.native_definition_path),
            "materialized": True,
            "discovered": row.native_name in stdout,
        },
    )
    _write_json(
        row.result_path,
        {
            "identifier": row.identifier,
            "parent_command": list(result.args)
            if not isinstance(result.args, str)
            else result.args,
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "returned_message": message,
            RESULT_RUN_TOKEN_KEY: run_token,
            RESULT_RUN_FILE_KEY: run_file,
            RESULT_BLOCKED_KEY: blocked,
            RESULT_TERMINAL_CONDITION_KEY: terminal_condition,
        },
    )
    return NativeAuditorDispatchObservation(
        row=row,
        install_exit_code=0,
        launch_exit_code=result.returncode,
        terminal_condition=terminal_condition,
    )


def record_native_auditor_failure(
    row: NativeAuditorRow, condition: str, *, install_exit_code: int | None = None
) -> NativeAuditorDispatchObservation:
    """Retain a harness failure as the row's terminal condition, without a retry."""
    retained = (
        json.loads(row.result_path.read_text(encoding="utf-8"))
        if row.result_path.exists()
        else {}
    )
    document: dict[str, object] = {"identifier": row.identifier}
    if isinstance(retained, dict):
        document.update(
            (key, retained[key]) for key in RESULT_DOCUMENT_KEYS if key in retained
        )
    document[RESULT_TERMINAL_CONDITION_KEY] = condition
    document["install_exit_code"] = install_exit_code
    _write_json(row.result_path, document)
    launch_exit_code = document.get("exit_code")
    return NativeAuditorDispatchObservation(
        row,
        install_exit_code,
        launch_exit_code if isinstance(launch_exit_code, int) else None,
        condition,
    )


def _returned_message(target: Target, stream: str) -> str:
    """The last assistant text one harness's machine stream carries."""
    message = ""
    for event in _json_lines(stream):
        if target is Target.CLAUDE and event.get("type") == "result":
            value = event.get("result")
            if isinstance(value, str):
                message = value
        item = event.get("item")
        if (
            target is Target.CODEX
            and event.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        ):
            message = item["text"]
    return message


def _first_group(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1) if match else None


def _json_lines(stream: str) -> Iterable[dict[str, object]]:
    for line in stream.splitlines():
        try:
            document = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(document, dict):
            yield document


def _write_json(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(  # NOSONAR S2083 - row paths derive from the harness's own run directory
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
