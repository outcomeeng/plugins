"""Plan isolated native auditor-dispatch rows from the shipped auditor definitions."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.agents import (
    AGENT_TOOLS_FIELD,
    ALL_TOOLS_SENTINEL,
    agent_tool_grants,
)
from outcomeeng.distribution.build import agent_capability, agent_dispatch_name
from outcomeeng.distribution.contracts import CLAUDE_DIST_RELATIVE, Target
from outcomeeng.distribution.installation import (
    CLAUDE_EXECUTABLE,
    CODEX_EXEC_SUBCOMMAND,
    CODEX_EXECUTABLE,
    CODEX_HOME_CONFIG_PATH,
    CODEX_HOME_ENV,
    ISOLATED_CLAUDE_CONFIG_DIRECTORY,
    ISOLATED_CODEX_HOME_DIRECTORY,
    generated_codex_agents_root,
)
from outcomeeng.distribution.native_profile_execution import (
    EvidenceSanitizer,
    NativeCommandRunner,
)
from outcomeeng.validation.implementation_audit_contract import (
    EVENT_RUN_ID_FIELD,
    RUN_EVENTS_FIELD,
    RUN_TERMINAL_STATUS_FIELD,
    RUN_TOKEN_FIELD,
    AuditTerminalStatus,
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
SCRATCH_DIRECTORY: Final = "scratch"
"""The row's session scratch directory, beside its fixture repository under the row's state root."""
SCRATCH_ENVIRONMENT_VARIABLES: Final = ("RUNNER_TEMP", "TMPDIR")
"""The variables that name the scratch location a dispatched session writes its payload files to."""
CONFIGURATION_FILENAME: Final = "configuration.json"
LOADING_FILENAME: Final = "loading.json"
RESULT_FILENAME: Final = "result.json"
BLOCKED_MARKER: Final = "BLOCKED"
RUN_FILE_WORD_PATTERN: Final = re.compile(r"[^\s\"'`<>(){}\[\],]+")
SENTENCE_PUNCTUATION: Final = ".;:!?"
CODEX_STRICT_CONFIG_OPTION: Final = "--strict-config"
"""The Codex option that refuses a configuration key the CLI does not recognize."""

NATIVE_LAUNCH_COMMANDS: Final[Mapping[Target, tuple[str, ...]]] = {
    Target.CLAUDE: (
        CLAUDE_EXECUTABLE,
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
    ),
    Target.CODEX: (
        CODEX_EXECUTABLE,
        CODEX_EXEC_SUBCOMMAND,
        "--json",
        CODEX_STRICT_CONFIG_OPTION,
        "--skip-git-repo-check",
    ),
}
"""Each harness's headless launch command, before the dispatch prompt is placed."""

CLAUDE_ADD_DIRECTORY_OPTION: Final = "--add-dir"
CLAUDE_ALLOWED_TOOLS_OPTION: Final = "--allowedTools"
CLAUDE_ALLOWED_TOOLS_SEPARATOR: Final = ","
CODEX_WORKSPACE_WRITE_OPTIONS: Final = (
    "--sandbox",
    "workspace-write",
    "-c",
    'approval_policy="never"',
)
"""The Codex parent's sandbox and approval options: writes reach only the writable roots, and no call waits on an approval."""
CODEX_SANDBOX_WORKSPACE_WRITE_TABLE: Final = "sandbox_workspace_write"
CODEX_WRITABLE_ROOTS_KEY: Final = "writable_roots"

RESULT_RUN_TOKEN_KEY: Final = "run_token"
RESULT_RUN_FILE_KEY: Final = "run_file"
RESULT_PROJECTION_KEY: Final = "projection"
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
    RESULT_PROJECTION_KEY,
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

GIT_EXECUTABLE: Final = "git"
FIXTURE_BRANCH: Final = "main"
FIXTURE_REMOTE: Final = "origin"
FIXTURE_IGNORE: Final = (".gitignore", ".spx/\n")
"""The base commit's one file: it keeps the run store the auditor writes out of the fixture's status."""
FIXTURE_IDENTITY: Final = "Native auditor dispatch fixture"
FIXTURE_EMAIL: Final = "fixture@native-auditor-dispatch.invalid"
FIXTURE_GIT_TIMEOUT_SECONDS: Final = 30
FIXTURE_BASE_MESSAGE: Final = "base"
FIXTURE_HEAD_MESSAGE: Final = "add the dispatch fixture"


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
    scratch_path: Path
    configuration_path: Path
    loading_path: Path
    result_path: Path
    launch_command: tuple[str, ...]

    @property
    def access_roots(self) -> tuple[Path, Path]:
        """The directories the row's parent session reaches: its fixture repository and its scratch directory."""
        return (self.fixture_path.parent, self.scratch_path)


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
    return agent_dispatch_name(
        AUDITOR_PLUGIN, auditor, capability=agent_capability(target)
    )


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
                    scratch_path=row_state / SCRATCH_DIRECTORY,
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
    _materialize_fixture_repository(row)
    row.scratch_path.mkdir(parents=True, exist_ok=True)
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


