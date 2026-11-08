"""Simulated GitHub Change Store for the `operate-change` script.

Backs the ``[test]`` evidence of the operate-change node. The script reaches
the Change Store only through its injected command runner, so the harness
passes it ``SimulatedGitHub``, a collaborator that answers each `gh` command
from an in-memory store and applies each write `gh` would apply, under the
interaction-protocol and failure-simulation exceptions of the test
methodology: it records every command in order, can make a chosen command
fail, can accept a write and leave the store unchanged, and can run a hook
after a chosen command, which is how another writer's edit lands between two
of the script's commands. `git` commands pass through to the real `git`, so
the review carry-forward reads a real repository the harness builds in a
temporary directory.

The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, Final

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SCRIPT: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "product-tree"
    / "skills"
    / "operate-change"
    / "scripts"
    / "operate_change.py"
)

#: The invented store, owner, and identities the simulated store serves.
STORE: Final = "example-org/example-changes"
LOGIN: Final = "example-account"
SESSION: Final = "11111111-2222-4333-8444-555555555555"
OTHER_SESSION: Final = "99999999-8888-4777-8666-555555555555"
WORKTREE: Final = "/work/example/worktrees/applier"
MACHINE: Final = "example@host"
HARNESS: Final = "example-harness"
PRODUCT_REPOSITORY: Final = "example-org/example-product"
MERGE_COMMIT: Final = "a" * 40
UNMERGED_COMMIT: Final = "b" * 40

#: The words the form check, the audit, and the infrastructure lookup hand the script.
APPROVED: Final = "approved"
REJECTED: Final = "rejected"
PASSING: Final = "Passing"
SPECIFIED: Final = "Specified"
FORM_STATUS: Final = "status"
FORM_BODY: Final = "body_sha256"
FORM_PASS: Final = "pass"
FORM_FAIL: Final = "fail"

_EPOCH: Final = datetime(2026, 1, 1, tzinfo=UTC)

_script_module: ModuleType | None = None


def load_script() -> ModuleType:
    """Load the shipped script module by path, once per session."""
    global _script_module
    if _script_module is None:
        spec = importlib.util.spec_from_file_location("operate_change", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load the operate-change script from {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["operate_change"] = module
        spec.loader.exec_module(module)
        _script_module = module
    return _script_module


script = load_script()

#: The vocabulary the script owns; the harness and the tests read it from there.
Transition = script.Transition
Maturity = script.Maturity
Lifecycle = script.Lifecycle
Mover = script.Mover
LowerCause = script.LowerCause
Status = script.Status
Reason = script.Reason
WriteKind = script.WriteKind
IssueState = script.IssueState
Field = script.Field
LogKey = script.LogKey
HandoffKey = script.HandoffKey
ChangesetKey = script.ChangesetKey


def _keys(name: str, record: Any) -> Any:
    """A key enumeration naming the fields of one of the script's request records."""
    members = {
        field_name.upper(): field_name for field_name in record.__dataclass_fields__
    }
    return StrEnum(name, members)  # type: ignore[misc]


#: The keys of a request, of the session identity, of a bound pair, and of a close check.
RequestKey = _keys("RequestKey", script.Request)
IdentityKey = _keys("IdentityKey", script.Identity)
PairKey = _keys("PairKey", script.BoundPair)
CloseKey = _keys("CloseKey", script.CloseCheck)

#: The organization issue field each issue-field write reaches.
FIELD_WRITES: Final = {
    Field.MATURITY.value: WriteKind.MATURITY,
    Field.LIFECYCLE.value: WriteKind.LIFECYCLE,
}


@dataclass
class Issue:
    """One Change issue as the simulated store holds it."""

    number: int
    body: str
    fields: dict[str, Any]
    state: str = IssueState.OPEN.value
    title: str = "An example Change"
    assignees: list[str] = field(default_factory=list)
    comments: list[dict[str, Any]] = field(default_factory=list)
    edits: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    blocked_by: list[int] = field(default_factory=list)
    close_reason: str | None = None


