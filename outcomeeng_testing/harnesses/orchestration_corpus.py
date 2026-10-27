"""Resolve the shared orchestration fixture corpus inside the pinned spx checkout."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import cast

from outcomeeng.validation.ci_gate import (
    CHECKOUT_ACTION_PREFIX,
    CHECKOUT_PATH_KEY,
    CHECKOUT_REPOSITORY_KEY,
    SPX_REPOSITORY,
    STEP_USES_KEY,
    STEP_WITH_KEY,
)
from outcomeeng.validation.orchestration_corpus import ORCHESTRATION_CORPUS_PATH
from outcomeeng_testing.harnesses.ci_gate import (
    REPO_ROOT,
    gate_steps,
    workflow,
)


class OrchestrationCorpusMissingError(FileNotFoundError):
    """The pinned spx checkout carries no orchestration fixture corpus directory."""


def spx_checkout_directory(workflow_path: Path | None = None) -> Path:
    """Return the directory the workflow's `outcomeeng/spx` checkout step declares."""
    for step in gate_steps(workflow(workflow_path)):
        if CHECKOUT_ACTION_PREFIX not in cast("str", step.get(STEP_USES_KEY, "")):
            continue
        declared = cast("dict[str, str]", step.get(STEP_WITH_KEY, {}))
        if declared.get(CHECKOUT_REPOSITORY_KEY) == SPX_REPOSITORY:
            return REPO_ROOT / declared[CHECKOUT_PATH_KEY]
    raise LookupError(f"no checkout step of {SPX_REPOSITORY} in the gate workflow")


def orchestration_corpus_directory(checkout_root: Path | None = None) -> Path:
    """Return the corpus directory inside the checkout; fail naming the missing path."""
    root = spx_checkout_directory() if checkout_root is None else checkout_root
    corpus = root / ORCHESTRATION_CORPUS_PATH
    if not corpus.is_dir():
        raise OrchestrationCorpusMissingError(
            f"orchestration fixture corpus directory is missing: {corpus}"
        )
    return corpus


def tracked_files_of_new_repository(
    directory: Path, relative_paths: Iterable[str]
) -> list[str]:
    """Create a git repository tracking one empty file per path; return its tracked files."""
    subprocess.run(["git", "init", "--quiet"], cwd=directory, check=True)
    for relative in relative_paths:
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("")
        subprocess.run(["git", "add", "--", relative], cwd=directory, check=True)
    listed = subprocess.run(
        ["git", "ls-files"],
        cwd=directory,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in listed.stdout.splitlines() if line]
