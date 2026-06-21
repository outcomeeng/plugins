"""Reconcile a handoff session file's recorded claims against current state.

`/pickup` runs this after bringing the checkout current and before its
post-context checkpoint, so the resuming agent acts on what the repository
supports now rather than on the snapshot frozen at handoff time. Each recorded
claim resolves to exactly one verdict — ``Confirmed`` when current state matches,
``Discrepancy`` when it differs, ``Unverifiable`` when the check cannot run — and
the verdicts are emitted as JSON for the workflow to render in place of the
recorded snapshot.

Stdlib-only ``python3`` shipped inside the pickup skill; runs under the two most
recent Python feature releases. Every ``spx``, ``gh``, and ``git`` call is issued
through an injected ``CommandRunner`` so the claim-checking logic is testable
without mocking, and the script only reads — it never mutates the working tree,
the index, or the session file.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol


class Verdict(StrEnum):
    CONFIRMED = "Confirmed"
    DISCREPANCY = "Discrepancy"
    UNVERIFIABLE = "Unverifiable"


class ClaimKind(StrEnum):
    GIT_REF = "git_ref"
    INJECTED_PATH = "injected_path"
    NODE_STATUS = "node_status"
    UNCOMMITTED_STATE = "uncommitted_state"
    EXTERNAL_ID = "external_id"


class CommandRunner(Protocol):
    """Issues a read-only command and returns ``(returncode, stdout, stderr)``."""

    def run(self, cmd: list[str]) -> tuple[int, str, str]: ...


class SubprocessRunner:
    """Default runner: array-argument subprocess rooted at the repository."""

    def __init__(self, repo: Path) -> None:
        self._repo = repo

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        proc = subprocess.run(  # noqa: S603 - array args, no shell
            cmd, cwd=self._repo, capture_output=True, text=True
        )
        return proc.returncode, proc.stdout, proc.stderr


@dataclass(frozen=True)
class ClaimVerdict:
    kind: ClaimKind
    subject: str
    verdict: Verdict
    evidence: str


@dataclass(frozen=True)
class Session:
    git_ref: str | None
    git_status: str | None
    specs: tuple[str, ...]
    files: tuple[str, ...]
    pr_numbers: tuple[str, ...]


def parse_session(text: str) -> Session:
    """Extract the structured, reliably-parseable claims from a session file."""
    git_ref = _scalar(text, "git_ref")
    git_status = None
    meta = re.search(r"git_status:\s*(clean|dirty)", text)
    if meta:
        git_status = meta.group(1)
    return Session(
        git_ref=git_ref,
        git_status=git_status,
        specs=_string_list(text, "specs"),
        files=_string_list(text, "files"),
        pr_numbers=tuple(re.findall(r"(?:PR|pull request)\s*#(\d+)", text)),
    )


def _scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^{key}:\s*\"?([^\"\n]+?)\"?\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def _string_list(text: str, key: str) -> tuple[str, ...]:
    # Require indentation before each bullet so the YAML document delimiter
    # `---` (no leading space) is never absorbed as a trailing list item.
    block = re.search(rf"^{key}:\s*\n((?:[ \t]+-\s*.+\n?)+)", text, re.MULTILINE)
    if not block:
        return ()
    items = re.findall(r"-\s*\"?([^\"\n]+?)\"?\s*$", block.group(1), re.MULTILINE)
    return tuple(items)


def check_git_ref(session: Session, runner: CommandRunner) -> ClaimVerdict | None:
    if session.git_ref is None:
        return None
    ref = session.git_ref
    if re.fullmatch(r"[0-9a-f]{7,40}", ref):
        expr = f"{ref}^{{commit}}"
        present, absent = "commit reachable", "commit not in repository"
    else:
        expr = f"refs/remotes/origin/{ref}"
        present, absent = "branch present on origin", "branch absent from origin"
    # rev-parse --verify --quiet exits 0 (resolves), 1 (clean miss), >=128 (git
    # could not run). The exit code, not the stderr text, distinguishes a missing
    # object — which also prints "fatal:" — from git being unavailable.
    code, _, _ = runner.run(["git", "rev-parse", "--verify", "--quiet", expr])
    if code >= 128:
        return ClaimVerdict(
            ClaimKind.GIT_REF, ref, Verdict.UNVERIFIABLE, "git unavailable"
        )
    ok = code == 0
    return ClaimVerdict(
        ClaimKind.GIT_REF,
        ref,
        Verdict.CONFIRMED if ok else Verdict.DISCREPANCY,
        present if ok else absent,
    )


def check_paths(session: Session, repo: Path) -> list[ClaimVerdict]:
    verdicts: list[ClaimVerdict] = []
    for path in session.specs + session.files:
        exists = (repo / path).exists()
        verdicts.append(
            ClaimVerdict(
                ClaimKind.INJECTED_PATH,
                path,
                Verdict.CONFIRMED if exists else Verdict.DISCREPANCY,
                "path present in the current checkout"
                if exists
                else "path missing in the current checkout",
            )
        )
    return verdicts


def check_node_status(session: Session, runner: CommandRunner) -> list[ClaimVerdict]:
    verdicts: list[ClaimVerdict] = []
    for spec in session.specs:
        node = str(Path(spec).parent)
        code, out, err = runner.run(["spx", "spec", "status", node, "--format", "json"])
        if code != 0:
            verdicts.append(
                ClaimVerdict(
                    ClaimKind.NODE_STATUS,
                    node,
                    Verdict.UNVERIFIABLE,
                    f"spx spec status unavailable: {err.strip() or 'non-zero exit'}",
                )
            )
            continue
        verdicts.append(
            ClaimVerdict(ClaimKind.NODE_STATUS, node, Verdict.CONFIRMED, out.strip())
        )
    return verdicts


def check_uncommitted(session: Session, runner: CommandRunner) -> ClaimVerdict | None:
    if session.git_status is None:
        return None
    code, out, _ = runner.run(["git", "status", "--porcelain"])
    if code != 0:
        return ClaimVerdict(
            ClaimKind.UNCOMMITTED_STATE,
            session.git_status,
            Verdict.UNVERIFIABLE,
            "git status unavailable",
        )
    now = "dirty" if out.strip() else "clean"
    ok = now == session.git_status
    return ClaimVerdict(
        ClaimKind.UNCOMMITTED_STATE,
        session.git_status,
        Verdict.CONFIRMED if ok else Verdict.DISCREPANCY,
        f"working tree is {now}",
    )


def check_external_ids(session: Session, runner: CommandRunner) -> list[ClaimVerdict]:
    verdicts: list[ClaimVerdict] = []
    for number in session.pr_numbers:
        code, out, err = runner.run(["gh", "pr", "view", number, "--json", "state"])
        if code != 0:
            verdicts.append(
                ClaimVerdict(
                    ClaimKind.EXTERNAL_ID,
                    f"PR #{number}",
                    Verdict.UNVERIFIABLE,
                    f"gh unavailable: {err.strip() or 'non-zero exit'}",
                )
            )
            continue
        verdicts.append(
            ClaimVerdict(
                ClaimKind.EXTERNAL_ID, f"PR #{number}", Verdict.CONFIRMED, out.strip()
            )
        )
    return verdicts


def verify(session_path: Path, repo: Path, runner: CommandRunner) -> list[ClaimVerdict]:
    """Reconcile every parseable recorded claim against current state."""
    session = parse_session(session_path.read_text())
    verdicts: list[ClaimVerdict] = []
    git_ref = check_git_ref(session, runner)
    if git_ref is not None:
        verdicts.append(git_ref)
    verdicts.extend(check_paths(session, repo))
    verdicts.extend(check_node_status(session, runner))
    uncommitted = check_uncommitted(session, runner)
    if uncommitted is not None:
        verdicts.append(uncommitted)
    verdicts.extend(check_external_ids(session, runner))
    return verdicts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile a session file's claims against current state."
    )
    parser.add_argument("session", type=Path, help="Path to the claimed session file")
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="Repository root (default: cwd)"
    )
    args = parser.parse_args(argv)
    verdicts = verify(args.session, args.repo, SubprocessRunner(args.repo))
    json.dump([asdict(v) for v in verdicts], sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
