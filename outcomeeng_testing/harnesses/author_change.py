"""Controlled Change store and plugin tree for the `author-change` script.

Backs the ``[test]`` evidence for the script's publishing, record, Draft,
reframe, merge, and form check call rules. The script reaches the Change store
only through its injected command runner, so the harness passes it a
controlled store that answers each `gh` and `git` command the way GitHub
answers it, under the failure-simulation, interaction-protocol, and
time-and-concurrency exceptions of the test methodology. The store keeps the
issues, their field values, assignees, blockers, comments, and body edit
history, and it can land a foreign body revision at a chosen moment of the
script's run or drop a field write.

The script reaches the form check and the transition function by
`__file__`-relative imports of sibling skills, so the harness copies the
script into a temporary plugin tree beside controlled stand-ins for those two
skills and runs the copy. The stand-ins hand each request they receive to the
harness bridge, which records it with the store's write log in one ordered
event list and applies the effect of a Transition to the store. Whether the
form check passes, and what the stand-in for the transition function answers,
are values the test supplies.

The harness decides nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import importlib.util
import io
import json
import shutil
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, Final

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SKILLS: Final = REPO_ROOT / "src" / "plugins" / "product-tree" / "skills"
SCRIPT: Final = SKILLS / "author-change" / "scripts" / "author_change.py"
FIXTURES: Final = REPO_ROOT / "outcomeeng_testing" / "fixtures" / "author_change"

STORE_IDENTITY: Final = "example-org/example-changes"
DEFAULT_BRANCH_HEAD: Final = "2222222222222222222222222222222222222222"

#: Vocabulary of the `gh` command line and of GitHub's REST and GraphQL
#: interfaces, which `gh` and GitHub own.
GH: Final = "gh"
GIT: Final = "git"
GH_API: Final = "api"
GH_GRAPHQL: Final = "graphql"
GH_ISSUE: Final = "issue"
GH_EDIT: Final = "edit"
GH_CREATE: Final = "create"
GH_METHOD_FLAG: Final = "--method"
GH_BODY_FILE_FLAG: Final = "--body-file"
GH_TITLE_FLAG: Final = "--title"
GH_ADD_ASSIGNEE_FLAG: Final = "--add-assignee"
GH_FIELD_FLAGS: Final = ("-f", "-F")
GRAPHQL_MUTATION: Final = "mutation"
GRAPHQL_ORGANIZATION: Final = "organization(login"
BLOCKED_BY_SEGMENT: Final = "/dependencies/blocked_by"
SINGLE_SELECT_FIELDS: Final = frozenset(
    {"Product", "Maturity", "Lifecycle", "Priority", "Value", "Investment"}
)
NUMBER_FIELDS: Final = frozenset({"Parent"})


class Stub(StrEnum):
    """The sibling skills the harness stands in for, with their module files."""

    FORM_CHECK_SKILL = "change-standards"
    FORM_CHECK_MODULE = "form_check.py"
    TRANSITION_SKILL = "operate-change"
    TRANSITION_MODULE = "operate_change.py"


class EventKind(StrEnum):
    READ = "read"
    FORM_CHECK = "form-check"
    TRANSITION = "transition"
    EDIT = "edit"
    FIELD = "field"
    BLOCKER_ADD = "blocker-add"
    BLOCKER_REMOVE = "blocker-remove"
    CREATE = "create"
    ASSIGNEE = "assignee"
    GIT = "git"


WRITE_KINDS: Final = frozenset(
    {
        EventKind.EDIT,
        EventKind.FIELD,
        EventKind.BLOCKER_ADD,
        EventKind.BLOCKER_REMOVE,
        EventKind.CREATE,
        EventKind.ASSIGNEE,
        EventKind.TRANSITION,
    }
)


class Moment(StrEnum):
    """When a foreign body revision lands in the script's run."""

    BEFORE_SECOND_READ = "before-second-read"
    BEFORE_WRITE = "before-write"
    AFTER_WRITE = "after-write"


