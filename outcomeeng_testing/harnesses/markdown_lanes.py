"""Declared Markdown verification lanes and the commands they execute.

Backs the selected-gate lane-coverage mapping. The harness reads the lanes the
repository's merge overlay declares, enumerates the repository's tracked
Markdown paths, and runs each declared lane command through the real `just`
command runner, the real `justfile`, and the real validation CLI, so the
observation is what the lane actually executes rather than what a reader of the
recipe text infers.

Exception case: `/test` Stage 5, Observability. A real gate tool such as `uv`,
`dprint`, `spx`, or `actionlint` performs its check and hides the command it was
asked to run; several of those checks also rewrite the generated plugin trees.
Every external tool a gate step or a lane command starts with is therefore
replaced, on `PATH` only, by a recording executable that appends its argv to a
record log and exits 0, so every later command in the lane still runs. The
`just` command runner and every other executable stay real, and a recorded
command that runs the validation CLI module — through `uv run python -m` or a
directly named interpreter — is forwarded to that CLI after it is recorded, so
the steps the CLI runs are recorded in turn.
The harness exposes the recorded commands as observations and decides nothing.
"""

from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng import validation as validation_package
from outcomeeng.validation import PREFLIGHT_STEPS, TEST_STEPS, VALIDATION_STEPS

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[2]
MERGE_OVERLAY_PATH: Final = Path("spx") / "local" / "merging.md"
LANE_SECTION_HEADING: Final = "## Deterministic verification commands"
MARKDOWN_PATHSPEC: Final = "*.md"

# `uv run <command>` runs <command> inside the project environment, so a lane
# that runs <command> directly runs the same check as a gate step that prefixes
# it with `uv run`.
UV_RUN_PREFIX: Final = ("uv", "run")

COMMAND_RUNNER: Final = "just"
# An interpreter flag naming the module to run; a recorded command that runs the
# validation CLI module this way is forwarded to that CLI.
PYTHON_MODULE_FLAG: Final = "-m"
LANE_TIMEOUT_SECONDS: Final = 300.0
KILL_GRACE_SECONDS: Final = 5.0
RECORD_LOG_VARIABLE: Final = "MARKDOWN_LANE_RECORD_LOG"
_BULLET_PREFIX: Final = "- "
_SECTION_PREFIX: Final = "## "
_LABEL_SEPARATOR: Final = ": "
_CODE_SPAN: Final = "`"

_RECORDING_TOOL_TEMPLATE: Final = """#!{interpreter}
import json
import os
import sys

TOOL = {tool!r}
FORWARDED_MODULE = {forwarded_module!r}
MODULE_FLAG = {module_flag!r}

arguments = sys.argv[1:]
with open(os.environ[{record_variable!r}], "a", encoding="utf-8") as record:
    record.write(json.dumps([TOOL, *arguments]) + "\\n")

for position in range(len(arguments) - 1):
    if arguments[position : position + 2] == [MODULE_FLAG, FORWARDED_MODULE]:
        os.execv(
            sys.executable,
            [sys.executable, MODULE_FLAG, FORWARDED_MODULE, *arguments[position + 2 :]],
        )
"""


@dataclass(frozen=True)
class DeclaredLane:
    """One verification lane the merge overlay declares."""

    label: str
    commands: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class LaneCommandRun:
    """What one declared lane command executed when it ran."""

    lane: DeclaredLane
    command: tuple[str, ...]
    exit_code: int
    executed: tuple[tuple[str, ...], ...]
    output_path: Path


def declared_lanes(repository: Path = REPOSITORY_ROOT) -> tuple[DeclaredLane, ...]:
    """Return every lane bullet the overlay's verification-commands section declares."""

    lines = (repository / MERGE_OVERLAY_PATH).read_text(encoding="utf-8").splitlines()
    start = lines.index(LANE_SECTION_HEADING) + 1
    lanes: list[DeclaredLane] = []
    for line in lines[start:]:
        if line.startswith(_SECTION_PREFIX):
            break
        if line.startswith(_BULLET_PREFIX):
            lanes.append(_lane_from_bullet(line.removeprefix(_BULLET_PREFIX)))
    return tuple(lanes)