def _materialize_fixture_repository(row: NativeAuditorRow) -> None:
    """Commit the inert fixture as the one change of a git repository the auditor can measure.

    The shipped auditors resolve the fixture's repository root and judge the
    changeset from `origin/HEAD` to `HEAD`, so the fixture's directory is a
    repository whose base commit `origin/HEAD` names and whose head commit adds
    the fixture, with a clean status. Git runs with no global or system
    configuration, so the host's settings change nothing in the fixture.
    """
    repository = row.fixture_path.parent
    repository.mkdir(parents=True, exist_ok=True)
    ignore_name, ignore_text = FIXTURE_IGNORE
    (repository / ignore_name).write_text(ignore_text, encoding="utf-8")
    _fixture_git(repository, "init", "--quiet", f"--initial-branch={FIXTURE_BRANCH}")
    _fixture_git(repository, "add", "--", ignore_name)
    _fixture_git(repository, "commit", "--quiet", "--message", FIXTURE_BASE_MESSAGE)
    remote_branch = f"refs/remotes/{FIXTURE_REMOTE}/{FIXTURE_BRANCH}"
    _fixture_git(repository, "update-ref", remote_branch, "HEAD")
    _fixture_git(
        repository, "symbolic-ref", f"refs/remotes/{FIXTURE_REMOTE}/HEAD", remote_branch
    )
    _, fixture_text = AUDITOR_FIXTURES[row.auditor]
    row.fixture_path.write_text(fixture_text, encoding="utf-8")
    _fixture_git(repository, "add", "--", row.fixture_path.name)
    _fixture_git(repository, "commit", "--quiet", "--message", FIXTURE_HEAD_MESSAGE)


