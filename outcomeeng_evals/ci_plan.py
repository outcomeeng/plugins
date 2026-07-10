"""CI planning for eval suites."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from outcomeeng_evals.definition import CiPolicy, EVAL_TOML_FILENAME, load_definition


ROOT_INSTRUCTION_PATHS: Final = ("AGENTS.md", "CLAUDE.md")
UNIVERSAL_OWNED_PATHS = (
    *ROOT_INSTRUCTION_PATHS,
    "outcomeeng_evals/**",
    "outcomeeng_testing/evals/**",
    "outcomeeng_testing/generators/**",
    "outcomeeng_testing/harnesses/**",
)
CHANGED_PATHS_FILE_HELP = (
    "File containing git diff --name-status rows, or one repository-relative "
    "path per line. Mixed formats are rejected."
)
RENAMED_GIT_STATUS_PREFIX = "R"
COPIED_GIT_STATUS_PREFIX = "C"
SIMPLE_GIT_STATUS_CODES: Final = frozenset(("A", "B", "D", "M", "T", "U", "X"))


class CiMode(StrEnum):
    """CI execution mode for eval selection."""

    PR = "pr"
    FULL = "full"


@dataclass(frozen=True)
class EvalPlanItem:
    """One eval suite invocation selected for CI."""

    eval_toml: Path
    plugin_dir: Path
    case_ids: tuple[str, ...]


def build_ci_plan(
    root: Path,
    *,
    mode: CiMode,
    changed_paths: tuple[str, ...] = (),
    default_plugin_dir: Path | None = None,
) -> list[EvalPlanItem]:
    """Select eval suites and cases for CI."""
    discovered = sorted(root.rglob(EVAL_TOML_FILENAME))
    items: list[EvalPlanItem] = []
    for eval_toml in discovered:
        definition = load_definition(eval_toml)
        if definition.ci_policy is CiPolicy.MANUAL:
            continue
        plugin_dir = definition.plugin_dir or default_plugin_dir
        if plugin_dir is None:
            msg = f"{eval_toml}: plugin_dir is required in eval.toml or --default-plugin-dir"
            raise ValueError(msg)
        if mode is CiMode.FULL:
            items.append(
                EvalPlanItem(eval_toml=eval_toml, plugin_dir=plugin_dir, case_ids=())
            )
            continue
        selection = _pr_selection(
            eval_toml=eval_toml,
            owned_paths=definition.owned_paths,
            smoke_case_ids=definition.smoke_case_ids,
            changed_paths=changed_paths,
        )
        if selection is not None:
            items.append(
                EvalPlanItem(
                    eval_toml=eval_toml,
                    plugin_dir=plugin_dir,
                    case_ids=selection,
                )
            )
    return items


def plan_to_jsonable(items: list[EvalPlanItem]) -> list[dict[str, object]]:
    """Convert a plan to a JSON-serializable structure."""
    return [
        {
            "eval_toml": str(item.eval_toml),
            "plugin_dir": str(item.plugin_dir),
            "case_ids": list(item.case_ids),
        }
        for item in items
    ]


def read_changed_paths_file(path: Path | None) -> tuple[str, ...]:
    """Read paths from git name-status rows or plain repository-relative paths."""

    if path is None:
        return ()
    lines = tuple(
        line for line in path.read_text(encoding="utf-8").splitlines() if line
    )
    if not lines:
        return ()
    has_tabbed_rows = any("\t" in line for line in lines)
    if not has_tabbed_rows:
        return lines
    return tuple(
        changed_path
        for line in lines
        for changed_path in _changed_paths_from_name_status_line(line)
    )


def _changed_paths_from_name_status_line(line: str) -> tuple[str, ...]:
    if "\t" not in line:
        msg = f"changed paths file mixes git name-status rows with plain path row: {line!r}"
        raise ValueError(msg)
    parts = line.split("\t")
    status = parts[0]
    if not _is_git_name_status(status):
        msg = f"changed paths file tabbed row is not git name-status: {line!r}"
        raise ValueError(msg)
    if status.startswith((RENAMED_GIT_STATUS_PREFIX, COPIED_GIT_STATUS_PREFIX)):
        if len(parts) != 3:
            msg = f"changed paths file rename/copy row must contain status, old path, and new path: {line!r}"
            raise ValueError(msg)
        return (parts[1], parts[2])
    if len(parts) != 2:
        msg = f"changed paths file status row must contain status and path: {line!r}"
        raise ValueError(msg)
    return (parts[1],)


def _is_git_name_status(status: str) -> bool:
    if status.startswith((RENAMED_GIT_STATUS_PREFIX, COPIED_GIT_STATUS_PREFIX)):
        return status[1:].isdigit()
    return status in SIMPLE_GIT_STATUS_CODES


def _pr_selection(
    *,
    eval_toml: Path,
    owned_paths: tuple[str, ...],
    smoke_case_ids: tuple[str, ...],
    changed_paths: tuple[str, ...],
) -> tuple[str, ...] | None:
    eval_dir_pattern = f"{eval_toml.parent.as_posix()}/**"
    for changed_path in changed_paths:
        if _matches_any(changed_path, UNIVERSAL_OWNED_PATHS):
            return ()
        if _matches_any(changed_path, (eval_dir_pattern, eval_toml.as_posix())):
            return ()

    for changed_path in changed_paths:
        if _matches_any(changed_path, owned_paths):
            return smoke_case_ids
    return None


def matches(path: str, pattern: str) -> bool:
    """Whether ``pattern`` selects ``path`` under CI-ownership glob rules.

    A trailing ``/**`` selects a directory's contents; ``fnmatch``'s ``*``
    already spans ``/``, so the pattern needs no handling beyond it. This is
    the one place the glob semantics of `owned_paths` are defined.

    The generated CI trigger filter matches the same paths, because
    :func:`outcomeeng_evals.definition.load_definition` admits only the two
    shapes both engines agree on — an exact path and a trailing ``/**``. The
    agreement is enforced at load time rather than assumed here: ``fnmatch``
    spans ``/`` with a bare ``*`` and the CI provider's glob engine does not.
    """

    return fnmatch.fnmatchcase(path, pattern)


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(matches(path, pattern) for pattern in patterns)
