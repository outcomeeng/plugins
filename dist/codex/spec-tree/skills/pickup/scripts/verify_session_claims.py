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
SPX_SESSION_SHOW_COMMAND: Final = ("spx", "session", "show")
SPX_SESSION_SHOW_JSON_FLAG: Final = "--json"
SPX_SPEC_STATUS_COMMAND: Final = ("spx", "spec", "status")
SPX_FORMAT_FLAG: Final = "--format"
SPX_JSON_FORMAT: Final = "json"
GIT_VERIFY_REF_COMMAND: Final = ("git", "rev-parse", "--verify", "--quiet")
GIT_STATUS_COMMAND: Final = ("git", "status", "--porcelain")
GH_PR_VIEW_COMMAND: Final = ("gh", "pr", "view")
GH_JSON_FLAG: Final = "--json"
GH_PR_STATE_FIELD: Final = "state"

SESSION_GIT_REF_FIELD: Final = "git_ref"
SESSION_SPECS_FIELD: Final = "specs"
SESSION_FILES_FIELD: Final = "files"
SESSION_GIT_STATUS_LABEL: Final = "git_status"
PR_REFERENCE_PREFIXES: Final = ("PR", "pull request")
EXTERNAL_ID_SUBJECT_PREFIX: Final = "PR #"
SESSION_REQUIRED_FIELDS: Final = (
    SESSION_GIT_REF_FIELD,
    SESSION_SPECS_FIELD,
    SESSION_FILES_FIELD,
)
SPEC_TREE_ROOT_DIR: Final = "spx"
SPEC_STATUS_NODES_FIELD: Final = "nodes"
NODE_RECORD_ID_FIELD: Final = "id"
NODE_RECORD_CHILDREN_FIELD: Final = "children"
type JsonScalar = str | int | float | bool | None


class Verdict(StrEnum):
    CONFIRMED = "Confirmed"
    DISCREPANCY = "Discrepancy"
    UNVERIFIABLE = "Unverifiable"


class ClaimRelation(StrEnum):
    """Source-owned relation between a recorded claim and observed state."""

    MATCHES = "matches"
    DIFFERS = "differs"
    OBSERVED = "observed"
    UNAVAILABLE = "unavailable"


CLAIM_RELATION_VERDICTS: Final[dict[ClaimRelation, Verdict]] = {
    ClaimRelation.MATCHES: Verdict.CONFIRMED,
    ClaimRelation.DIFFERS: Verdict.DISCREPANCY,
    ClaimRelation.OBSERVED: Verdict.CONFIRMED,
    ClaimRelation.UNAVAILABLE: Verdict.UNVERIFIABLE,
}


class ClaimKind(StrEnum):
    SESSION_METADATA = "session_metadata"
    GIT_REF = "git_ref"
    INJECTED_PATH = "injected_path"
    NODE_STATUS = "node_status"
    UNCOMMITTED_STATE = "uncommitted_state"
    EXTERNAL_ID = "external_id"


CLAIM_KIND_RELATIONS: Final[dict[ClaimKind, tuple[ClaimRelation, ...]]] = {
    ClaimKind.SESSION_METADATA: (ClaimRelation.UNAVAILABLE,),
    ClaimKind.GIT_REF: (
        ClaimRelation.MATCHES,
        ClaimRelation.DIFFERS,
        ClaimRelation.UNAVAILABLE,
    ),
    ClaimKind.INJECTED_PATH: (ClaimRelation.MATCHES, ClaimRelation.DIFFERS),
    ClaimKind.NODE_STATUS: (ClaimRelation.OBSERVED, ClaimRelation.UNAVAILABLE),
    ClaimKind.UNCOMMITTED_STATE: (
        ClaimRelation.MATCHES,
        ClaimRelation.DIFFERS,
        ClaimRelation.UNAVAILABLE,
    ),
    ClaimKind.EXTERNAL_ID: (ClaimRelation.OBSERVED, ClaimRelation.UNAVAILABLE),
}


class GitStatus(StrEnum):
    """Session vocabulary for the recorded working-tree state."""

    CLEAN = "clean"
    DIRTY = "dirty"


GIT_STATUS_PATTERN: Final = re.compile(
    rf"^\s*{re.escape(SESSION_GIT_STATUS_LABEL)}:\s*({'|'.join(GitStatus)})\s*$",
    re.MULTILINE,
)
PR_REFERENCE_PATTERN: Final = re.compile(
    rf"(?:{'|'.join(re.escape(prefix) for prefix in PR_REFERENCE_PREFIXES)})\s*#(\d+)"
)


