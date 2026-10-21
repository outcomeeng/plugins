"""Replay harness for the `report-changes` script.

Backs the ``[test]`` evidence for the report's rows, mappings, blocked
results, and read-only behavior. The script reaches the Change store only
through its injected command runner, so the harness passes it a replaying
collaborator that answers each `gh` command with the store's answer for it,
under the interaction-protocol and failure-simulation exceptions of the test
methodology. The script's output stream is a string sink the harness reads
back, and the entry point runs in this process from one empty working
directory under an audit-hook ``Recorder``, so a file the script wrote
anywhere shows in the observation.

A replayed store is either an inert fixture file under
``outcomeeng_testing/fixtures/report_changes``, written with invented
identities because the Change store is private and this repository is public,
or a generated store from ``outcomeeng_testing.generators.report_changes``
rendered into the store's answer shapes here. A fixture holds the store's
``pages`` in reading order, the REST ``blockers``, the ``comments``, and the field-change ``events`` per
issue number, the pull request ``checks`` per URL, and ``direct``, the rows
read by hand from those answers. The collaborator answers the first store
call with the first page and each later one with the page that follows the
page whose ``endCursor`` the call passes as ``after``; once the pages run out
it answers with the final page again, which is what a store that never ends
its connection does.

The bounds a blocked result names come from the spec assertion text, read here
by path. The harness decides nothing: every predicate belongs to the linked
test.
"""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import re
import sys
import threading
from collections.abc import Callable, Sequence
from contextlib import chdir
from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng_testing.generators.report_changes import (
    GeneratedIssue,
    GeneratedStore,
    stores,
)
from outcomeeng_testing.harnesses import audit_change_run_observer as observer
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SCRIPT: Final = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "report-changes"
    / "scripts"
    / "report_changes.py"
)
CHANGES_SPEC: Final = (
    REPO_ROOT / "spx" / "31-outcomeeng.enabler" / "32-changes.enabler" / "changes.md"
)
_FIXTURES_DIR: Final = REPO_ROOT / "outcomeeng_testing" / "fixtures" / "report_changes"
#: A multi-page store holding a Change in each waiting state, a Parent cycle,
#: and an absent Parent, with the rows read by hand from its answers.
RECORDED_STORE: Final = _FIXTURES_DIR / "store.json"

#: The invented store every generated store claims to be.
GENERATED_STORE_IDENTITY: Final = "example-org/example-changes"
#: The invented repository every generated blocker names as its home.
_REST_REPOSITORY_URL: Final = f"https://api.github.com/repos/{GENERATED_STORE_IDENTITY}"

#: Vocabulary of the `gh` command line and of GraphQL, which `gh` and GitHub own.
GH_API: Final = "api"
GH_GRAPHQL: Final = "graphql"
GH_ISSUE: Final = "issue"
GH_PULL_REQUEST: Final = "pr"
GH_VIEW: Final = "view"
GH_METHOD_FLAG: Final = "--method"
GH_READ_METHOD: Final = "GET"
GRAPHQL_WRITE_OPERATION: Final = "mutation"
_QUERY_PREFIX: Final = "query="
_AFTER_PREFIX: Final = "after="
_NUMBER_PREFIX: Final = "n="
_BLOCKERS_PATH: Final = re.compile(r"issues/(\d+)/dependencies/blocked_by$")

#: Property run configuration for generated stores.
GENERATED_STORE_PROPERTY_SEED: Final = 20261021
GENERATED_STORE_PROPERTY_EXAMPLES: Final = settings().max_examples
GENERATED_STORE_PROPERTY_REPLAY: Final = (
    "just test spx/31-outcomeeng.enabler/32-changes.enabler/tests/"
    "test_report_changes.property.l1.py"
)

_BOUND_LINE: Final = "returns a shorter list in place of a failure"
_BOUND_PHRASE: Final = re.compile(r"`(\d+ [^`]+)`")
_FIRST_INTEGER: Final = re.compile(r"\d+")

_SIMULATED_FAILURE: Final = "simulated failure"
_SIMULATED_UNREADABLE: Final = "this is not JSON"
_UNENDING_CURSOR: Final = "cursor-that-never-ends"