def tracked_markdown_paths(repository: Path = REPOSITORY_ROOT) -> tuple[str, ...]:
    """Return every Markdown path Git tracks in the repository."""

    completed = subprocess.run(
        ("git", "ls-files", "-z", "--", MARKDOWN_PATHSPEC),
        cwd=repository,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
        timeout=LANE_TIMEOUT_SECONDS,
    )
    return tuple(sorted(path for path in completed.stdout.split("\0") if path))


def project_command(argv: Sequence[str]) -> tuple[str, ...]:
    """Return a command in the form it takes inside the project environment."""

    command = tuple(argv)
    if command[: len(UV_RUN_PREFIX)] == UV_RUN_PREFIX:
        return command[len(UV_RUN_PREFIX) :]
    return command


def run_lanes(
    lanes: Iterable[DeclaredLane],
    scratch: Path,
    repository: Path = REPOSITORY_ROOT,
) -> tuple[LaneCommandRun, ...]:
    """Run every command of every lane and record the external commands it executed."""

    lane_tuple = tuple(lanes)
    tools_directory = scratch / "recording-tools"
    temporary_directory = scratch / "tmp"
    tools_directory.mkdir()
    temporary_directory.mkdir()
    for tool in _recorded_tools(lane_tuple):
        _write_recording_tool(tools_directory / tool, tool)
    runs: list[LaneCommandRun] = []
    for lane_index, lane in enumerate(lane_tuple):
        for command_index, command in enumerate(lane.commands):
            record_path = scratch / f"record-{lane_index}-{command_index}.jsonl"
            output_path = scratch / f"output-{lane_index}-{command_index}.log"
            record_path.touch()
            environment = {
                **os.environ,
                "PATH": os.pathsep.join(
                    (str(tools_directory), os.environ.get("PATH", ""))
                ),
                "TMPDIR": str(temporary_directory),
                "PYTHONDONTWRITEBYTECODE": "1",
                RECORD_LOG_VARIABLE: str(record_path),
            }
            exit_code = _run_bounded(command, repository, environment, output_path)
            runs.append(
                LaneCommandRun(
                    lane=lane,
                    command=command,
                    exit_code=exit_code,
                    executed=_recorded_commands(record_path),
                    output_path=output_path,
                )
            )
    return tuple(runs)


def _lane_from_bullet(text: str) -> DeclaredLane:
    label_end = _label_end(text)
    label = text[:label_end]
    body = text[label_end + len(_LABEL_SEPARATOR) :]
    spans = body.split(_CODE_SPAN)[1::2]
    return DeclaredLane(
        label=label,
        commands=tuple(tuple(shlex.split(span)) for span in spans),
    )


def _label_end(text: str) -> int:
    inside_code = False
    for position, character in enumerate(text):
        if character == _CODE_SPAN:
            inside_code = not inside_code
        elif not inside_code and text.startswith(_LABEL_SEPARATOR, position):
            return position
    raise ValueError(f"lane bullet declares no label: {text}")


def _recorded_tools(lanes: Sequence[DeclaredLane]) -> tuple[str, ...]:
    step_tools = {
        step.argv[0] for step in (*PREFLIGHT_STEPS, *VALIDATION_STEPS, *TEST_STEPS)
    }
    lane_tools = {command[0] for lane in lanes for command in lane.commands if command}
    return tuple(sorted((step_tools | lane_tools) - {COMMAND_RUNNER}))


def _write_recording_tool(path: Path, tool: str) -> None:
    path.write_text(
        _RECORDING_TOOL_TEMPLATE.format(
            interpreter=sys.executable,
            tool=tool,
            forwarded_module=validation_package.__name__,
            module_flag=PYTHON_MODULE_FLAG,
            record_variable=RECORD_LOG_VARIABLE,
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


def _run_bounded(
    command: Sequence[str],
    repository: Path,
    environment: dict[str, str],
    output_path: Path,
) -> int:
    with output_path.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(  # noqa: S603 - argv comes from the declared lane
            tuple(command),
            cwd=repository,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            return process.wait(timeout=LANE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=KILL_GRACE_SECONDS)
            raise


def _recorded_commands(record_path: Path) -> tuple[tuple[str, ...], ...]:
    return tuple(
        tuple(json.loads(line))
        for line in record_path.read_text(encoding="utf-8").splitlines()
        if line
    )
