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
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
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


@dataclass
class Issue:
    """One Change issue as the simulated store holds it."""

    number: int
    body: str
    fields: dict[str, Any]
    state: str = "OPEN"
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

    def add(self, number: int, body: str, **fields: Any) -> Issue:
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
        script = load_script()
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
                issue.state = "CLOSED"
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
                "Maturity": ("Proposed", "Framed", "Sliced", "Applicable"),
                "Lifecycle": ("Submitted", "Available", "Applied", "Abandoned"),
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
        parent = issue.fields.get("Parent")
        values = (
            []
            if parent is None
            else [{"value": float(parent), "field": {"name": "Parent"}}]
        )
        return {
            "number": issue.number,
            "state": issue.state,
            "issueFieldValues": {"nodes": values},
        }

    def _state_node(self, issue: Issue) -> dict[str, Any]:
        values: list[dict[str, Any]] = []
        for name, value in issue.fields.items():
            if name in ("Maturity", "Lifecycle"):
                values.append({"name": value, "field": {"name": name}})
            elif name == "Parent":
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


def write_kind(command: Sequence[str]) -> str:
    """Name a write command by the part of the store it reaches."""
    if tuple(command[1:3]) == ("api", "graphql"):
        field_id = next(
            part for part in command if part.startswith("field=")
        ).removeprefix("field=F_")
        return field_id.lower()
    if tuple(command[1:3]) == ("issue", "edit"):
        return "assignee"
    if tuple(command[1:3]) == ("issue", "comment"):
        return "comment"
    if tuple(command[1:3]) == ("issue", "close"):
        return "state"
    return "dependency"


def identity(session: str = SESSION) -> dict[str, str]:
    return {
        "login": LOGIN,
        "harness": HARNESS,
        "session": session,
        "machine": MACHINE,
        "worktree": WORKTREE,
    }


def claim_block(session: str = SESSION, maturity: str = "Applicable") -> str:
    """A claim comment as a claim of `session` posts it."""
    script = load_script()
    entries = {
        "transition": "claim",
        "maturity": maturity,
        "harness": HARNESS,
        "session": session,
        "machine": MACHINE,
        "worktree": WORKTREE,
    }
    return str(script.render_block(entries))


def held(github: SimulatedGitHub, number: int, session: str = SESSION) -> None:
    """Make `session` the holder of `number`: one assignee and its claim comment."""
    issue = github.issues[number]
    issue.assignees = [LOGIN]
    github.post(number, claim_block(session, issue.fields.get("Maturity", "Proposed")))


def request(transition: str, number: int, mover: str, **values: Any) -> dict[str, Any]:
    return {
        "transition": transition,
        "store": STORE,
        "number": number,
        "mover": mover,
        "identity": identity(values.pop("session", SESSION)),
        **values,
    }


def run(
    github: SimulatedGitHub, payload: dict[str, Any], root: str | None = None
) -> dict[str, Any]:
    script = load_script()
    result: dict[str, Any] = script.transition(payload, run=github, root=root)
    return result


def run_main(
    github: SimulatedGitHub, payload: dict[str, Any]
) -> tuple[int, dict[str, Any]]:
    """Run the entry point on one request; return its exit code and its result."""
    script = load_script()
    sink = io.StringIO()
    code = script.main(io.StringIO(json.dumps(payload)), sink, github)
    return code, json.loads(sink.getvalue())


def sha256(text: str) -> str:
    return str(load_script().sha256(text))


@contextmanager
def product_repository(
    files_by_commit: Sequence[dict[str, str]],
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