def _fixture_git(repository: Path, *arguments: str) -> None:
    """Run one git command in the fixture repository; a failure is the row's terminal condition."""
    command = (GIT_EXECUTABLE, *arguments)
    result = subprocess.run(
        command,
        cwd=repository,
        env={
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(repository),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": FIXTURE_IDENTITY,
            "GIT_AUTHOR_EMAIL": FIXTURE_EMAIL,
            "GIT_COMMITTER_NAME": FIXTURE_IDENTITY,
            "GIT_COMMITTER_EMAIL": FIXTURE_EMAIL,
        },
        check=False,
        capture_output=True,
        text=True,
        timeout=FIXTURE_GIT_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        raise OSError(
            f"fixture repository command {' '.join(command)} exited "
            f"{result.returncode}: {result.stderr.strip()}"
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
    """The parent command: the harness's launch command, the row's access grants, and the prompt.

    A Claude Code parent reaches each access root through `--add-dir` and
    approves exactly the dispatched definition's `tools` grants, because a
    headless session refuses every call that would wait on an approval. A Codex
    parent runs under the workspace-write sandbox with no approval, and reaches
    the access roots through the writable roots its `CODEX_HOME` declares.
    """
    prompt = _dispatch_prompt(row)
    if row.target is Target.CLAUDE:
        directories = (
            argument
            for root in row.access_roots
            for argument in (CLAUDE_ADD_DIRECTORY_OPTION, str(root))
        )
        return (
            row.launch_command[0],
            "-p",
            prompt,
            *row.launch_command[2:],
            *directories,
            CLAUDE_ALLOWED_TOOLS_OPTION,
            CLAUDE_ALLOWED_TOOLS_SEPARATOR.join(_claude_tool_grants(row)),
        )
    return (
        *row.launch_command,
        *CODEX_WORKSPACE_WRITE_OPTIONS,
        "-C",
        str(checkout),
        prompt,
    )


def _claude_tool_grants(row: NativeAuditorRow) -> tuple[str, ...]:
    """The `tools` grants the row's Claude Code definition declares; a definition with none, or with every tool, launches nothing.

    An empty `--allowedTools` value approves no call, so the dispatched auditor
    could only stall on its first approval. A grant of every tool names no
    exact set the parent could approve, and the parent runs no bypass mode. In
    either case the row refuses before the parent session starts.
    """
    grants = agent_tool_grants(row.native_definition_path)
    if not grants:
        raise ValueError(
            f"Claude Code auditor definition {row.native_definition_path} for "
            f"{row.native_name} declares no `{AGENT_TOOLS_FIELD}` grant"
        )
    if ALL_TOOLS_SENTINEL in grants:
        raise ValueError(
            f"Claude Code auditor definition {row.native_definition_path} for "
            f"{row.native_name} grants every tool through "
            f"`{AGENT_TOOLS_FIELD}: {ALL_TOOLS_SENTINEL}`"
        )
    return grants


def _session_environment(
    row: NativeAuditorRow, environment: Mapping[str, str]
) -> dict[str, str]:
    """The parent session's environment, naming the row's scratch directory as its scratch location."""
    scratch = str(row.scratch_path)
    return {
        **environment,
        **dict.fromkeys(SCRATCH_ENVIRONMENT_VARIABLES, scratch),
    }


def _declare_codex_writable_roots(
    row: NativeAuditorRow, environment: Mapping[str, str]
) -> None:
    """Name the row's access roots as the writable roots of the selected `CODEX_HOME`.

    A dispatched Codex child inherits the writable roots only from a top-level
    `[sandbox_workspace_write]` table of the selected home's `config.toml`, so
    the table is appended there and every entry the home already holds is kept.
    """
    home = environment.get(CODEX_HOME_ENV)
    if not home:
        raise ValueError(f"Codex auditor dispatch requires a selected {CODEX_HOME_ENV}")
    config = Path(home) / CODEX_HOME_CONFIG_PATH
    text = config.read_text(encoding="utf-8") if config.exists() else ""
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"unreadable Codex configuration {config}: {error}") from error
    if CODEX_SANDBOX_WORKSPACE_WRITE_TABLE in document:
        raise ValueError(
            f"Codex configuration {config} already declares "
            f"[{CODEX_SANDBOX_WORKSPACE_WRITE_TABLE}]"
        )
    roots = ", ".join(json.dumps(str(root)) for root in row.access_roots)
    table = (
        f"[{CODEX_SANDBOX_WORKSPACE_WRITE_TABLE}]\n"
        f"{CODEX_WRITABLE_ROOTS_KEY} = [{roots}]\n"
    )
    separator = "\n" if text and not text.endswith("\n") else ""
    config.write_text(  # NOSONAR S2083 - the home is the row's own disposable CODEX_HOME
        f"{text}{separator}{table}", encoding="utf-8"
    )


def run_native_auditor_row(
    row: NativeAuditorRow,
    *,
    checkout: Path,
    environment: Mapping[str, str],
    parent: NativeCommandRunner,
    sanitize: EvidenceSanitizer,
) -> NativeAuditorDispatchObservation:
    """Make the one native dispatch of an auditor from already installed disposable state.

    Every refusal — a Codex home whose writable roots cannot be declared, a
    Claude Code definition that declares no tool grant — raises `ValueError`
    before the parent runner is called, so a refused row launches nothing.
    """
    if row.target is Target.CODEX:
        _declare_codex_writable_roots(row, environment)
    command = _launch_command(row, checkout)
    result = parent(command, checkout, _session_environment(row, environment))
    stdout = sanitize(result.stdout)
    stderr = sanitize(result.stderr)
    message = _returned_message(row.target, stdout)
    projection = _rendered_projection(message)
    run_token = projection[RUN_TOKEN_FIELD] if projection else None
    run_file = _run_file(message, projection)
    blocked = projection is None and BLOCKED_MARKER in message
    terminal_condition: str | None = None
    if result.returncode != 0:
        terminal_condition = f"native parent session exited {result.returncode}"
    elif blocked:
        terminal_condition = "auditor dispatch returned a blocked diagnostic"
    elif run_token is None:
        terminal_condition = "auditor dispatch returned no run token"
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
            RESULT_PROJECTION_KEY: projection,
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


def _rendered_projection(message: str) -> dict[str, object] | None:
    """The rendered SPX projection a message carries: the first JSON object with a run token and a terminal status."""
    decoder = json.JSONDecoder()
    for start, character in enumerate(message):
        if character != "{":
            continue
        try:
            document, _ = decoder.raw_decode(message, start)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(document, dict)
            and isinstance(document.get(RUN_TOKEN_FIELD), str)
            and document.get(RUN_TERMINAL_STATUS_FIELD)
            in {status.value for status in AuditTerminalStatus}
        ):
            return document
    return None


def _run_file(message: str, projection: Mapping[str, object] | None) -> str | None:
    """The run file a message returns: its longest word ending with the run file name the rendered projection records."""
    name = _projection_run_file_name(projection)
    if name is None:
        return None
    words = (
        word.rstrip(SENTENCE_PUNCTUATION)
        for word in RUN_FILE_WORD_PATTERN.findall(message)
    )
    return max((word for word in words if word.endswith(name)), key=len, default=name)


def _projection_run_file_name(projection: Mapping[str, object] | None) -> str | None:
    """The run file name the first rendered event of a projection carries."""
    events = projection.get(RUN_EVENTS_FIELD) if projection else None
    if not isinstance(events, list):
        return None
    for event in events:
        name = event.get(EVENT_RUN_ID_FIELD) if isinstance(event, dict) else None
        if isinstance(name, str) and name:
            return name
    return None


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
