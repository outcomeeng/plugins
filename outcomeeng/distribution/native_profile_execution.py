"""Plan isolated native profile-execution probes from the central registry."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, Mapping, Protocol

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.native_thread_evidence import (
    NativeThreadReader,
    collect_native_child_evidence,
)
from outcomeeng.distribution.profiles import (
    AGENT_PROFILES,
    AgentProfile,
    CodexConfiguration,
    NativeConfiguration,
    native_configuration_values,
)

NATIVE_PROFILE_ARTIFACTS_DIRECTORY: Final = Path("native-profile-execution")
NATIVE_PROFILE_OVERRIDE_ENVIRONMENT_VARIABLES: Final = frozenset(
    {
        "CLAUDE_CODE_EFFORT_LEVEL",
        "CLAUDE_CODE_SUBAGENT_MODEL",
    }
)

_CLAUDE_EXECUTABLE: Final = "claude"
_CODEX_EXECUTABLE: Final = "codex"


@dataclass(frozen=True)
class NativeProfileRow:
    """One central profile rendered into an isolated native probe lifecycle."""

    identifier: str
    target: Target
    profile: AgentProfile
    configuration: NativeConfiguration
    state_root: Path
    definition_path: Path
    native_definition_path: Path
    loading_path: Path
    result_path: Path
    launch_commands: tuple[tuple[str, ...], ...]


def native_profile_rows(
    artifact_root: Path = NATIVE_PROFILE_ARTIFACTS_DIRECTORY,
    state_root: Path = Path("native-profile-state"),
) -> tuple[NativeProfileRow, ...]:
    """Return one immutable probe row for every centrally configured profile.

    The function is deliberately a pure projection: it creates neither an
    agent state directory nor an artifact. The native execution entrypoint
    supplies the caller-selected artifact root and performs those effects.
    """
    rows: list[NativeProfileRow] = []
    for target, profiles in AGENT_PROFILES.items():
        for profile, configuration in profiles.items():
            identifier = f"{target.value}-{profile.value}"
            row_state = state_root / identifier
            row_artifacts = artifact_root / identifier
            definition_path = row_artifacts / _definition_filename(target)
            rows.append(
                NativeProfileRow(
                    identifier=identifier,
                    target=target,
                    profile=profile,
                    configuration=configuration,
                    state_root=row_state,
                    definition_path=definition_path,
                    native_definition_path=_native_definition_path(
                        row_state, target, definition_path.name
                    ),
                    loading_path=row_artifacts / "loading.json",
                    result_path=row_artifacts / "result.json",
                    launch_commands=(_native_launch_command(target),),
                )
            )
    return tuple(rows)


def _definition_filename(target: Target) -> str:
    if target is Target.CLAUDE:
        return "profile-probe.md"
    return "profile-probe.toml"


def _native_definition_path(state_root: Path, target: Target, name: str) -> Path:
    agent_home = "claude" if target is Target.CLAUDE else "codex"
    return state_root / agent_home / "agents" / name


def _native_launch_command(target: Target) -> tuple[str, ...]:
    if target is Target.CLAUDE:
        return (
            _CLAUDE_EXECUTABLE,
            "-p",
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--forward-subagent-text",
        )
    return (
        _CODEX_EXECUTABLE,
        "exec",
        "--json",
        "--strict-config",
        "--skip-git-repo-check",
    )


@dataclass(frozen=True)
class NativeProfileExecutionObservation:
    """Retained paths and terminal process observations for one probe row."""

    row: NativeProfileRow
    install_exit_code: int | None
    launch_exit_code: int | None
    terminal_condition: str | None


class NativeCommandRunner(Protocol):
    """Execute one native parent session with explicit process boundaries."""

    def __call__(
        self, argv: Sequence[str], cwd: Path, environment: Mapping[str, str]
    ) -> subprocess.CompletedProcess[str]: ...


class EvidenceSanitizer(Protocol):
    """Remove credential material before retaining any native observation."""

    def __call__(self, text: str) -> str: ...


@dataclass(frozen=True)
class NativeExecutionRunners:
    """Native operations supplied within the harness's authentication interval."""

    parent: NativeCommandRunner
    thread: NativeThreadReader
    sanitize: EvidenceSanitizer


