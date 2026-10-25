"""Harness for review-run changeset evidence.

Builds synthetic repositories whose branch carries generated extents, region-bounded
outputs, renames, or large unread sets, drives ``review_run.py`` through
``start``, ``append-scope``, and ``finish`` against the fake ``spx`` journal that
``reviewing_changes`` provides, and returns what the runner wrote. The harness extracts
data; every predicate over it lives in the linked test files.

The runner's field names for extents, renames, and skips are the runner's own, so the
extraction helpers here are structure-agnostic: ``nodes_mentioning`` returns the smallest
JSON objects whose serialization carries every given token.
"""

from __future__ import annotations

import enum
import json
import pathlib
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from outcomeeng_testing.generators.reviewing_changes_runs import (
    ExtentRelation,
    RegionRelation,
    RenameCase,
)
from outcomeeng_testing.harnesses.journal_projection import (
    load_journal_projection_module,
)
from outcomeeng_testing.harnesses.reviewing_changes import (
    REVIEW_RUN_SCRIPT,
    load_compute_diff_module,
    load_review_run_module,
    read_fake_journal,
    run_git,
    run_script,
    runner_env,
)

jp = load_journal_projection_module()
review_run = load_review_run_module()
compute_diff = load_compute_diff_module()
# The start payload's keys that name this run's own paths and tokens, which differ between
# any two runs; the remaining keys carry the run state under comparison.
START_PAYLOAD_RUN_KEYS = (
    review_run.START_RUN_TOKEN,
    review_run.START_STATE_PATH,
    review_run.START_DIFF_PATH,
    review_run.START_MANIFEST_PATH,
    review_run.CHANGED_FILES_KEY,
)
EDIT_MARKER_COMMENT = "# declaration edited"
BASE_BRANCH = "main"
FEATURE_BRANCH = "feature/x"
CONTENT_LINE_COUNT = 24
EDITED_LINE_INDEX = 3


def file_content(path: str, *, edited: bool = False) -> str:
    """Return deterministic multi-line content for ``path``; ``edited`` changes one line."""
    lines = [f"{path} line {index}\n" for index in range(CONTENT_LINE_COUNT)]
    if edited:
        lines[EDITED_LINE_INDEX] = f"{path} edited line {EDITED_LINE_INDEX}\n"
    return "".join(lines)


def _toml_strings(values: Iterable[str]) -> str:
    return "[" + ", ".join(json.dumps(value) for value in values) + "]"


def render_generated_sources(
    relations: Sequence[ExtentRelation | RegionRelation],
) -> str:
    """Render relations as the ``[[relation]]`` tables of a generated-sources declaration."""
    tables: list[str] = []
    for relation in relations:
        if isinstance(relation, RegionRelation):
            output = (
                f"{{ file = {json.dumps(relation.file)}, "
                f"begin = {json.dumps(relation.begin)}, "
                f"end = {json.dumps(relation.end)} }}"
            )
        else:
            output = json.dumps(relation.output_pattern)
        tables.append(
            "[[relation]]\n"
            f"outputs = [{output}]\n"
            f"sources = {_toml_strings(relation.sources)}\n"
            f"generator = {_toml_strings(relation.generator)}\n"
            f"regenerate = {json.dumps(relation.regenerate)}\n"
        )
    return "\n".join(tables)