_script_module: ModuleType | None = None


def load_script() -> ModuleType:
    """Load the shipped script module by path, once per session."""
    global _script_module
    if _script_module is None:
        spec = importlib.util.spec_from_file_location("report_changes", SCRIPT)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load the report-changes script from {SCRIPT}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["report_changes"] = module
        spec.loader.exec_module(module)
        _script_module = module
    return _script_module


class ReadKind(StrEnum):
    """The kinds of read the script makes of the store."""

    STORE = "store"
    BLOCKERS = "blockers"
    COMMENTS = "comments"
    EVENTS = "events"
    CHECKS = "checks"


class FaultKind(StrEnum):
    """The ways a read can fail."""

    NONZERO_EXIT = "nonzero_exit"
    UNREADABLE_OUTPUT = "unreadable_output"
    CANNOT_START = "cannot_start"


@dataclass(frozen=True)
class Fault:
    """Make every read of one kind fail in one way."""

    read: ReadKind
    kind: FaultKind


@dataclass(frozen=True)
class ReplayedStore:
    """What the store answers, and the rows read by hand from those answers."""

    store: str
    priority_order: tuple[str, ...]
    pages: list[dict[str, object]]
    blockers: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    comments: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    events: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    checks: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    direct: list[dict[str, object]] = field(default_factory=list)
    #: Whether every page of an issue's field-change events reports a further page.
    events_never_end: bool = False


@dataclass(frozen=True)
class GhCall:
    """One `gh` command line the script issued."""

    argv: tuple[str, ...]

    @property
    def command(self) -> str:
        return self.argv[0]

    @property
    def verb(self) -> str | None:
        """The word after the command, for `gh api`, `gh issue`, and `gh pr`."""
        return self.argv[1] if len(self.argv) > 1 else None

    @property
    def graphql_query(self) -> str | None:
        """The GraphQL query text the call sends, when it is a GraphQL call."""
        if self.command != GH_API or self.verb != GH_GRAPHQL:
            return None
        return next(
            (
                arg.removeprefix(_QUERY_PREFIX)
                for arg in self.argv
                if arg.startswith(_QUERY_PREFIX)
            ),
            None,
        )

    @property
    def rest_method(self) -> str | None:
        """The HTTP method a `gh api` REST call names, ``None`` when it names none."""
        if self.command != GH_API or self.verb == GH_GRAPHQL:
            return None
        if GH_METHOD_FLAG not in self.argv:
            return None
        return self.argv[self.argv.index(GH_METHOD_FLAG) + 1]


@dataclass(frozen=True)
class ReportObservation:
    """What one run of the script returned, issued, and wrote."""

    exit_code: int
    #: The JSON document the script printed on its output stream.
    result: dict[str, object]
    calls: tuple[GhCall, ...]
    #: Every filesystem mutation the script performed, as ``(event, path)``.
    writes: tuple[tuple[str, ...], ...]
    #: The entries in the working directory after the run.
    working_directory_entries: tuple[str, ...]

    @property
    def event_page_calls(self) -> tuple[GhCall, ...]:
        """The calls that read a page of an issue's field-change events."""
        return tuple(
            call
            for call in self.calls
            if call.graphql_query == load_script().EVENT_QUERY
        )

    @property
    def store_page_calls(self) -> tuple[GhCall, ...]:
        """The calls that read a page of the store's issues."""
        return tuple(
            call
            for call in self.calls
            if call.graphql_query == load_script().STORE_QUERY
        )


@dataclass(frozen=True)
class SpecBounds:
    """The bounds the spec assertion says a blocked result names."""

    issues: str
    field_values: str
    blockers: str
    assignees: str
    events: str

    @property
    def page_count(self) -> int:
        return int(_FIRST_INTEGER.findall(self.issues)[-1])

    @property
    def field_value_count(self) -> int:
        return int(_FIRST_INTEGER.findall(self.field_values)[0])

    @property
    def blocker_count(self) -> int:
        return int(_FIRST_INTEGER.findall(self.blockers)[0])

    @property
    def assignee_count(self) -> int:
        return int(_FIRST_INTEGER.findall(self.assignees)[0])

    @property
    def event_page_count(self) -> int:
        return int(_FIRST_INTEGER.findall(self.events)[-1])