@dataclass
class SimulatedGitHub:
    """A `gh` runner answering from an in-memory Change Store."""

    issues: dict[int, Issue] = field(default_factory=dict)
    merged: set[str] = field(default_factory=lambda: {MERGE_COMMIT})
    commands: list[tuple[str, ...]] = field(default_factory=list)
    fail_when: Callable[[Sequence[str]], bool] | None = None
    ignore_when: Callable[[Sequence[str]], bool] | None = None
    after: Callable[[SimulatedGitHub, Sequence[str]], None] | None = None
    clock: int = 0

    # -------------------------------------------------------------- setup

    def now(self) -> str:
        self.clock += 1
        return (_EPOCH + timedelta(seconds=self.clock)).strftime("%Y-%m-%dT%H:%M:%SZ")

    def add(self, number: int, body: str, fields: Mapping[str, Any]) -> Issue:
        issue = Issue(number, body, dict(fields))
        issue.edits.append(
            {"id": f"UCE_{number}_0", "editedAt": self.now(), "diff": body}
        )
        for name, value in fields.items():
            issue.events.append(
                {
                    "createdAt": self.now(),
                    "newValue": value,
                    "issueField": {"name": name},
                }
            )
        self.issues[number] = issue
        return issue

    def edit_body(self, number: int, body: str) -> None:
        issue = self.issues[number]
        issue.body = body
        issue.edits.append(
            {
                "id": f"UCE_{number}_{len(issue.edits)}",
                "editedAt": self.now(),
                "diff": body,
            }
        )

    def set_field(self, number: int, name: str, value: Any) -> None:
        issue = self.issues[number]
        issue.fields[name] = value
        issue.events.append(
            {"createdAt": self.now(), "newValue": value, "issueField": {"name": name}}
        )

    def post(self, number: int, body: str, author: str = LOGIN) -> str:
        issue = self.issues[number]
        url = f"https://github.com/{STORE}/issues/{number}#issuecomment-{len(issue.comments) + 1}"
        issue.comments.append(
            {
                "createdAt": self.now(),
                "url": url,
                "body": body,
                "author": {"login": author},
            }
        )
        return url

    # ----------------------------------------------------------- the runner

    def __call__(self, args: Sequence[str], stdin: str | None = None) -> Any:
        command = tuple(args)
        if command[0] == "git":
            completed = subprocess.run(
                list(command), capture_output=True, text=True, check=False
            )
            return script.CommandResult(
                completed.returncode, completed.stdout, completed.stderr
            )
        self.commands.append(command)
        if self.fail_when is not None and self.fail_when(command):
            return script.CommandResult(1, "", "simulated failure")
        ignored = self.ignore_when is not None and self.ignore_when(command)
        stdout = self._answer(command, stdin, ignored)
        if self.after is not None:
            self.after(self, command)
        return script.CommandResult(0, stdout, "")

    def _answer(
        self, command: tuple[str, ...], stdin: str | None, ignored: bool
    ) -> str:
        if command[1:3] == ("api", "graphql"):
            return json.dumps({"data": self._graphql(command, ignored)})
        if command[1:3] == ("issue", "edit"):
            issue = self.issues[int(command[3])]
            if not ignored:
                login = command[-1]
                if command[-2] == "--add-assignee" and login not in issue.assignees:
                    issue.assignees.append(login)
                if command[-2] == "--remove-assignee" and login in issue.assignees:
                    issue.assignees.remove(login)
            return ""
        if command[1:3] == ("issue", "comment"):
            if ignored:
                return (
                    f"https://github.com/{STORE}/issues/{command[3]}#issuecomment-0\n"
                )
            return self.post(int(command[3]), stdin or "") + "\n"
        if command[1:3] == ("issue", "close"):
            issue = self.issues[int(command[3])]
            if not ignored:
                issue.state = IssueState.CLOSED.value
                issue.close_reason = command[-1]
            return ""
        if command[1:3] == ("repo", "view"):
            return "main\n"
        return self._rest(command, ignored)

    def _rest(self, command: tuple[str, ...], ignored: bool) -> str:
        path = next(part for part in command[2:] if part.startswith("repos/"))
        if "/compare/" in path:
            commit = path.split("/compare/")[1].split("...")[0]
            return ("ahead" if commit in self.merged else "diverged") + "\n"
        parts = path.split("/")
        number = int(parts[4])
        if path.endswith("/dependencies/blocked_by") and "POST" in command:
            blocker = (
                int(next(p for p in command if p.startswith("issue_id=")).split("=")[1])
                // 1000
            )
            if not ignored:
                self.issues[number].blocked_by.append(blocker)
            return "{}"
        if path.endswith("/dependencies/blocked_by"):
            return json.dumps(
                [self._rest_issue(n) for n in self.issues[number].blocked_by]
            )
        if path.endswith("/dependencies/blocking"):
            return json.dumps(
                [
                    self._rest_issue(n)
                    for n, issue in self.issues.items()
                    if number in issue.blocked_by
                ]
            )
        return f"{number * 1000}\n"

    def _rest_issue(self, number: int) -> dict[str, Any]:
        return {"number": number, "state": self.issues[number].state.lower()}

    def _variables(self, command: tuple[str, ...]) -> dict[str, str]:
        found: dict[str, str] = {}
        for flag, value in zip(command, command[1:]):
            if flag in ("-f", "-F") and "=" in value:
                name, _, raw = value.partition("=")
                found[name] = raw
        return found

    def _graphql(self, command: tuple[str, ...], ignored: bool) -> dict[str, Any]:
        variables = self._variables(command)
        query = variables["query"]
        if "setIssueFieldValue" in query:
            if not ignored:
                number = next(
                    n
                    for n, issue in self.issues.items()
                    if f"I_{n}" == variables["issue"]
                )
                name = variables["field"].removeprefix("F_")
                option = variables["option"].removeprefix(f"O_{name}_")
                self.set_field(number, name, option)
            return {"setIssueFieldValue": {"clientMutationId": None}}
        if "organization(" in query:
            fields = {
                Field.MATURITY.value: tuple(member.value for member in Maturity),
                Field.LIFECYCLE.value: tuple(member.value for member in Lifecycle),
            }
            return {
                "organization": {
                    "issueFields": {
                        "nodes": [
                            {
                                "id": f"F_{name}",
                                "name": name,
                                "options": [
                                    {"id": f"O_{name}_{option}", "name": option}
                                    for option in options
                                ],
                            }
                            for name, options in fields.items()
                        ]
                    }
                }
            }
        if "issues(first" in query:
            return {
                "repository": {
                    "issues": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [self._child_node(i) for i in self.issues.values()],
                    }
                }
            }
        issue = self.issues[int(variables["n"])]
        if "timelineItems" in query:
            return {
                "repository": {
                    "issue": {
                        "timelineItems": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": list(issue.events),
                        }
                    }
                }
            }
        return {"repository": {"issue": self._state_node(issue)}}

    def _child_node(self, issue: Issue) -> dict[str, Any]:
        parent = issue.fields.get(Field.PARENT)
        values = (
            []
            if parent is None
            else [{"value": float(parent), "field": {"name": Field.PARENT.value}}]
        )
        return {
            "number": issue.number,
            "state": issue.state,
            "issueFieldValues": {"nodes": values},
        }

    def _state_node(self, issue: Issue) -> dict[str, Any]:
        values: list[dict[str, Any]] = []
        for name, value in issue.fields.items():
            if name in (Field.MATURITY, Field.LIFECYCLE):
                values.append({"name": value, "field": {"name": name}})
            elif name == Field.PARENT:
                values.append({"value": float(value), "field": {"name": name}})
            else:
                values.append({"value": value, "field": {"name": name}})
        return {
            "id": f"I_{issue.number}",
            "state": issue.state,
            "title": issue.title,
            "body": issue.body,
            "assignees": {
                "totalCount": len(issue.assignees),
                "nodes": [{"login": login} for login in issue.assignees],
            },
            "userContentEdits": {
                "totalCount": len(issue.edits),
                "nodes": list(reversed(issue.edits)),
            },
            "comments": {
                "totalCount": len(issue.comments),
                "nodes": list(issue.comments),
            },
            "issueFieldValues": {"pageInfo": {"hasNextPage": False}, "nodes": values},
        }

    # -------------------------------------------------------- observations

    def writes(self) -> list[tuple[str, ...]]:
        """Every command that changes the store, in order."""
        return [command for command in self.commands if is_write(command)]

    def blocks(self, number: int) -> list[str]:
        """The comment bodies of one issue, in order."""
        return [comment["body"] for comment in self.issues[number].comments]


