"""Reconcile a handoff session's recorded claims against current state.

`/pickup` runs this after bringing the checkout current and before its
post-context checkpoint, so the resuming agent acts on what the repository
supports now rather than on the snapshot frozen at handoff time. Each recorded
claim resolves to exactly one verdict -- ``Confirmed`` when current state matches,
``Discrepancy`` when it differs, ``Unverifiable`` when the check cannot run -- and
the verdicts are emitted as JSON for the workflow to render in place of the
recorded snapshot.

Stdlib-only ``python3`` shipped inside the pickup skill; runs under the two most
recent Python feature releases. Every ``spx``, ``gh``, and ``git`` call is issued
through an injected ``CommandRunner`` so the claim-checking logic is testable
without mocking, and the script only reads -- it never mutates the working tree,
the index, or the session file.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Final, Protocol, TypeGuard, cast


COMMAND_UNAVAILABLE_EXIT: Final = 127
type JsonScalar = str | int | float | bool | None


class Verdict(StrEnum):
    CONFIRMED = "Confirmed"
    DISCREPANCY = "Discrepancy"
    UNVERIFIABLE = "Unverifiable"


class ClaimKind(StrEnum):
    SESSION_METADATA = "session_metadata"
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

    def __init__(self, repo: Path, env: Mapping[str, str] | None = None) -> None:
        self._repo = repo
        self._env = dict(env) if env is not None else None

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        try:
            proc = subprocess.run(  # noqa: S603 - array args, no shell
                cmd, cwd=self._repo, capture_output=True, text=True, env=self._env
            )
        except OSError as exc:
            return COMMAND_UNAVAILABLE_EXIT, "", str(exc)
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


def load_session(
    session_id: str, runner: CommandRunner
) -> tuple[Session | None, ClaimVerdict | None]:
    """Read session claims through the spx session API, never a worktree path."""
    code, out, err = runner.run(["spx", "session", "show", "--json", session_id])
    if code != 0:
        return None, _session_unverifiable(
            session_id, f"spx session show --json unavailable: {_detail(err)}"
        )
    try:
        record = _single_session_record(json.loads(out))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return None, _session_unverifiable(
            session_id, f"spx session show --json returned invalid JSON: {exc}"
        )
    shape_error = _metadata_shape_error(record)
    if shape_error is not None:
        return None, _session_unverifiable(
            session_id, f"spx session show returned malformed metadata: {shape_error}"
        )

    raw_code, raw_out, raw_err = runner.run(["spx", "session", "show", session_id])
    if raw_code != 0:
        return None, _session_unverifiable(
            session_id, f"spx session show unavailable: {_detail(raw_err)}"
        )
    return parse_session(record, raw_out), None


def parse_session(record: dict[str, object], text: str) -> Session:
    """Extract structured claims from parsed frontmatter plus session prose."""
    payload = cast("dict[str, object]", record)
    git_ref = payload["git_ref"]
    return Session(
        git_ref=git_ref if isinstance(git_ref, str) else None,
        git_status=_body_git_status(text),
        specs=_string_tuple(payload["specs"]),
        files=_string_tuple(payload["files"]),
        pr_numbers=_pr_numbers(text),
    )


def _session_unverifiable(session_id: str, evidence: str) -> ClaimVerdict:
    return ClaimVerdict(
        ClaimKind.SESSION_METADATA, session_id, Verdict.UNVERIFIABLE, evidence
    )


def _detail(stderr: str) -> str:
    return stderr.strip() or "non-zero exit"


def _single_session_record(data: object) -> dict[str, object]:
    if isinstance(data, dict):
        return data
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
        return data[0]
    raise ValueError("expected one session record")


def _metadata_shape_error(payload: dict[str, object]) -> str | None:
    for key in ("git_ref", "specs", "files"):
        if key not in payload:
            return f"{key} is absent"
    git_ref = payload["git_ref"]
    if git_ref is not None and not isinstance(git_ref, str):
        return "git_ref is not a string or null"
    for key in ("specs", "files"):
        value = payload[key]
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            return f"{key} is not a list of strings"
        for item in value:
            path = PurePosixPath(item)
            if item == "" or path.is_absolute() or ".." in path.parts:
                return f"{key} contains a path outside the checkout"
    return None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _body_git_status(text: str) -> str | None:
    meta = re.search(r"^\s*git_status:\s*(clean|dirty)\s*$", text, re.MULTILINE)
    return meta.group(1) if meta else None


def _pr_numbers(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"(?:PR|pull request)\s*#(\d+)", text))


def check_git_ref(session: Session, runner: CommandRunner) -> ClaimVerdict | None:
    if session.git_ref is None:
        return None
    ref = session.git_ref
    branch_code, _, _ = runner.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{ref}"]
    )
    if branch_code == COMMAND_UNAVAILABLE_EXIT or branch_code >= 128:
        return ClaimVerdict(
            ClaimKind.GIT_REF, ref, Verdict.UNVERIFIABLE, "git unavailable"
        )
    if branch_code == 0:
        return ClaimVerdict(
            ClaimKind.GIT_REF,
            ref,
            Verdict.CONFIRMED,
            "branch present on origin",
        )
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        return ClaimVerdict(
            ClaimKind.GIT_REF,
            ref,
            Verdict.DISCREPANCY,
            "branch absent from origin",
        )
    code, _, _ = runner.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"]
    )
    if code == COMMAND_UNAVAILABLE_EXIT or code >= 128:
        return ClaimVerdict(
            ClaimKind.GIT_REF, ref, Verdict.UNVERIFIABLE, "git unavailable"
        )
    ok = code == 0
    return ClaimVerdict(
        ClaimKind.GIT_REF,
        ref,
        Verdict.CONFIRMED if ok else Verdict.DISCREPANCY,
        "commit reachable" if ok else "commit not in repository",
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
            ClaimVerdict(
                ClaimKind.NODE_STATUS,
                node,
                Verdict.CONFIRMED,
                _node_status_evidence(node, out),
            )
        )
    return verdicts


def _node_status_evidence(node: str, stdout: str) -> str:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout.strip()
    if not isinstance(payload, dict):
        return stdout.strip()
    summary: dict[str, JsonScalar] = {}
    for key in ("node", "path", "spec", "status", "state", "result"):
        if key not in payload:
            continue
        value = payload.get(key)
        if _is_json_scalar(value):
            summary[key] = value
    if "node" not in summary:
        summary["node"] = node
    return json.dumps(summary, sort_keys=True)


def _is_json_scalar(value: object) -> TypeGuard[JsonScalar]:
    return value is None or isinstance(value, str | int | float | bool)


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


def verify(session_id: str, repo: Path, runner: CommandRunner) -> list[ClaimVerdict]:
    """Reconcile every parseable recorded claim against current state."""
    session, load_error = load_session(session_id, runner)
    if session is None:
        if load_error is not None:
            return [load_error]
        return [
            _session_unverifiable(
                session_id, "internal: load_session returned no session and no error"
            )
        ]
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
        description="Reconcile a session's claims against current state."
    )
    parser.add_argument("session_id", help="Claimed session id")
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="Repository root (default: cwd)"
    )
    args = parser.parse_args(argv)
    verdicts = verify(args.session_id, args.repo, SubprocessRunner(args.repo))
    json.dump([asdict(v) for v in verdicts], sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
