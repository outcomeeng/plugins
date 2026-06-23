"""Harness for the pickup claim-verification script's ``l1`` tests.

Provides:

- An importlib loader for ``verify_session_claims.py``. The module ships under a
  hyphenated skill path that is not importable by package name; tests load it
  through ``importlib`` (mirroring ``sync_base``).
- ``RecordingRunner`` — a dependency-injected ``CommandRunner`` double that runs
  real ``git`` against a temp repo (Stage 4: git is cheap, deterministic, and
  observable at ``l1``), returns scripted output for ``spx`` and ``gh`` (Stage 5
  exceptions: contract probe and failure simulation), and records every command
  so the read-only / no-mutation rules are inspectable (exception 6).
- ``write_session_file`` — writes a minimal stored-format session file carrying
  the structured claims the script parses.

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
    """Delegates ``git`` to a real temp repo, scripts ``spx``/``gh``, records all calls."""

    repo: pathlib.Path
    scripted: dict[tuple[str, ...], tuple[int, str, str]] = field(default_factory=dict)
    calls: list[list[str]] = field(default_factory=list)

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        self.calls.append(list(cmd))
        for prefix, response in sorted(
            self.scripted.items(), key=lambda item: len(item[0]), reverse=True
        ):
            if tuple(cmd[: len(prefix)]) == prefix:
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


def write_session_file(
    directory: pathlib.Path,
    *,
    git_ref: str | None = None,
    git_status: str | None = None,
    specs: tuple[str, ...] = (),
    files: tuple[str, ...] = (),
    pr_numbers: tuple[str, ...] = (),
) -> pathlib.Path:
    """Write a minimal stored-format session file carrying structured claims."""
    front = ["---"]
    if git_ref is not None:
        front.append(f'"git_ref": "{git_ref}"')
    if specs:
        front.append('"specs":')
        front.extend(f'  - "{path}"' for path in specs)
    if files:
        front.append('"files":')
        front.extend(f'  - "{path}"' for path in files)
    front.append("---")
    body = ["<metadata>"]
    if git_status is not None:
        body.append(f"  git_status: {git_status}")
    body.append("</metadata>")
    if pr_numbers:
        body.append("<coordination>")
        body.extend(f"- shipped PR #{number}" for number in pr_numbers)
        body.append("</coordination>")
    path = directory / "session.md"
    path.write_text("\n".join(front + body) + "\n")
    return path


def session_show_response(
    *,
    git_ref: str | None = None,
    git_status: str | None = None,
    specs: tuple[str, ...] = (),
    files: tuple[str, ...] = (),
    pr_numbers: tuple[str, ...] = (),
) -> tuple[int, str, str]:
    """Return the ``spx session show --json`` response for structured fields."""
    _ = git_status, pr_numbers
    payload: dict[str, object] = {
        "id": "session",
        "status": "doing",
        "priority": "medium",
        "git_ref": git_ref,
        "goal": "Reconcile pickup claims.",
        "next_step": "Continue.",
        "specs": list(specs),
        "files": list(files),
        "created_at": "2026-06-23T00:00:00.000Z",
        "agent_session_id": "00000000-0000-0000-0000-000000000000",
    }
    return (0, json.dumps(payload), "")
