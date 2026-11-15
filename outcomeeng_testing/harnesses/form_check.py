"""Synthetic-repository harness for the change-standards form check.

Backs the ``[test]`` evidence of ``spx/21-product-tree.enabler/79-changes.enabler``.
The harness loads ``form_check.py`` once, commits a synthetic repository under the
caller's ``tmp_path`` as a record's Base, writes one Draft against that Base, and
runs the form check's entry point on it in this process, returning the findings it
prints. The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SCRIPT: Final = (
    REPO_ROOT / "src/plugins/product-tree/skills/change-standards/scripts/form_check.py"
)
MODULE_NAME: Final = "form_check"


def load_form_check() -> ModuleType:
    """Return the form check module, loading it from ``SCRIPT`` on first use."""
    loaded = sys.modules.get(MODULE_NAME)
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *argv: str) -> str:
    """Run ``git`` in ``repo`` isolated from the user's configuration."""
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    completed = subprocess.run(
        ["git", *argv], cwd=repo, env=env, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def commit_base(repo: Path, files: Mapping[str, str]) -> str:
    """Create ``repo``, commit ``files`` as the Base, and return its commit."""
    git(repo.parent, "init", "-q", "-b", "main", str(repo))
    git(repo, "config", "commit.gpgsign", "false")
    for path, text in files.items():
        target = repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return git(repo, "rev-parse", "HEAD")


@dataclass(frozen=True)
class Intent:
    """The title and Statement of Intent lines of a Draft."""

    title: str
    output: str
    why: str
    verification: str


def write_draft(
    directory: Path,
    base: str,
    intent: Intent,
    heading: str,
    payload: Sequence[str],
) -> Path:
    """Write a Proposed Draft on ``base`` with one Declarations subsection."""
    draft = directory / "draft.md"
    lines = [
        "---",
        f"title: {intent.title}",
        "product: plugins",
        "maturity: Proposed",
        "lifecycle: Submitted",
        "parent: null",
        "predecessors: []",
        "blockers: []",
        f"base: {base}",
        "priority: null",
        "primary_value: null",
        "investment: null",
        "---",
        "",
        "## Statement of Intent",
        "",
        f"- Output: {intent.output}",
        f"- Why: {intent.why}",
        f"- Verification: {intent.verification}",
        "",
        "## Declarations",
        "",
        f"### {heading}",
        "",
        *payload,
        "",
    ]
    draft.write_text("\n".join(lines), encoding="utf-8")
    return draft


def findings(
    repo: Path, draft: Path, capsys: pytest.CaptureFixture[str]
) -> list[dict[str, str]]:
    """Run the form check on ``draft`` against ``repo`` and return its findings."""
    load_form_check().main(["--root", str(repo), "--draft", str(draft)])
    reported: list[dict[str, str]] = json.loads(capsys.readouterr().out).get(
        "findings", []
    )
    return reported