def _write(repo: pathlib.Path, path: str, content: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def build_changeset_repo(
    repo: pathlib.Path,
    *,
    declaration: str | None,
    changed_paths: Iterable[str],
    unchanged_paths: Iterable[str] = (),
    rename: RenameCase | None = None,
    head_declaration: str | None = None,
    working_tree_declaration: str | None = None,
) -> str:
    """Create a repository whose feature branch adds ``changed_paths`` and applies ``rename``.

    The base commit holds the declaration (when given), ``unchanged_paths``, and the
    rename's old path, so none of them is part of the changeset. The feature branch adds
    each changed path with generated content and renames the old path to the new one,
    editing its content when the case says so. ``head_declaration`` replaces the
    declaration in the branch commit; ``working_tree_declaration`` replaces it in the
    working tree after that commit. Returns the base ref name.
    """
    repo.mkdir(parents=True, exist_ok=True)
    run_git("init", "-q", "-b", BASE_BRANCH, str(repo), cwd=pathlib.Path.cwd())
    run_git("config", "commit.gpgsign", "false", cwd=repo)
    if declaration is not None:
        _write(repo, str(compute_diff.GENERATED_SOURCES_PATH), declaration)
    for path in unchanged_paths:
        _write(repo, path, file_content(path))
    if rename is not None:
        _write(repo, rename.old_path, file_content(rename.old_path))
    _write(repo, "seed.txt", file_content("seed.txt"))
    run_git("add", "-A", cwd=repo)
    run_git("commit", "-q", "-m", "base", cwd=repo)
    run_git("switch", "-q", "-c", FEATURE_BRANCH, cwd=repo)
    if rename is not None:
        (repo / rename.new_path).parent.mkdir(parents=True, exist_ok=True)
        run_git("mv", rename.old_path, rename.new_path, cwd=repo)
        if rename.content_changed:
            _write(repo, rename.new_path, file_content(rename.old_path, edited=True))
    for path in changed_paths:
        _write(repo, path, file_content(path))
    if head_declaration is not None:
        _write(repo, str(compute_diff.GENERATED_SOURCES_PATH), head_declaration)
    run_git("add", "-A", cwd=repo)
    run_git("commit", "-q", "-m", "branch", cwd=repo)
    if working_tree_declaration is not None:
        _write(repo, str(compute_diff.GENERATED_SOURCES_PATH), working_tree_declaration)
    return BASE_BRANCH


def edited_declaration(declaration: str) -> str:
    """Return ``declaration`` with a trailing comment, a text that differs from it."""
    return f"{declaration}\n{EDIT_MARKER_COMMENT}\n"


class UnreadChannel(enum.Enum):
    """How the unread set reaches ``finish``."""

    ARGUMENTS = "arguments"
    FILE = "file"


@dataclass(frozen=True)
class StartedRun:
    """A started run: the start payload and the manifest and state it wrote."""

    start_payload: dict[str, Any]
    manifest: dict[str, Any]
    run_state: dict[str, Any]
    env: dict[str, str]
    journal_path: pathlib.Path
    repo: pathlib.Path
    scratch: pathlib.Path


@dataclass(frozen=True)
class FinishedRun:
    """A finished run: the finish result and the journal the fake ``spx`` recorded."""

    started: StartedRun
    finished: subprocess.CompletedProcess[str]
    events: list[dict[str, Any]]
    sealed: bool


def start_changeset_review(
    scratch: pathlib.Path, repo: pathlib.Path, base_ref: str
) -> StartedRun:
    """Run ``review_run.py start`` in ``repo`` under a fresh ``scratch`` directory."""
    scratch.mkdir(parents=True)
    env, journal_path = runner_env(scratch, repo, base_ref)
    started = run_script(REVIEW_RUN_SCRIPT, "start", env=env, cwd=repo)
    if started.returncode != 0:
        raise RuntimeError(f"review_run.py start failed: {started.stderr}")
    payload = json.loads(started.stdout)
    manifest = json.loads(
        pathlib.Path(payload[review_run.START_MANIFEST_PATH]).read_text("utf-8")
    )
    run_state = json.loads(
        pathlib.Path(payload[review_run.START_STATE_PATH]).read_text("utf-8")
    )
    return StartedRun(payload, manifest, run_state, env, journal_path, repo, scratch)


def finish_changeset_review(
    started: StartedRun,
    *,
    scope: Sequence[str] = (),
    unread: Sequence[str] = (),
    channel: UnreadChannel = UnreadChannel.ARGUMENTS,
) -> FinishedRun:
    """Append scope for ``scope``, then run ``finish`` with ``unread`` over ``channel``."""
    state_path = started.start_payload[review_run.START_STATE_PATH]
    for unit in scope:
        scoped = run_script(
            REVIEW_RUN_SCRIPT,
            "append-scope",
            "--state",
            state_path,
            unit,
            env=started.env,
            cwd=started.repo,
        )
        if scoped.returncode != 0:
            raise RuntimeError(f"review_run.py append-scope failed: {scoped.stderr}")
    unread_args: list[str] = []
    if channel is UnreadChannel.ARGUMENTS:
        for path in unread:
            unread_args.extend(["--unread", path])
    elif unread:
        listing = started.scratch / "unread-paths.txt"
        listing.write_text("".join(f"{path}\n" for path in unread), encoding="utf-8")
        unread_args.extend(["--unread-file", str(listing)])
    finished = run_script(
        REVIEW_RUN_SCRIPT,
        "finish",
        "--state",
        state_path,
        *unread_args,
        env=started.env,
        cwd=started.repo,
    )
    journal = read_fake_journal(started.journal_path)
    return FinishedRun(started, finished, journal.events, journal.sealed)


def events_of_type(
    events: Iterable[Mapping[str, Any]], event_type: str
) -> list[Mapping[str, Any]]:
    """Return the events whose ``type`` is ``event_type``, in order."""
    return [event for event in events if event.get(jp.EVENT_TYPE_FIELD) == event_type]


def without_keys(document: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    """Return ``document`` without its top-level ``keys``."""
    return {name: value for name, value in document.items() if name not in keys}


def run_state_listing(started: StartedRun) -> dict[str, Any]:
    """Return the start payload without the keys that name the run's own paths and tokens."""
    return without_keys(started.start_payload, *START_PAYLOAD_RUN_KEYS)


def run_completed_event(events: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Return the run-completed event of a journal."""
    return events_of_type(events, jp.RUN_COMPLETED)[-1]


def completed_unread(completed: Mapping[str, Any]) -> list[str]:
    """Return the files a run-completed event records as unread."""
    review = completed[jp.EVENT_DATA_FIELD][review_run.REVIEW_KEY]
    return list(review.get(review_run.REVIEW_UNREAD, []))


def scope_advanced_units(events: Iterable[Mapping[str, Any]]) -> list[str]:
    """Return the unit of each scope-advanced event, in order."""
    return [
        event[jp.EVENT_DATA_FIELD]["unit"]
        for event in events_of_type(events, jp.SCOPE_ADVANCED)
    ]


def _objects(document: Any) -> Iterable[dict[str, Any]]:
    if isinstance(document, dict):
        yield document
        for value in document.values():
            yield from _objects(value)
    elif isinstance(document, list):
        for item in document:
            yield from _objects(item)


def nodes_mentioning(document: Any, *tokens: str) -> list[dict[str, Any]]:
    """Return the smallest JSON objects in ``document`` whose text carries every token.

    An object is smallest when no object nested inside it carries every token too.
    """
    matching = [
        node
        for node in _objects(document)
        if all(token in json.dumps(node) for token in tokens)
    ]
    return [
        node
        for node in matching
        if not any(
            child is not node and all(token in json.dumps(child) for token in tokens)
            for child in _objects(list(node.values()))
        )
    ]
