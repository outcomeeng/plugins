"""Harness for the pickup claim-verification script's ``l1`` tests.

Provides:

- An importlib loader for ``verify_session_claims.py``. The module ships under a
  hyphenated skill path that is not importable by package name; tests load it
  through ``importlib`` (mirroring ``sync_base``).
- ``RecordingRunner`` -- a dependency-injected ``CommandRunner`` double that runs
  real ``git`` against a temp repo (Stage 4: git is cheap, deterministic, and
  observable at ``l1``), returns scripted output for ``spx`` and ``gh`` (Stage 5
  exceptions: contract probe and failure simulation), and records every command
  so the read-only / no-mutation rules are inspectable (exception 6).
- ``session_command_scripts`` -- scripts the ``spx session show`` JSON and prose
  outputs the verifier consumes.

No framework mocks: the runner is an explicit injected object, and git runs for
real against a temp repository built by ``git_context``.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
from dataclasses import dataclass, field
from types import ModuleType

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFY_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "pickup"
    / "scripts"
    / "verify_session_claims.py"
)
SESSION_ID = "2026-01-01_00-00-00"


def load_verify_session_claims_module() -> ModuleType:
    """Load the ``verify_session_claims`` module via importlib and cache it."""
    cached = sys.modules.get("verify_session_claims")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "verify_session_claims", VERIFY_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load verify_session_claims from {VERIFY_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_session_claims"] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class RecordingRunner:
    """Delegates ``git`` to a real temp repo, scripts ``spx``/``gh``, records calls."""

    repo: pathlib.Path
    scripted: dict[tuple[str, ...], tuple[int, str, str]] = field(default_factory=dict)
    calls: list[list[str]] = field(default_factory=list)

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        self.calls.append(list(cmd))
        cmd_tuple = tuple(cmd)
        for prefix, response in self.scripted.items():
            if cmd_tuple == prefix:
                return response
        for prefix, response in self.scripted.items():
            if cmd_tuple[: len(prefix)] == prefix:
                return response
        if cmd and cmd[0] == "git":
            proc = subprocess.run(cmd, cwd=self.repo, capture_output=True, text=True)
            return proc.returncode, proc.stdout, proc.stderr
        return (1, "", f"not scripted: {' '.join(cmd)}")


def head_sha(repo: pathlib.Path) -> str:
    """Return the repo's current HEAD commit SHA."""
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def dirty_tree(repo: pathlib.Path, name: str = "scratch.txt") -> None:
    """Leave an uncommitted untracked file so ``git status`` reports dirty."""
    (repo / name).write_text("uncommitted\n")


def session_command_scripts(
    *,
    git_ref: str | None = None,
    git_status: str | None = None,
    specs: tuple[str, ...] = (),
    files: tuple[str, ...] = (),
    pr_numbers: tuple[str, ...] = (),
) -> dict[tuple[str, ...], tuple[int, str, str]]:
    """Return ``spx session show`` outputs carrying structured claims."""
    record: dict[str, object] = {
        "id": SESSION_ID,
        "status": "doing",
        "git_ref": git_ref,
        "specs": list(specs),
        "files": list(files),
    }
    front = ["---"]
    for key, value in record.items():
        front.append(f'"{key}": {json.dumps(value)}')
    front.append("---")
    body = ["<metadata>"]
    if git_status is not None:
        body.append(f"  git_status: {git_status}")
    body.append("</metadata>")
    if pr_numbers:
        body.append("<coordination>")
        body.extend(f"- shipped PR #{number}" for number in pr_numbers)
        body.append("</coordination>")
    raw = "\n".join(front + body) + "\n"
    return {
        ("spx", "session", "show", "--json", SESSION_ID): (
            0,
            json.dumps(record),
            "",
        ),
        ("spx", "session", "show", SESSION_ID): (0, raw, ""),
    }