def verdict_for_relation(relation: ClaimRelation) -> Verdict:
    """Map the finite claim/observation relation domain to its verdict."""
    return CLAIM_RELATION_VERDICTS[relation]


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


def claim_verdict(
    kind: ClaimKind,
    subject: str,
    relation: ClaimRelation,
    evidence: str,
) -> ClaimVerdict:
    """Construct a verdict only for a source-owned claim/relation pair."""
    if relation not in CLAIM_KIND_RELATIONS[kind]:
        raise ValueError(f"{relation} is not valid for {kind}")
    return ClaimVerdict(kind, subject, verdict_for_relation(relation), evidence)


@dataclass(frozen=True)
class Session:
    git_ref: str | None
    git_status: GitStatus | None
    specs: tuple[str, ...]
    files: tuple[str, ...]
    pr_numbers: tuple[str, ...]


def load_session(
    session_id: str, runner: CommandRunner
) -> tuple[Session | None, ClaimVerdict | None]:
    """Read session claims through the spx session API, never a worktree path."""
    code, out, err = runner.run(
        [*SPX_SESSION_SHOW_COMMAND, SPX_SESSION_SHOW_JSON_FLAG, session_id]
    )
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

    raw_code, raw_out, raw_err = runner.run([*SPX_SESSION_SHOW_COMMAND, session_id])
    if raw_code != 0:
        return None, _session_unverifiable(
            session_id, f"spx session show unavailable: {_detail(raw_err)}"
        )
    return parse_session(record, raw_out), None


def parse_session(record: dict[str, object], text: str) -> Session:
    """Extract structured claims from parsed frontmatter plus session prose."""
    payload = cast("dict[str, object]", record)
    git_ref = payload[SESSION_GIT_REF_FIELD]
    return Session(
        git_ref=git_ref if isinstance(git_ref, str) else None,
        git_status=_body_git_status(text),
        specs=_string_tuple(payload[SESSION_SPECS_FIELD]),
        files=_string_tuple(payload[SESSION_FILES_FIELD]),
        pr_numbers=_pr_numbers(text),
    )