def spec_bounds() -> SpecBounds:
    """The five bounds named in the spec assertion that forbids a shorter list."""
    line = next(
        text
        for text in CHANGES_SPEC.read_text(encoding="utf-8").splitlines()
        if _BOUND_LINE in text
    )
    issues, field_values, blockers, assignees, events = _BOUND_PHRASE.findall(line)
    return SpecBounds(
        issues=issues,
        field_values=field_values,
        blockers=blockers,
        assignees=assignees,
        events=events,
    )


def load_recorded_store(path: Path = RECORDED_STORE) -> ReplayedStore:
    """Read a recorded store fixture by path."""
    document = json.loads(path.read_text(encoding="utf-8"))
    return ReplayedStore(
        store=document["store"],
        priority_order=tuple(document["priority_order"]),
        pages=document["pages"],
        blockers=document["blockers"],
        comments=document["comments"],
        events=document["events"],
        checks=document["checks"],
        direct=document["direct"],
    )


def unending_issues(store: ReplayedStore) -> ReplayedStore:
    """The store whose issue connection never reports its last page."""
    page = copy.deepcopy(store.pages[0])
    info = page["data"]["repository"]["issues"]["pageInfo"]  # type: ignore[index]
    info["hasNextPage"] = True
    info["endCursor"] = _UNENDING_CURSOR
    return replace(store, pages=[page])


def filled_field_values(store: ReplayedStore, count: int) -> ReplayedStore:
    """The store whose first issue returns ``count`` field values."""
    pages = copy.deepcopy(store.pages)
    nodes = pages[0]["data"]["repository"]["issues"]["nodes"][0]["issueFieldValues"][  # type: ignore[index]
        "nodes"
    ]
    nodes[:] = [nodes[0]] * count
    return replace(store, pages=pages)


def filled_assignees(store: ReplayedStore, count: int) -> ReplayedStore:
    """The store whose first issue returns ``count`` assignees."""
    pages = copy.deepcopy(store.pages)
    assignees = pages[0]["data"]["repository"]["issues"]["nodes"][0]["assignees"][  # type: ignore[index]
        "nodes"
    ]
    assignees[:] = [{"login": f"assignee-{index}"} for index in range(count)]
    return replace(store, pages=pages)


def unending_events(store: ReplayedStore) -> ReplayedStore:
    """The store whose field-change event timelines never report their last page."""
    return replace(store, events_never_end=True)


def filled_blockers(store: ReplayedStore, count: int) -> ReplayedStore:
    """The store whose blocked issue returns ``count`` blockers on its one page."""
    blockers = copy.deepcopy(store.blockers)
    for number, entries in blockers.items():
        blockers[number] = [entries[0]] * count
    return replace(store, blockers=blockers)


@dataclass(frozen=True)
class OmittedPriority:
    """A store whose Priority order omits a Priority one open Change holds."""

    store: ReplayedStore
    #: The Priority the order omits.
    priority: str
    #: The first open Change, in reading order, that holds it.
    number: int


def omitting_a_held_priority(store: ReplayedStore) -> OmittedPriority:
    """The store whose Priority order drops the Priority of its first open Change that holds one."""
    script = load_script()
    for page in store.pages:
        for node in page["data"]["repository"]["issues"]["nodes"]:  # type: ignore[index]
            if node["state"] != script.IssueState.OPEN:
                continue
            for entry in node["issueFieldValues"]["nodes"]:
                if entry["field"]["name"] == script.FIELD_PRIORITY:
                    order = tuple(
                        name for name in store.priority_order if name != entry["name"]
                    )
                    return OmittedPriority(
                        store=replace(store, priority_order=order),
                        priority=entry["name"],
                        number=node["number"],
                    )
    raise LookupError("the store holds no open Change with a Priority")


