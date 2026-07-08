"""CI planning for eval suites."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from outcomeeng_evals.definition import CiPolicy, EVAL_TOML_FILENAME, load_definition


UNIVERSAL_OWNED_PATHS = (
    "outcomeeng_evals/**",
    "outcomeeng_testing/evals/**",
    "outcomeeng_testing/generators/**",
    "outcomeeng_testing/harnesses/**",
)
RENAMED_GIT_STATUS_PREFIX = "R"
COPIED_GIT_STATUS_PREFIX = "C"


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
    """Read repository-relative changed paths from a git changed-path file."""

    if path is None:
        return ()
    return tuple(
        changed_path
        for line in path.read_text(encoding="utf-8").splitlines()
        for changed_path in _changed_paths_from_line(line)
    )


def _changed_paths_from_line(line: str) -> tuple[str, ...]:
    if not line:
        return ()
    parts = line.split("\t")
    status = parts[0]
    if len(parts) == 1:
        return (line,)
    if status.startswith((RENAMED_GIT_STATUS_PREFIX, COPIED_GIT_STATUS_PREFIX)):
        if len(parts) < 3:
            return ()
        return (parts[1], parts[2])
    return (parts[1],)


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


def _matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)