def is_write(command: Sequence[str]) -> bool:
    """Whether a `gh` command changes the store, by the vocabulary `gh` and GraphQL own."""
    if tuple(command[1:3]) in (
        ("issue", "edit"),
        ("issue", "comment"),
        ("issue", "close"),
    ):
        return True
    if tuple(command[1:3]) == ("api", "graphql"):
        return any(part.startswith("query=mutation") for part in command)
    return "POST" in command or "DELETE" in command or "PATCH" in command


def write_kind(command: Sequence[str]) -> Any:
    """Name a write command by the script's write kind it reaches; `None` for a read or a dependency write."""
    if not is_write(command):
        return None
    if tuple(command[1:3]) == ("api", "graphql"):
        field_id = next(
            part for part in command if part.startswith("field=")
        ).removeprefix("field=F_")
        return FIELD_WRITES[field_id]
    if tuple(command[1:3]) == ("issue", "edit"):
        return WriteKind.ASSIGNEE
    if tuple(command[1:3]) == ("issue", "comment"):
        return WriteKind.COMMENT
    if tuple(command[1:3]) == ("issue", "close"):
        return WriteKind.STATE
    return None


def identity(session: str = SESSION) -> dict[str, str]:
    return asdict(
        script.Identity(
            login=LOGIN,
            harness=HARNESS,
            session=session,
            machine=MACHINE,
            worktree=WORKTREE,
        )
    )