@dataclass(frozen=True)
class Interference:
    """A foreign body revision the store lands at one moment of the run."""

    moment: Moment
    body: str


@dataclass
class Event:
    sequence: int
    kind: EventKind
    detail: dict[str, Any]


@dataclass
class Issue:
    number: int
    title: str
    body: str
    fields: dict[str, Any] = field(default_factory=dict)
    assignees: list[str] = field(default_factory=list)
    blockers: list[int] = field(default_factory=list)
    comments: list[dict[str, Any]] = field(default_factory=list)
    edits: list[tuple[str, str]] = field(default_factory=list)
    open: bool = True

    @property
    def node_id(self) -> str:
        return f"I_{self.number}"

    @property
    def database_id(self) -> int:
        return 1000 + self.number


ORGANIZATION_FIELDS: Final = {
    "Product": ("example",),
    "Maturity": ("Proposed", "Framed", "Sliced", "Applicable"),
    "Lifecycle": ("Submitted", "Available", "Applied", "Abandoned"),
    "Priority": ("Urgent", "Normal"),
    "Value": ("Quality", "Capability"),
    "Investment": ("Harvest", "Seed"),
    "Parent": (),
    "Predecessors": (),
    "Base": (),
}


class Store:
    """The Change store: issues, fields, blockers, comments, and body edits."""

    def __init__(self) -> None:
        self.issues: dict[int, Issue] = {}
        self.events: list[Event] = []
        self.interference: Interference | None = None
        self.dropped_fields: frozenset[str] = frozenset()
        self.default_branch_head: str = DEFAULT_BRANCH_HEAD
        self.read_counts: dict[int, int] = {}
        self.checks_started = 0
        self._edit_counter = 0
        self._next_number = 100
        self._sequence = 0

    # --- arrangement -----------------------------------------------------
    def seed(
        self,
        number: int,
        title: str,
        body: str,
        fields: Mapping[str, Any],
        blockers: Sequence[int] = (),
        assignees: Sequence[str] = (),
    ) -> Issue:
        issue = Issue(
            number=number,
            title=title,
            body=body,
            fields=dict(fields),
            blockers=list(blockers),
            assignees=list(assignees),
        )
        self.issues[number] = issue
        return issue

    def log(self, kind: EventKind, **detail: Any) -> None:
        self._sequence += 1
        self.events.append(Event(self._sequence, kind, detail))

    def new_edit_id(self) -> str:
        self._edit_counter += 1
        return f"E{self._edit_counter}"

    def land(self, issue: Issue, body: str) -> None:
        issue.body = body
        issue.edits.insert(0, (self.new_edit_id(), body))

    # --- the command runner the script receives ---------------------------
    def runner(self, arguments: Sequence[str]) -> Any:
        from outcomeeng_testing.harnesses.author_change import Result

        argv = list(arguments)
        program = argv[0]
        if program == GIT:
            self.log(EventKind.GIT, argv=argv)
            return Result(0, self.default_branch_head + "\n", "")
        assert program == GH
        rest = argv[1:]
        if rest[0] == GH_API and rest[1] == GH_GRAPHQL:
            return self._graphql(rest)
        if rest[0] == GH_API:
            return self._rest(rest)
        assert rest[0] == GH_ISSUE
        if rest[1] == GH_EDIT:
            return self._edit(rest)
        return self._create(rest)

    # --- GraphQL ----------------------------------------------------------
    def _variables(self, rest: Sequence[str]) -> dict[str, str]:
        variables: dict[str, str] = {}
        for index, token in enumerate(rest):
            if token in GH_FIELD_FLAGS:
                name, _, value = rest[index + 1].partition("=")
                variables[name] = value
        return variables

    def _graphql(self, rest: Sequence[str]) -> Any:
        from outcomeeng_testing.harnesses.author_change import Result

        variables = self._variables(rest)
        query = variables["query"]
        if GRAPHQL_ORGANIZATION in query:
            return Result(0, json.dumps(self._organization_answer()), "")
        if query.startswith(GRAPHQL_MUTATION):
            return self._set_field(variables)
        return Result(0, json.dumps(self._issue_answer(int(variables["n"]))), "")

    def _organization_answer(self) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        for name, options in ORGANIZATION_FIELDS.items():
            node: dict[str, Any] = {"id": f"IF_{name}", "name": name}
            if name in SINGLE_SELECT_FIELDS:
                node["options"] = [
                    {"id": f"IFO_{name}_{option}", "name": option} for option in options
                ]
            nodes.append(node)
        return {"data": {"organization": {"issueFields": {"nodes": nodes}}}}

    def _issue_answer(self, number: int) -> dict[str, Any]:
        count = self.read_counts.get(number, 0) + 1
        self.read_counts[number] = count
        issue = self.issues[number]
        interference = self.interference
        if (
            interference is not None
            and interference.moment == Moment.BEFORE_SECOND_READ
            and count == 2
        ):
            self.land(issue, interference.body)
        self.log(EventKind.READ, number=number, count=count)
        values: list[dict[str, Any]] = []
        for name, value in issue.fields.items():
            if value is None:
                continue
            if name in SINGLE_SELECT_FIELDS:
                values.append({"name": value, "field": {"name": name}})
            else:
                values.append({"value": value, "field": {"name": name}})
        return {
            "data": {
                "repository": {
                    "issue": {
                        "id": issue.node_id,
                        "number": number,
                        "title": issue.title,
                        "body": issue.body,
                        "url": f"https://github.com/{STORE_IDENTITY}/issues/{number}",
                        "assignees": {"nodes": [{"login": a} for a in issue.assignees]},
                        "userContentEdits": {
                            "nodes": [
                                {"id": identifier, "diff": diff}
                                for identifier, diff in issue.edits[:5]
                            ]
                        },
                        "issueFieldValues": {"nodes": values},
                    }
                }
            }
        }

    def _set_field(self, variables: Mapping[str, str]) -> Any:
        from outcomeeng_testing.harnesses.author_change import Result

        issue = next(i for i in self.issues.values() if i.node_id == variables["i"])
        name = variables["f"].removeprefix("IF_")
        raw = variables["v"]
        if name in SINGLE_SELECT_FIELDS:
            value: Any = raw.removeprefix(f"IFO_{name}_")
        elif name in NUMBER_FIELDS:
            value = float(raw)
        else:
            value = raw
        self.log(EventKind.FIELD, number=issue.number, name=name, value=value)
        if name not in self.dropped_fields:
            issue.fields[name] = value if value != "" else None
        return Result(0, json.dumps({"data": {"setIssueFieldValue": {}}}), "")

    # --- REST -------------------------------------------------------------
    def _rest(self, rest: Sequence[str]) -> Any:
        from outcomeeng_testing.harnesses.author_change import Result

        path = rest[1]
        _, _, tail = path.partition(f"repos/{STORE_IDENTITY}/issues/")
        number = int(tail.split("/")[0])
        if BLOCKED_BY_SEGMENT in path:
            method = rest[rest.index(GH_METHOD_FLAG) + 1]
            issue = self.issues[number]
            if method == "GET":
                entries = [
                    {
                        "number": blocker,
                        "id": self.issues[blocker].database_id,
                        "html_url": f"https://github.com/{STORE_IDENTITY}/issues/{blocker}",
                    }
                    for blocker in issue.blockers
                ]
                return Result(0, json.dumps(entries), "")
            if method == "POST":
                database_id = int(self._variables(rest)["issue_id"])
                blocker = next(
                    i.number
                    for i in self.issues.values()
                    if i.database_id == database_id
                )
                issue.blockers.append(blocker)
                self.log(EventKind.BLOCKER_ADD, number=number, blocker=blocker)
                return Result(0, "{}", "")
            database_id = int(path.rsplit("/", 1)[1])
            blocker = next(
                i.number for i in self.issues.values() if i.database_id == database_id
            )
            issue.blockers.remove(blocker)
            self.log(EventKind.BLOCKER_REMOVE, number=number, blocker=blocker)
            return Result(0, "{}", "")
        return Result(0, f"{self.issues[number].database_id}\n", "")

    # --- gh issue edit and create ----------------------------------------
    def _edit(self, rest: Sequence[str]) -> Any:
        from outcomeeng_testing.harnesses.author_change import Result

        number = int(rest[2])
        issue = self.issues[number]
        interference = self.interference
        if GH_ADD_ASSIGNEE_FLAG in rest:
            issue.assignees.append(rest[rest.index(GH_ADD_ASSIGNEE_FLAG) + 1])
            self.log(EventKind.ASSIGNEE, number=number)
            return Result(0, "", "")
        if (
            interference is not None
            and interference.moment == Moment.BEFORE_WRITE
            and GH_BODY_FILE_FLAG in rest
        ):
            self.land(issue, interference.body)
        detail: dict[str, Any] = {"number": number}
        if GH_TITLE_FLAG in rest:
            issue.title = rest[rest.index(GH_TITLE_FLAG) + 1]
            detail["title"] = issue.title
        if GH_BODY_FILE_FLAG in rest:
            body = Path(rest[rest.index(GH_BODY_FILE_FLAG) + 1]).read_text(
                encoding="utf-8"
            )
            self.land(issue, body)
            detail["body"] = body
            if interference is not None and interference.moment == Moment.AFTER_WRITE:
                self.land(issue, interference.body)
        self.log(EventKind.EDIT, **detail)
        return Result(0, "", "")

    def _create(self, rest: Sequence[str]) -> Any:
        from outcomeeng_testing.harnesses.author_change import Result

        number = self._next_number
        self._next_number += 1
        title = rest[rest.index(GH_TITLE_FLAG) + 1]
        body = Path(rest[rest.index(GH_BODY_FILE_FLAG) + 1]).read_text(encoding="utf-8")
        issue = self.seed(number, title, body, {})
        self.land(issue, body)
        self.log(EventKind.CREATE, number=number, title=title, body=body)
        return Result(0, f"https://github.com/{STORE_IDENTITY}/issues/{number}\n", "")

    # --- effect of a Transition ------------------------------------------
    def apply_transition(self, request: Mapping[str, Any]) -> None:
        issue = self.issues[int(request["number"])]
        if request["transition"] == "lower":
            issue.fields["Maturity"] = request["target"]
        else:
            issue.fields["Lifecycle"] = "Abandoned"
            issue.open = False
        issue.comments.append(dict(request))


