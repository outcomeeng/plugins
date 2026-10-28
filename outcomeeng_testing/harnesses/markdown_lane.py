"""Declared Markdown lanes and the replayable property over their coverage.

The lane declaration is `spx/local/merging.md`, section "Deterministic
verification commands": each bullet whose scope names Markdown declares one
lane, with the commands it runs. A `just` command expands to the command
lines of its recipe in the `justfile`. The harness returns those declared
command lines as observations; the linked test decides which selected step a
declared line runs.
"""

from __future__ import annotations

import io
import re
import shlex
from functools import cache
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng.distribution.instruction_block import JUSTFILE_NAME
from outcomeeng.validation import SUMMARY_KEY_LABEL, VALIDATION_ENTRY_COMMAND
from outcomeeng.validation.__main__ import main as run_validation_entry
from outcomeeng.validation.infrastructure_index import PRODUCT_TREE_ROOT
from outcomeeng.validation.selected_gate import RECIPE_MARKDOWN_LANE
from outcomeeng_testing.generators.markdown_lane import markdown_lane_changesets
from outcomeeng_testing.harnesses.gate import (
    RecordingSpawner,
    summary_path_from_output,
    summary_steps,
    read_summary,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
MERGING_OVERLAY_PATH: Final = REPO_ROOT / "spx" / "local" / "merging.md"
JUSTFILE_PATH: Final = REPO_ROOT / JUSTFILE_NAME
LANES_SECTION_HEADING: Final = "## Deterministic verification commands"
SECTION_HEADING_PREFIX: Final = "## "
BULLET_PREFIX: Final = "- "
SCOPE_SEPARATOR: Final = ": "
MARKDOWN_SCOPE_WORD: Final = "Markdown"
CODE_SPAN: Final = re.compile(r"`([^`]+)`")
JUST_COMMAND: Final = "just"
LAUNCHER: Final = ("uv", "run")
DIRECTORY_SUFFIX: Final = "/"
ROOT_PREFIX: Final = ""

MARKDOWN_LANE_PROPERTY_SEED: Final = 20261028
MARKDOWN_LANE_PROPERTY_EXAMPLES: Final = 60
PROPERTY_REPLAY_COMMAND: Final = "just test"


class LaneDeclarationError(RuntimeError):
    """The lane declaration or the recipe it names cannot be read."""


@dataclass(frozen=True)
class MarkdownLane:
    """One declared Markdown lane: its scoped prefixes and the lines it runs."""

    scope: str
    path_prefixes: tuple[str, ...]
    command_lines: tuple[tuple[str, ...], ...]


def without_launcher(argv: tuple[str, ...]) -> tuple[str, ...]:
    """The command tokens of ``argv`` after a leading `uv run` launcher."""

    if argv[: len(LAUNCHER)] == LAUNCHER:
        return argv[len(LAUNCHER) :]
    return argv


@dataclass(frozen=True)
class LaneRunObservation:
    """What one run of the Markdown lane through the validation entry point spawned."""

    command_lines: tuple[tuple[str, ...], ...]
    step_labels: tuple[str, ...]


@cache
def markdown_lane_run() -> LaneRunObservation:
    """Run the Markdown lane entry point against a recording spawner.

    The observation is the command lines the lane spawns and the step labels its
    summary records, read from the run rather than from the selector's tables.
    """

    spawner = RecordingSpawner(exit_codes=())
    sink = io.StringIO()
    run_validation_entry(
        [RECIPE_MARKDOWN_LANE], spawner=spawner, sink=sink, repo=REPO_ROOT
    )
    summary = read_summary(Path(summary_path_from_output(sink.getvalue())))
    return LaneRunObservation(
        command_lines=tuple(without_launcher(call) for call in spawner.spawn_calls),
        step_labels=tuple(
            str(record[SUMMARY_KEY_LABEL]) for record in summary_steps(summary)
        ),
    )


def _expand_validation_recipe(
    line: tuple[str, ...],
) -> tuple[tuple[str, ...], ...]:
    """The command lines a line runs; the Markdown lane recipe runs the lines its run spawns."""

    if line == (*VALIDATION_ENTRY_COMMAND, RECIPE_MARKDOWN_LANE):
        return markdown_lane_run().command_lines
    return (line,)


def _recipe_lines(recipe: str) -> tuple[tuple[str, ...], ...]:
    header = re.compile(rf"^{re.escape(recipe)}(\s[^:]*)?:\s*$")
    lines = JUSTFILE_PATH.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not header.match(line):
            continue
        body: list[tuple[str, ...]] = []
        for candidate in lines[index + 1 :]:
            if candidate and not candidate[0].isspace():
                break
            stripped = candidate.strip().lstrip("@-")
            if stripped and not stripped.startswith("#"):
                body.extend(
                    _expand_validation_recipe(
                        without_launcher(tuple(shlex.split(stripped)))
                    )
                )
        return tuple(body)
    raise LaneDeclarationError(f"recipe {recipe!r} is absent from {JUSTFILE_PATH}")


def _command_lines(command: str) -> tuple[tuple[str, ...], ...]:
    tokens = tuple(shlex.split(command))
    if tokens[0] == JUST_COMMAND:
        return tuple(line for recipe in tokens[1:2] for line in _recipe_lines(recipe))
    return (without_launcher(tokens),)


def markdown_lanes() -> tuple[MarkdownLane, ...]:
    """Every lane `spx/local/merging.md` declares for Markdown paths."""

    lines = MERGING_OVERLAY_PATH.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index(LANES_SECTION_HEADING)
    except ValueError as error:
        raise LaneDeclarationError(
            f"{LANES_SECTION_HEADING!r} is absent from {MERGING_OVERLAY_PATH}"
        ) from error
    lanes: list[MarkdownLane] = []
    for line in lines[start + 1 :]:
        if line.startswith(SECTION_HEADING_PREFIX):
            break
        if not line.startswith(BULLET_PREFIX):
            continue
        scope, _, commands = line[len(BULLET_PREFIX) :].partition(SCOPE_SEPARATOR)
        if MARKDOWN_SCOPE_WORD not in scope:
            continue
        lanes.append(
            MarkdownLane(
                scope=scope,
                path_prefixes=tuple(
                    span
                    for span in CODE_SPAN.findall(scope)
                    if span.endswith(DIRECTORY_SUFFIX)
                ),
                command_lines=tuple(
                    line
                    for command in CODE_SPAN.findall(commands)
                    for line in _command_lines(command)
                ),
            )
        )
    if not lanes:
        raise LaneDeclarationError(
            f"no Markdown lane is declared in {MERGING_OVERLAY_PATH}"
        )
    return tuple(lanes)


def declared_lane_command_lines() -> tuple[tuple[str, ...], ...]:
    """Every command line any declared Markdown lane runs."""

    return tuple(line for lane in markdown_lanes() for line in lane.command_lines)


def lane_scope_prefixes() -> tuple[str, ...]:
    """Directory prefixes the lanes scope, the product tree and the repository root among them.

    The spec-only lane covers the product tree and Markdown at the repository
    root; the other lane names its prefixes in its declaration.
    """

    declared = tuple(
        prefix for lane in markdown_lanes() for prefix in lane.path_prefixes
    )
    return (*declared, PRODUCT_TREE_ROOT, ROOT_PREFIX)


def markdown_lane_property(
    test_func: Callable[[list[str]], None],
) -> Callable[[], None]:
    """Run a property over Markdown-lane changesets with replayable failures."""

    configured = seed(MARKDOWN_LANE_PROPERTY_SEED)(
        settings(max_examples=MARKDOWN_LANE_PROPERTY_EXAMPLES, deadline=None)(
            given(paths=markdown_lane_changesets(lane_scope_prefixes()))(test_func)
        )
    )
    source = Path(test_func.__code__.co_filename).resolve()
    replay_path = (
        f"{PROPERTY_REPLAY_COMMAND} {source.relative_to(REPO_ROOT).as_posix()}"
        f"::test{test_func.__name__}"
    )

    def wrapper() -> None:
        run_replayable_property(
            configured,
            seed_value=MARKDOWN_LANE_PROPERTY_SEED,
            replay_path=replay_path,
        )

    return wrapper