def render_generated(generated: GeneratedStore) -> ReplayedStore:
    """Render a generated store into the store's answer shapes."""
    script = load_script()

    def entries(issue: GeneratedIssue) -> list[dict[str, object]]:
        values: list[dict[str, object]] = []
        for name, value in (
            (script.FIELD_PRODUCT, issue.product),
            (script.FIELD_MATURITY, issue.maturity),
            (script.FIELD_LIFECYCLE, issue.lifecycle),
            (script.FIELD_PRIORITY, issue.priority),
        ):
            if value is not None:
                values.append({"name": value, "field": {"name": name}})
        if issue.parent is not None:
            values.append(
                {"value": issue.parent, "field": {"name": script.FIELD_PARENT}}
            )
        return values

    def node(issue: GeneratedIssue) -> dict[str, object]:
        return {
            "number": issue.number,
            "url": issue.url,
            "title": issue.title,
            "state": issue.state,
            "assignees": {"nodes": [{"login": login} for login in issue.assignees]},
            "issueFieldValues": {"nodes": entries(issue)},
        }

    pages: list[dict[str, object]] = []
    start = 0
    for index, size in enumerate(generated.page_sizes):
        last = index == len(generated.page_sizes) - 1
        pages.append(
            {
                "data": {
                    "repository": {
                        "issues": {
                            "pageInfo": {
                                "hasNextPage": not last,
                                "endCursor": f"cursor-{index}",
                            },
                            "nodes": [
                                node(issue)
                                for issue in generated.issues[start : start + size]
                            ],
                        }
                    }
                }
            }
        )
        start += size
    blockers: dict[str, list[dict[str, object]]] = {
        str(issue.number): [
            {
                "number": number,
                "state": state,
                "state_reason": None,
                "repository_url": _REST_REPOSITORY_URL,
            }
            for number, state in zip(issue.blocker_numbers, issue.blocker_states)
        ]
        for issue in generated.issues
    }
    return ReplayedStore(
        store=GENERATED_STORE_IDENTITY,
        priority_order=generated.request.priority_order,
        pages=pages,
        blockers=blockers,
    )


class _Replay:
    """Answer each `gh` command with the store's answer, or a simulated failure."""

    def __init__(self, replayed: ReplayedStore, fault: Fault | None) -> None:
        self._replayed = replayed
        self._fault = fault
        self.calls: list[GhCall] = []

    def _page_for(self, after: str | None) -> dict[str, object]:
        pages = self._replayed.pages
        position = 0
        if after is not None:
            ends = [
                page["data"]["repository"]["issues"]["pageInfo"]["endCursor"]  # type: ignore[index]
                for page in pages
            ]
            position = ends.index(after) + 1 if after in ends else len(pages)
        return pages[min(position, len(pages) - 1)]

    def _value(self, argv: Sequence[str], prefix: str) -> str | None:
        return next(
            (arg.removeprefix(prefix) for arg in argv if arg.startswith(prefix)),
            None,
        )

    def _answer(self, call: GhCall) -> tuple[ReadKind, object]:
        script = load_script()
        argv = call.argv
        query = call.graphql_query
        if query == script.STORE_QUERY:
            return ReadKind.STORE, self._page_for(self._value(argv, _AFTER_PREFIX))
        if query == script.EVENT_QUERY:
            number = self._value(argv, _NUMBER_PREFIX)
            nodes = self._replayed.events.get(str(number), [])
            timeline = {
                "pageInfo": {
                    "hasNextPage": self._replayed.events_never_end,
                    "endCursor": _UNENDING_CURSOR
                    if self._replayed.events_never_end
                    else None,
                },
                "nodes": nodes,
            }
            return ReadKind.EVENTS, {
                "data": {"repository": {"issue": {"timelineItems": timeline}}}
            }
        if call.command == GH_API and call.verb is not None:
            found = _BLOCKERS_PATH.search(call.verb)
            if found:
                return ReadKind.BLOCKERS, self._replayed.blockers.get(
                    found.group(1), []
                )
        if call.command == GH_ISSUE and call.verb == GH_VIEW:
            return ReadKind.COMMENTS, {
                "comments": self._replayed.comments.get(argv[2], [])
            }
        if call.command == GH_PULL_REQUEST and call.verb == GH_VIEW:
            return ReadKind.CHECKS, {
                "statusCheckRollup": self._replayed.checks.get(argv[2], [])
            }
        raise AssertionError(f"the replay has no answer for {list(argv)}")

    def __call__(self, arguments: Sequence[str]) -> object:
        call = GhCall(tuple(arguments))
        self.calls.append(call)
        kind, answer = self._answer(call)
        script = load_script()
        if self._fault is not None and self._fault.read == kind:
            if self._fault.kind == FaultKind.CANNOT_START:
                raise OSError(_SIMULATED_FAILURE)
            if self._fault.kind == FaultKind.NONZERO_EXIT:
                return script.CommandResult(1, "", _SIMULATED_FAILURE)
            return script.CommandResult(0, _SIMULATED_UNREADABLE, "")
        return script.CommandResult(0, json.dumps(answer), "")