@dataclass
class Result:
    """What one command the store answered returned; the script's shape."""

    returncode: int
    stdout: str
    stderr: str


@dataclass
class Bridge:
    """What the stand-in sibling skills hand to the harness."""

    store: Store
    checkout_root: Path
    form_check_result: dict[str, Any]
    transition_result: dict[str, Any]
    check_requests: list[dict[str, Any]] = field(default_factory=list)
    check_roots_before: list[tuple[str, ...]] = field(default_factory=list)
    check_writes_before: list[int] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)

    def form_check(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.store.checks_started += 1
        self.check_requests.append(json.loads(json.dumps(request)))
        self.check_roots_before.append(
            tuple(sorted(path.name for path in self.checkout_root.iterdir()))
        )
        self.check_writes_before.append(
            sum(1 for event in self.store.events if event.kind in WRITE_KINDS)
        )
        self.store.log(EventKind.FORM_CHECK, operation=request.get("operation"))
        return self.form_check_result

    def transition(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.transitions.append(json.loads(json.dumps(request)))
        self.store.log(
            EventKind.TRANSITION,
            number=request["number"],
            transition=request["transition"],
        )
        if self.transition_result.get("status") == "done":
            self.store.apply_transition(request)
        return self.transition_result


_BRIDGE: Bridge | None = None


def bridge() -> Bridge:
    assert _BRIDGE is not None
    return _BRIDGE


_FORM_CHECK_SOURCE: Final = '''"""Controlled stand-in for the form check of the change-standards skill."""

from outcomeeng_testing.harnesses.author_change import bridge


def check(request, run=None):
    return bridge().form_check(request)
'''
_TRANSITION_SOURCE: Final = '''"""Controlled stand-in for the transition function of the operate-change skill."""

from outcomeeng_testing.harnesses.author_change import bridge


def transition(request, store=None, *, run=None, root=None):
    return bridge().transition(request)
'''


@dataclass
class Observation:
    exit_code: int
    result: dict[str, Any]
    store: Store
    bridge: Bridge
    calls: list[list[str]]
    checkout_entries_after: tuple[str, ...]


def build_plugin_tree(
    root: Path, with_form_check: bool = True, with_transition: bool = True
) -> Path:
    """Copy the script into a temporary plugin tree beside the stand-ins."""
    scripts = root / "skills" / "author-change" / "scripts"
    scripts.mkdir(parents=True)
    copied = scripts / SCRIPT.name
    shutil.copy(SCRIPT, copied)
    if with_form_check:
        directory = root / "skills" / Stub.FORM_CHECK_SKILL / "scripts"
        directory.mkdir(parents=True)
        (directory / Stub.FORM_CHECK_MODULE).write_text(_FORM_CHECK_SOURCE)
    if with_transition:
        directory = root / "skills" / Stub.TRANSITION_SKILL / "scripts"
        directory.mkdir(parents=True)
        (directory / Stub.TRANSITION_MODULE).write_text(_TRANSITION_SOURCE)
    return copied


def load_copied_script(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("author_change_copied", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_script() -> ModuleType:
    """The script as authored, for its exported vocabulary."""
    spec = importlib.util.spec_from_file_location("author_change_source", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_script(
    request_for: Callable[[Path], Mapping[str, Any]],
    store: Store,
    *,
    form_check_result: Mapping[str, Any] | None = None,
    transition_result: Mapping[str, Any] | None = None,
    with_form_check: bool = True,
    with_transition: bool = True,
) -> Observation:
    """Run a copy of the script against the store and observe the run.

    `request_for` receives the checkout root the harness provisions and returns
    the request the script reads on stdin.
    """
    global _BRIDGE
    with TemporaryDirectory() as scratch:
        tree = Path(scratch) / "plugin"
        checkout = Path(scratch) / "checkout"
        checkout.mkdir()
        copied = build_plugin_tree(tree, with_form_check, with_transition)
        module = load_copied_script(copied)
        _BRIDGE = Bridge(
            store=store,
            checkout_root=checkout,
            form_check_result=dict(
                form_check_result or {"status": "pass", "findings": []}
            ),
            transition_result=dict(transition_result or {"status": "done"}),
        )
        calls: list[list[str]] = []

        def recording_runner(arguments: Sequence[str]) -> Any:
            calls.append(list(arguments))
            return store.runner(arguments)

        stdout = io.StringIO()
        exit_code = module.main(
            stdin=io.StringIO(json.dumps(request_for(checkout))),
            stdout=stdout,
            run=recording_runner,
        )
        observed_bridge = _BRIDGE
        _BRIDGE = None
        return Observation(
            exit_code=exit_code,
            result=json.loads(stdout.getvalue()),
            store=store,
            bridge=observed_bridge,
            calls=calls,
            checkout_entries_after=tuple(
                sorted(path.name for path in checkout.iterdir())
            ),
        )
