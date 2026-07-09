"""Derivation of the CI workflow's eval trigger paths from eval definitions.

A path-filtered CI workflow decides whether the eval job starts at all. That
decision is evaluated by the CI provider's event router before any code runs,
so it cannot call :func:`outcomeeng_evals.ci_plan.build_ci_plan` — the router
needs a static list of path patterns.

That static list is the only place in the system where eval ownership must be
materialized as text. Every other consumer reads ``eval.toml`` directly. Hand
maintaining the list drifts in both directions: an ``owned_paths`` entry absent
from the list silently prevents its suite from ever running, and a stale entry
no suite owns burns a runner on every matching change. This module computes the
list from the same inputs the planner reads, so the workflow's trigger surface
is generated rather than transcribed.

The derived set is exact, not a convenient superset. Under-inclusion loses eval
coverage silently; over-inclusion wastes a runner. Both are defects, and a
generator that reads a closed set of inputs has no reason to commit either.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng_evals.ci_plan import UNIVERSAL_OWNED_PATHS
from outcomeeng_evals.definition import CiPolicy, EVAL_TOML_FILENAME, load_definition


BEGIN_MARKER: Final = "# BEGIN eval-trigger-paths"
END_MARKER: Final = "# END eval-trigger-paths"

# One block per trigger event the workflow declares (`pull_request`, `push`).
# A file carrying a different count is not the workflow this command generates.
EXPECTED_BLOCK_COUNT: Final = 2

_RECURSIVE_GLOB_SUFFIX: Final = "/**"

_BLOCK_PATTERN: Final = re.compile(
    rf"(?P<indent>[ ]*){re.escape(BEGIN_MARKER)}\n"
    rf"(?:.*?\n)*?"
    rf"(?P=indent){re.escape(END_MARKER)}"
)


class CiTriggerError(Exception):
    """A workflow file cannot carry generated eval trigger paths."""


@dataclass(frozen=True)
class CiTriggerResult:
    """Outcome of materializing (or checking) a workflow's trigger paths."""

    workflow: Path
    paths: tuple[str, ...]
    changed: bool


def ci_trigger_paths(root: Path, *, repo_root: Path = Path()) -> tuple[str, ...]:
    """Return the exact, minimal path patterns that must trigger eval CI.

    The union of every CI-eligible suite's ``owned_paths``, its own eval
    directory, and the universal surfaces that force a full plan. Suites
    declaring ``ci_policy = "manual"`` are excluded: no automated run selects
    them, so a trigger on their owned paths would start a job with an empty
    plan.

    A derived eval-directory glob is expressed relative to ``repo_root``,
    because a trigger pattern is matched against repository-relative paths.
    """

    resolved_repo_root = repo_root.resolve()
    patterns: set[str] = set(UNIVERSAL_OWNED_PATHS)
    for eval_toml in sorted(root.rglob(EVAL_TOML_FILENAME)):
        definition = load_definition(eval_toml)
        if definition.ci_policy is CiPolicy.MANUAL:
            continue
        eval_dir = eval_toml.parent.resolve()
        try:
            relative_dir = eval_dir.relative_to(resolved_repo_root)
        except ValueError as exc:
            msg = f"eval directory is outside the repository root: {eval_dir}"
            raise CiTriggerError(msg) from exc
        patterns.add(f"{relative_dir.as_posix()}{_RECURSIVE_GLOB_SUFFIX}")
        patterns.update(definition.owned_paths)
    return minimal_patterns(patterns)


def render_trigger_block(paths: tuple[str, ...], *, indent: str) -> str:
    """Render the marker-delimited YAML sequence entries for ``paths``."""

    entries = "".join(f'{indent}- "{path}"\n' for path in paths)
    return f"{indent}{BEGIN_MARKER}\n{entries}{indent}{END_MARKER}"


def render_workflow(workflow_text: str, paths: tuple[str, ...]) -> str:
    """Replace every generated trigger block in ``workflow_text``."""

    blocks = _BLOCK_PATTERN.findall(workflow_text)
    if len(blocks) != EXPECTED_BLOCK_COUNT:
        msg = (
            f"expected {EXPECTED_BLOCK_COUNT} {BEGIN_MARKER!r}/{END_MARKER!r} "
            f"blocks, found {len(blocks)}"
        )
        raise CiTriggerError(msg)

    def _replace(match: re.Match[str]) -> str:
        return render_trigger_block(paths, indent=match["indent"])

    return _BLOCK_PATTERN.sub(_replace, workflow_text)


def materialize_ci_triggers(
    root: Path,
    workflow: Path,
    *,
    repo_root: Path = Path(),
    check: bool = False,
) -> CiTriggerResult:
    """Write the workflow's trigger blocks, or report drift when ``check``.

    Raises :class:`CiTriggerError` in ``check`` mode when the committed
    workflow's trigger blocks differ from the blocks derived from ``root``.
    """

    if not workflow.is_file():
        msg = f"workflow not found: {workflow}"
        raise CiTriggerError(msg)

    paths = ci_trigger_paths(root, repo_root=repo_root)
    current = workflow.read_text(encoding="utf-8")
    rendered = render_workflow(current, paths)
    changed = rendered != current

    if not changed:
        return CiTriggerResult(workflow=workflow, paths=paths, changed=False)
    if check:
        msg = (
            f"{workflow}: eval trigger paths are stale. "
            f"Run `just build-eval-triggers` and commit the result."
        )
        raise CiTriggerError(msg)

    workflow.write_text(rendered, encoding="utf-8")
    return CiTriggerResult(workflow=workflow, paths=paths, changed=True)


def minimal_patterns(patterns: set[str]) -> tuple[str, ...]:
    """Drop every pattern a recursive-glob sibling already covers.

    ``a/b/**`` matches everything under ``a/b/``, so a co-present ``a/b/c/**``
    or ``a/b/c.md`` adds no coverage. Removing it keeps the rendered list the
    shortest text with identical matching behavior, which keeps a real ownership
    change visible in the diff instead of buried among redundant entries.
    """

    # Each recursive glob covers its own prefix. A glob never covers itself, so
    # the owner is carried alongside the prefix and skipped during the scan.
    covering = {
        pattern.removesuffix(_RECURSIVE_GLOB_SUFFIX) + "/": pattern
        for pattern in patterns
        if pattern.endswith(_RECURSIVE_GLOB_SUFFIX)
    }
    return tuple(
        sorted(
            pattern
            for pattern in patterns
            if not any(
                pattern != owner and pattern.startswith(prefix)
                for prefix, owner in covering.items()
            )
        )
    )