def request_arguments(
    replayed: ReplayedStore,
    *,
    product: str | None = None,
    maturity: str | None = None,
    lifecycle: str | None = None,
    holder: str | None = None,
    blocked: str | None = None,
) -> list[str]:
    """The command line that asks for ``replayed``'s store with the given filters."""
    flag = load_script().Flag
    arguments = [
        flag.STORE,
        replayed.store,
        flag.PRIORITY_ORDER,
        ",".join(replayed.priority_order),
    ]
    for name, value in (
        (flag.PRODUCT, product),
        (flag.MATURITY, maturity),
        (flag.LIFECYCLE, lifecycle),
        (flag.HOLDER, holder),
        (flag.BLOCKED, blocked),
    ):
        if value is not None:
            arguments += [name, value]
    return arguments


_recorder: observer.Recorder | None = None


def _entry_point_recorder() -> observer.Recorder:
    global _recorder
    if _recorder is None:
        _recorder = observer.Recorder()
        sys.addaudithook(_recorder)
    return _recorder


def report(
    replayed: ReplayedStore,
    arguments: Sequence[str] | None = None,
    *,
    fault: Fault | None = None,
) -> ReportObservation:
    """Run the script's entry point against ``replayed`` from an empty directory."""
    script = load_script()
    replay = _Replay(replayed, fault)
    sink = io.StringIO()
    recorder = _entry_point_recorder()
    with TemporaryDirectory() as temporary, chdir(temporary):
        recorder.start(thread=threading.get_ident())
        try:
            exit_code = int(
                script.main(
                    list(arguments)
                    if arguments is not None
                    else request_arguments(replayed),
                    runner=replay,
                    stdout=sink,
                )
            )
        finally:
            writes, _spawns = recorder.stop()
        entries = tuple(sorted(path.name for path in Path(temporary).iterdir()))
    return ReportObservation(
        exit_code=exit_code,
        result=json.loads(sink.getvalue()),
        calls=tuple(replay.calls),
        writes=tuple(tuple(write) for write in writes),
        working_directory_entries=entries,
    )


def exercise_generated_stores(
    assert_case: Callable[[GeneratedStore, ReportObservation], None],
) -> None:
    """Report on every generated store and its request.

    ``assert_case`` receives the generated store and what the script returned
    for it; a failing case reports the seed and the replay command.
    """
    script = load_script()

    @seed(GENERATED_STORE_PROPERTY_SEED)
    @settings(max_examples=GENERATED_STORE_PROPERTY_EXAMPLES, print_blob=True)
    @given(generated=stores(script))
    def run_cases(generated: GeneratedStore) -> None:
        replayed = render_generated(generated)
        request = generated.request
        arguments = request_arguments(
            replayed,
            product=request.product,
            maturity=request.maturity,
            lifecycle=request.lifecycle,
            holder=request.holder,
            blocked=request.blocked,
        )
        assert_case(generated, report(replayed, arguments))

    run_replayable_property(
        run_cases,
        seed_value=GENERATED_STORE_PROPERTY_SEED,
        replay_path=GENERATED_STORE_PROPERTY_REPLAY,
    )