def run_native_profile_row(
    row: NativeProfileRow,
    *,
    checkout: Path,
    environment: Mapping[str, str],
    runners: NativeExecutionRunners,
) -> NativeProfileExecutionObservation:
    """Capture one child invocation from already installed disposable state."""
    native_environment = dict(environment)
    command = _launch_command(row, checkout)
    result = runners.parent(command, checkout, native_environment)
    sanitized_stdout = runners.sanitize(result.stdout)
    sanitized_stderr = runners.sanitize(result.stderr)
    child_observation: dict[str, object] = {}
    terminal_condition: str | None
    if result.returncode != 0:
        terminal_condition = f"native parent session exited {result.returncode}"
    elif isinstance(row.configuration, CodexConfiguration):
        evidence = collect_native_child_evidence(
            sanitized_stdout,
            f"profile-probe-{row.identifier}",
            row.configuration,
            reader=runners.thread,
            cwd=checkout,
            environment=native_environment,
        )
        child_observation = json.loads(runners.sanitize(json.dumps(asdict(evidence))))
        terminal_condition = evidence.terminal_condition
        _write_json(
            row.loading_path,
            {
                "identifier": row.identifier,
                "native_definition_path": str(row.native_definition_path),
                "materialized": True,
                "discovered": evidence.thread is not None
                and evidence.thread.get("agentRole")
                == f"profile-probe-{row.identifier}",
                "evidence": str(row.result_path),
            },
        )
    else:
        child_observation = _child_observation(sanitized_stdout)
        terminal_condition = _unusable_child_condition(child_observation)
    _write_json(
        row.result_path,
        {
            "identifier": row.identifier,
            "parent_command": result.args
            if isinstance(result.args, str)
            else list(result.args),
            "exit_code": result.returncode,
            "stdout": sanitized_stdout,
            "stderr": sanitized_stderr,
            "child_observation": child_observation,
            "configuration_identity_evidence": (
                "native-child-thread-read"
                if row.target is Target.CODEX
                else "definition-and-forwarded-stream"
            ),
            "terminal_condition": terminal_condition,
        },
    )
    return NativeProfileExecutionObservation(
        row=row,
        install_exit_code=0,
        launch_exit_code=result.returncode,
        terminal_condition=terminal_condition,
    )


def materialize_native_profile(row: NativeProfileRow) -> None:
    definition = _render_definition(row)
    row.definition_path.parent.mkdir(parents=True, exist_ok=True)
    row.definition_path.write_text(definition, encoding="utf-8")
    row.native_definition_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(row.definition_path, row.native_definition_path)

    _write_json(
        row.loading_path,
        {
            "identifier": row.identifier,
            "native_definition_path": str(row.native_definition_path),
            "materialized": True,
            "discovered": None,
        },
    )


def _render_definition(row: NativeProfileRow) -> str:
    values = native_configuration_values(row.configuration)
    child_prompt = _child_prompt(row.identifier)
    if row.target is Target.CLAUDE:
        fields = ("name", "description", *values)
        frontmatter = {
            "name": f"profile-probe-{row.identifier}",
            "description": "One native profile-execution evidence child.",
            **values,
        }
        return (
            "---\n"
            + "\n".join(
                f"{field}: {json.dumps(frontmatter[field])}" for field in fields
            )
            + f"\n---\n{child_prompt}\n"
        )
    return "\n".join(
        (
            f"name = {json.dumps(f'profile-probe-{row.identifier}')}",
            'description = "One native profile-execution evidence child."',
            *(f"{name} = {json.dumps(value)}" for name, value in values.items()),
            f"developer_instructions = {json.dumps(child_prompt)}",
            "",
        )
    )


def _launch_command(row: NativeProfileRow, checkout: Path) -> tuple[str, ...]:
    prompt = _parent_prompt(row)
    if row.target is Target.CLAUDE:
        return (row.launch_commands[0][0], "-p", prompt, *row.launch_commands[0][2:])
    return (*row.launch_commands[0], "-C", str(checkout), prompt)


def _parent_prompt(row: NativeProfileRow) -> str:
    isolation = (
        ' Explicitly set fork_turns to "none".' if row.target is Target.CODEX else ""
    )
    return (
        "Use the native subagent tool exactly once to launch "
        f"`profile-probe-{row.identifier}` with the prompt `Complete`."
        f"{isolation} Wait for its result. Do not launch another child."
    )


def _child_prompt(identifier: str) -> str:
    return (
        f"This is native profile-execution evidence for {identifier}. "
        "Return one concise completion message."
    )


def _child_observation(stream: str) -> dict[str, object]:
    events = tuple(_json_lines(stream))
    parent_ids = sorted(
        {
            value
            for event in events
            for value in _field_values(event, "parent_tool_use_id")
            if isinstance(value, str)
        }
    )
    return {"forwarded_parent_tool_use_ids": parent_ids}


def _unusable_child_condition(observation: Mapping[str, object]) -> str | None:
    parent_ids = observation["forwarded_parent_tool_use_ids"]
    if isinstance(parent_ids, list) and len(parent_ids) == 1:
        return None
    return (
        "forwarded native child evidence did not identify exactly one parent tool use"
    )


def _json_lines(stream: str) -> Iterable[dict[str, object]]:
    for line in stream.splitlines():
        try:
            document = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(document, dict):
            yield document


def _field_values(value: object, field: str) -> Iterable[object]:
    if isinstance(value, dict):
        for name, nested in value.items():
            if name == field:
                yield nested
            yield from _field_values(nested, field)
    elif isinstance(value, list):
        for nested in value:
            yield from _field_values(nested, field)


def _write_json(path: Path, document: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def record_native_profile_failure(
    row: NativeProfileRow, condition: str, *, install_exit_code: int | None = None
) -> NativeProfileExecutionObservation:
    """Retain a harness failure without discarding any captured child evidence."""
    document: dict[str, object] = (
        json.loads(row.result_path.read_text(encoding="utf-8"))
        if row.result_path.exists()
        else {"identifier": row.identifier}
    )
    document["terminal_condition"] = condition
    document["install_exit_code"] = install_exit_code
    _write_json(row.result_path, document)
    launch_exit_code = document.get("exit_code")
    return NativeProfileExecutionObservation(
        row,
        install_exit_code,
        launch_exit_code if isinstance(launch_exit_code, int) else None,
        condition,
    )