def change_fields(
    maturity: str,
    lifecycle: str,
    base: str | None = None,
    parent: int | None = None,
) -> dict[str, Any]:
    """The organization issue fields a Change issue holds."""
    found: dict[str, Any] = {
        Field.MATURITY.value: str(maturity),
        Field.LIFECYCLE.value: str(lifecycle),
    }
    if base is not None:
        found[Field.BASE.value] = base
    if parent is not None:
        found[Field.PARENT.value] = parent
    return found


def claim_block(session: str = SESSION, maturity: str = Maturity.APPLICABLE) -> str:
    """A claim comment as a claim of `session` posts it."""
    ids = identity(session)
    entries = {
        LogKey.TRANSITION.value: Transition.CLAIM.value,
        LogKey.MATURITY.value: str(maturity),
        LogKey.HARNESS.value: ids[IdentityKey.HARNESS],
        LogKey.SESSION.value: ids[IdentityKey.SESSION],
        LogKey.MACHINE.value: ids[IdentityKey.MACHINE],
        LogKey.WORKTREE.value: ids[IdentityKey.WORKTREE],
    }
    return str(script.render_block(entries))


def held(github: SimulatedGitHub, number: int, session: str = SESSION) -> None:
    """Make `session` the holder of `number`: one assignee and its claim comment."""
    issue = github.issues[number]
    issue.assignees = [LOGIN]
    github.post(
        number,
        claim_block(session, issue.fields.get(Field.MATURITY, Maturity.PROPOSED)),
    )