def _session_unverifiable(session_id: str, evidence: str) -> ClaimVerdict:
    return claim_verdict(
        ClaimKind.SESSION_METADATA,
        session_id,
        ClaimRelation.UNAVAILABLE,
        evidence,
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
    for key in SESSION_REQUIRED_FIELDS:
        if key not in payload:
            return f"{key} is absent"
    git_ref = payload[SESSION_GIT_REF_FIELD]
    if git_ref is not None and not isinstance(git_ref, str):
        return "git_ref is not a string or null"
    for key in (SESSION_SPECS_FIELD, SESSION_FILES_FIELD):
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


def _body_git_status(text: str) -> GitStatus | None:
    meta = GIT_STATUS_PATTERN.search(text)
    return GitStatus(meta.group(1)) if meta else None


def _pr_numbers(text: str) -> tuple[str, ...]:
    return tuple(PR_REFERENCE_PATTERN.findall(text))


def check_git_ref(session: Session, runner: CommandRunner) -> ClaimVerdict | None:
    if session.git_ref is None:
        return None
    ref = session.git_ref
    branch_code, _, _ = runner.run(
        [*GIT_VERIFY_REF_COMMAND, f"refs/remotes/origin/{ref}"]
    )
    if branch_code == COMMAND_UNAVAILABLE_EXIT or branch_code >= 128:
        return claim_verdict(
            ClaimKind.GIT_REF,
            ref,
            ClaimRelation.UNAVAILABLE,
            "git unavailable",
        )
    if branch_code == 0:
        return claim_verdict(
            ClaimKind.GIT_REF,
            ref,
            ClaimRelation.MATCHES,
            "branch present on origin",
        )
    if not re.fullmatch(r"[0-9a-f]{40}", ref):
        return claim_verdict(
            ClaimKind.GIT_REF,
            ref,
            ClaimRelation.DIFFERS,
            "branch absent from origin",
        )
    code, _, _ = runner.run([*GIT_VERIFY_REF_COMMAND, f"{ref}^{{commit}}"])
    if code == COMMAND_UNAVAILABLE_EXIT or code >= 128:
        return claim_verdict(
            ClaimKind.GIT_REF,
            ref,
            ClaimRelation.UNAVAILABLE,
            "git unavailable",
        )
    ok = code == 0
    return claim_verdict(
        ClaimKind.GIT_REF,
        ref,
        ClaimRelation.MATCHES if ok else ClaimRelation.DIFFERS,
        "commit reachable" if ok else "commit not in repository",
    )


def check_paths(session: Session, repo: Path) -> list[ClaimVerdict]:
    verdicts: list[ClaimVerdict] = []
    for path in session.specs + session.files:
        exists = (repo / path).exists()
        verdicts.append(
            claim_verdict(
                ClaimKind.INJECTED_PATH,
                path,
                ClaimRelation.MATCHES if exists else ClaimRelation.DIFFERS,
                "path present in the current checkout"
                if exists
                else "path missing in the current checkout",
            )
        )
    return verdicts


def check_node_status(session: Session, runner: CommandRunner) -> list[ClaimVerdict]:
    if not session.specs:
        return []
    code, out, err = runner.run(
        [*SPX_SPEC_STATUS_COMMAND, SPX_FORMAT_FLAG, SPX_JSON_FORMAT]
    )
    nodes = _projection_nodes(out)
    verdicts: list[ClaimVerdict] = []
    for spec in session.specs:
        node = str(PurePosixPath(spec).parent)
        if code != 0:
            verdicts.append(
                claim_verdict(
                    ClaimKind.NODE_STATUS,
                    node,
                    ClaimRelation.UNAVAILABLE,
                    f"spx spec status unavailable: {_detail(err)}",
                )
            )
            continue
        record = _node_record(nodes, node)
        if record is None:
            verdicts.append(
                claim_verdict(
                    ClaimKind.NODE_STATUS,
                    node,
                    ClaimRelation.UNAVAILABLE,
                    f"node absent from the spx spec status projection: {node}",
                )
            )
            continue
        verdicts.append(
            claim_verdict(
                ClaimKind.NODE_STATUS,
                node,
                ClaimRelation.OBSERVED,
                json.dumps(record, sort_keys=True),
            )
        )
    return verdicts


def node_tree_id(node: str) -> str:
    """Address a node the way the spec-status projection keys it."""
    parts = PurePosixPath(node).parts
    if parts and parts[0] == SPEC_TREE_ROOT_DIR:
        parts = parts[1:]
    return str(PurePosixPath(*parts)) if parts else ""


def _projection_nodes(stdout: str) -> object | None:
    """Parse the spec-status projection once for the whole call."""
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload.get(SPEC_STATUS_NODES_FIELD)


def _node_record(nodes: object, node: str) -> dict[str, JsonScalar] | None:
    record = _find_node_record(nodes, node_tree_id(node))
    if record is None:
        return None
    return {
        key: value
        for key, value in record.items()
        if key != NODE_RECORD_CHILDREN_FIELD and _is_json_scalar(value)
    }


def _find_node_record(nodes: object, node_id: str) -> dict[str, object] | None:
    if not isinstance(nodes, list):
        return None
    for entry in nodes:
        if not isinstance(entry, dict):
            continue
        if entry.get(NODE_RECORD_ID_FIELD) == node_id:
            return entry
        found = _find_node_record(entry.get(NODE_RECORD_CHILDREN_FIELD), node_id)
        if found is not None:
            return found
    return None


def _is_json_scalar(value: object) -> TypeGuard[JsonScalar]:
    return value is None or isinstance(value, str | int | float | bool)


def check_uncommitted(session: Session, runner: CommandRunner) -> ClaimVerdict | None:
    if session.git_status is None:
        return None
    code, out, _ = runner.run(list(GIT_STATUS_COMMAND))
    if code != 0:
        return claim_verdict(
            ClaimKind.UNCOMMITTED_STATE,
            session.git_status,
            ClaimRelation.UNAVAILABLE,
            "git status unavailable",
        )
    now = GitStatus.DIRTY if out.strip() else GitStatus.CLEAN
    ok = now == session.git_status
    return claim_verdict(
        ClaimKind.UNCOMMITTED_STATE,
        session.git_status,
        ClaimRelation.MATCHES if ok else ClaimRelation.DIFFERS,
        f"working tree is {now}",
    )


def check_external_ids(session: Session, runner: CommandRunner) -> list[ClaimVerdict]:
    verdicts: list[ClaimVerdict] = []
    for number in session.pr_numbers:
        code, out, err = runner.run(
            [*GH_PR_VIEW_COMMAND, number, GH_JSON_FLAG, GH_PR_STATE_FIELD]
        )
        if code != 0:
            verdicts.append(
                claim_verdict(
                    ClaimKind.EXTERNAL_ID,
                    f"{EXTERNAL_ID_SUBJECT_PREFIX}{number}",
                    ClaimRelation.UNAVAILABLE,
                    f"gh unavailable: {err.strip() or 'non-zero exit'}",
                )
            )
            continue
        verdicts.append(
            claim_verdict(
                ClaimKind.EXTERNAL_ID,
                f"{EXTERNAL_ID_SUBJECT_PREFIX}{number}",
                ClaimRelation.OBSERVED,
                out.strip(),
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