def request(
    transition: str,
    number: int,
    mover: str,
    session: str = SESSION,
    **values: Any,
) -> dict[str, Any]:
    unknown = set(values) - {key.value for key in RequestKey}
    if unknown:
        raise ValueError(f"not request keys: {sorted(unknown)}")
    return {
        RequestKey.TRANSITION.value: str(transition),
        RequestKey.STORE.value: STORE,
        RequestKey.NUMBER.value: number,
        RequestKey.MOVER.value: str(mover),
        RequestKey.IDENTITY.value: identity(session),
        **values,
    }


def bound_pair(github: SimulatedGitHub, number: int = 10) -> dict[str, str]:
    """The pair a review or an audit reads: the current body revision and Base."""
    issue = github.issues[number]
    return asdict(
        script.BoundPair(
            body_sha256=sha256(issue.body), base=str(issue.fields[Field.BASE])
        )
    )


def pair_of(body: str, base: str) -> dict[str, str]:
    """The pair a review or an audit read for a body text and a Base."""
    return asdict(script.BoundPair(body_sha256=sha256(body), base=base))


def close_check(**overrides: Any) -> dict[str, Any]:
    """A close check that meets the close condition, with `overrides` applied."""
    found = asdict(
        script.CloseCheck(
            merge_gates_passed=True,
            results_complete=True,
            declarations_on_default=True,
            audit_at_close=APPROVED,
        )
    )
    return {**found, **overrides}


def changeset(merge_commit: str = MERGE_COMMIT) -> dict[str, str]:
    """A Changeset naming the merge commit."""
    return {
        ChangesetKey.URL.value: f"https://github.com/{PRODUCT_REPOSITORY}/pull/7",
        ChangesetKey.MERGE_COMMIT.value: merge_commit,
    }


def handoff(**overrides: str) -> dict[str, str]:
    """A Handoff holding the branch, the head commit, and the next subsection."""
    return {
        HandoffKey.BRANCH.value: "work/example",
        HandoffKey.HEAD.value: "d" * 40,
        HandoffKey.NEXT.value: "spx/20-example.enabler/example.md",
        **overrides,
    }


def passing_form_check(github: SimulatedGitHub, number: int = 10) -> dict[str, str]:
    """The form check's pass result for the current body revision."""
    return {FORM_STATUS: FORM_PASS, FORM_BODY: sha256(github.issues[number].body)}


def failing_form_check(github: SimulatedGitHub, number: int = 10) -> dict[str, str]:
    """The form check's fail result for the current body revision."""
    return {FORM_STATUS: FORM_FAIL, FORM_BODY: sha256(github.issues[number].body)}


def run(
    github: SimulatedGitHub, payload: dict[str, Any], root: str | None = None
) -> dict[str, Any]:
    result: dict[str, Any] = script.transition(payload, run=github, root=root)
    return result


def run_main(
    github: SimulatedGitHub, payload: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    """Run the entry point on one request; return its exit code and its result."""
    sink = io.StringIO()
    code = script.main(io.StringIO(json.dumps(payload)), sink, github)
    return code, json.loads(sink.getvalue())


def sha256(text: str) -> str:
    return str(script.sha256(text))


@contextmanager
def product_repository(
    files_by_commit: Sequence[Mapping[str, str]],
) -> Iterator[tuple[str, list[str]]]:
    """A real git repository holding one commit per mapping of path to text."""
    with TemporaryDirectory() as directory:
        root = Path(directory)

        def git(*args: str) -> str:
            return subprocess.run(
                ["git", "-C", directory, *args],
                capture_output=True,
                text=True,
                check=True,
                env={
                    "GIT_AUTHOR_NAME": "t",
                    "GIT_AUTHOR_EMAIL": "t@t",
                    "GIT_COMMITTER_NAME": "t",
                    "GIT_COMMITTER_EMAIL": "t@t",
                    "PATH": "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin",
                },
            ).stdout.strip()

        git("init", "-q")
        commits: list[str] = []
        for files in files_by_commit:
            for path, text in files.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            git("add", "-A")
            git("commit", "-q", "--allow-empty", "-m", f"commit {len(commits)}")
            commits.append(git("rev-parse", "HEAD"))
        yield directory, commits
