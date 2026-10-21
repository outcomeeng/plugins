"""Report the open Changes of a Change store, read-only.

Reads the store's issues, blockers, comments, field-change events, and linked
pull requests through reading `gh` commands only, and prints one JSON document
on stdout: `{"status": "ok", "rows": [...]}`, or `{"status": "blocked", ...}`
with exit status 3 when a read fails, returns unreadable output, or fills a
bound. The script writes no file, posts no comment, and sets no field,
assignee, or blocker.

The Change store, the Priority order, and the filters arrive as request
values on the command line; the script reads no overlay and no repository
content.

Portability: stdlib only; supports Python 3.13 and later.

Tested with a stub `gh` serving a store of open and closed Changes: no
filter, a blocked filter, a holder filter, a Parent cycle, a Submitted, an
Available-with-blocker, and a Claimed Change with a pull request holding an
unfinished check, a Priority outside the declared order, an invalid
`--maturity`, and a missing `gh`.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, NoReturn

EXIT_OK = 0
EXIT_BLOCKED = 3

PAGE_SIZE = 100
MAX_PAGES = 10
FIELD_VALUE_LIMIT = 50
ASSIGNEE_LIMIT = 100
BLOCKER_LIMIT = 100

MATURITIES = ("Proposed", "Framed", "Sliced", "Executable")
LIFECYCLES = ("Available", "Claimed", "Submitted", "Applied", "Abandoned")

FIELD_PRODUCT = "Product"
FIELD_MATURITY = "Maturity"
FIELD_LIFECYCLE = "Lifecycle"
FIELD_PRIORITY = "Priority"
FIELD_PARENT = "Parent"

STORE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9._-]+$")
PULL_REQUEST_PATTERN = re.compile(r"^https?://[^\s]+/pull/\d+$")
CLAIM_PATTERN = re.compile(r"^Claim: (\S+) (.+)$")

STORE_QUERY = (
    "query($o:String!,$r:String!,$after:String){repository(owner:$o,name:$r){"
    "issues(first:100,after:$after){pageInfo{hasNextPage endCursor} nodes{"
    "number url title state assignees(first:100){nodes{login}} "
    "issueFieldValues(first:50){nodes{"
    "... on IssueFieldSingleSelectValue{name field{... on IssueFieldSingleSelect{name}}} "
    "... on IssueFieldTextValue{value field{... on IssueFieldText{name}}} "
    "... on IssueFieldNumberValue{value field{... on IssueFieldNumber{name}}}"
    "}}}}}}"
)
EVENT_QUERY = (
    "query($o:String!,$r:String!,$n:Int!,$after:String){repository(owner:$o,name:$r){"
    "issue(number:$n){timelineItems(first:100,after:$after,"
    "itemTypes:[ISSUE_FIELD_CHANGED_EVENT]){pageInfo{hasNextPage endCursor} nodes{"
    "... on IssueFieldChangedEvent{createdAt actor{login} previousValue newValue "
    "issueField{... on IssueFieldSingleSelect{name} ... on IssueFieldText{name}}}"
    "}}}}}"
)


class BlockedRead(Exception):
    """A read failed, returned unreadable output, or filled a bound."""

    def __init__(self, read: str, detail: str, bound: str | None = None) -> None:
        super().__init__(detail)
        self.read = read
        self.detail = detail
        self.bound = bound


@dataclass(frozen=True)
class Request:
    owner: str
    repo: str
    priority_order: tuple[str, ...]
    product: str | None
    maturity: str | None
    lifecycle: str | None
    holder: str | None
    blocked: bool | None

    @property
    def store(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass(frozen=True)
class Change:
    number: int
    url: str
    title: str
    state: str
    assignees: tuple[str, ...]
    product: str | None
    maturity: str | None
    lifecycle: str | None
    priority: str | None
    parent: int | None


def emit(document: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(document, indent=2) + "\n")


def emit_blocked(blocked: BlockedRead) -> NoReturn:
    document: dict[str, Any] = {
        "status": "blocked",
        "read": blocked.read,
        "detail": blocked.detail,
    }
    if blocked.bound is not None:
        document["bound"] = blocked.bound
    emit(document)
    raise SystemExit(EXIT_BLOCKED)


class RequestParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        emit_blocked(BlockedRead("request", message))


def build_parser() -> argparse.ArgumentParser:
    parser = RequestParser(
        description="Report the open Changes of a Change store (read-only)."
    )
    parser.add_argument("--store", required=True, help="Change store as owner/repo")
    parser.add_argument(
        "--priority-order",
        required=True,
        help="Priority values from first to last, comma-separated "
        "(for example Blocker,Urgent,Normal,Deferred)",
    )
    parser.add_argument("--product", help="keep only Changes with this Product")
    parser.add_argument(
        "--maturity", help=f"keep only this Maturity: {', '.join(MATURITIES)}"
    )
    parser.add_argument(
        "--lifecycle", help=f"keep only this Lifecycle: {', '.join(LIFECYCLES)}"
    )
    parser.add_argument("--holder", help="keep only Changes this login is assigned to")
    parser.add_argument(
        "--blocked",
        choices=("yes", "no"),
        help="yes keeps Changes with an open blocker, no keeps Changes without one",
    )
    return parser


def parse_request(argv: list[str]) -> Request:
    args = build_parser().parse_args(argv)
    if not STORE_PATTERN.match(args.store):
        raise BlockedRead(
            "request",
            f"--store must be owner/repo; observed {args.store!r}",
        )
    order = tuple(
        part.strip() for part in args.priority_order.split(",") if part.strip()
    )
    if not order or len(set(order)) != len(order):
        raise BlockedRead(
            "request",
            "--priority-order must list distinct Priority values from first to last, "
            f"comma-separated; observed {args.priority_order!r}",
        )
    if args.maturity is not None and args.maturity not in MATURITIES:
        raise BlockedRead(
            "request",
            f"--maturity must be one of {', '.join(MATURITIES)}; observed {args.maturity!r}",
        )
    if args.lifecycle is not None and args.lifecycle not in LIFECYCLES:
        raise BlockedRead(
            "request",
            f"--lifecycle must be one of {', '.join(LIFECYCLES)}; observed {args.lifecycle!r}",
        )
    owner, repo = args.store.split("/", 1)
    return Request(
        owner=owner,
        repo=repo,
        priority_order=order,
        product=args.product,
        maturity=args.maturity,
        lifecycle=args.lifecycle,
        holder=args.holder,
        blocked=None if args.blocked is None else args.blocked == "yes",
    )


def run_gh(read: str, arguments: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["gh", *arguments], capture_output=True, text=True, check=False
        )
    except OSError as error:
        raise BlockedRead(read, f"gh could not run: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise BlockedRead(read, f"gh exited {completed.returncode}: {detail}")
    return completed.stdout


def gh_json(read: str, arguments: list[str]) -> Any:
    output = run_gh(read, arguments)
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise BlockedRead(read, f"unreadable output: {error}") from error


def graphql(read: str, query: str, variables: dict[str, str | int]) -> dict[str, Any]:
    arguments = ["api", "graphql", "-f", f"query={query}"]
    for name, value in variables.items():
        flag = "-F" if isinstance(value, int) else "-f"
        arguments += [flag, f"{name}={value}"]
    document = gh_json(read, arguments)
    if not isinstance(document, dict) or document.get("errors"):
        raise BlockedRead(
            read, f"graphql returned errors or an unexpected shape: {document!r}"
        )
    data = document.get("data")
    if not isinstance(data, dict):
        raise BlockedRead(read, "graphql returned no data")
    return data


def field_values(read: str, node: dict[str, Any]) -> dict[str, Any]:
    connection = (node.get("issueFieldValues") or {}).get("nodes") or []
    if len(connection) >= FIELD_VALUE_LIMIT:
        raise BlockedRead(
            read,
            f"issue {node.get('number')} returned {FIELD_VALUE_LIMIT} field values",
            bound="50 field values",
        )
    values: dict[str, Any] = {}
    for entry in connection:
        field = (entry.get("field") or {}).get("name")
        if field is None:
            continue
        value = entry["name"] if "name" in entry else entry.get("value")
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        values[field] = value
    return values


def read_store(request: Request) -> list[Change]:
    read = f"issues of {request.store}"
    changes: list[Change] = []
    cursor: str | None = None
    for _page in range(MAX_PAGES):
        variables: dict[str, str | int] = {"o": request.owner, "r": request.repo}
        if cursor is not None:
            variables["after"] = cursor
        data = graphql(read, STORE_QUERY, variables)
        try:
            issues = data["repository"]["issues"]
            nodes = issues["nodes"]
            page_info = issues["pageInfo"]
        except (KeyError, TypeError) as error:
            raise BlockedRead(read, f"unreadable output: missing {error}") from error
        for node in nodes:
            assignees = tuple(
                a["login"] for a in (node.get("assignees") or {}).get("nodes") or []
            )
            if len(assignees) >= ASSIGNEE_LIMIT:
                raise BlockedRead(
                    read,
                    f"issue {node.get('number')} returned {ASSIGNEE_LIMIT} assignees",
                    bound="100 assignees",
                )
            values = field_values(read, node)
            parent = values.get(FIELD_PARENT)
            changes.append(
                Change(
                    number=node["number"],
                    url=node["url"],
                    title=node["title"],
                    state=node["state"],
                    assignees=assignees,
                    product=values.get(FIELD_PRODUCT),
                    maturity=values.get(FIELD_MATURITY),
                    lifecycle=values.get(FIELD_LIFECYCLE),
                    priority=values.get(FIELD_PRIORITY),
                    parent=parent if isinstance(parent, int) else None,
                )
            )
        if not page_info["hasNextPage"]:
            return changes
        cursor = page_info["endCursor"]
    raise BlockedRead(
        read,
        f"{request.store} holds more than {PAGE_SIZE * MAX_PAGES} issues",
        bound="100 issues per page, 10 pages",
    )


def read_blockers(request: Request, number: int) -> list[dict[str, Any]]:
    read = f"blockers of {request.store}#{number}"
    entries = gh_json(
        read,
        [
            "api",
            f"repos/{request.store}/issues/{number}/dependencies/blocked_by",
            "--method",
            "GET",
            "-F",
            f"per_page={BLOCKER_LIMIT}",
        ],
    )
    if not isinstance(entries, list):
        raise BlockedRead(
            read, f"unreadable output: expected a list, observed {entries!r}"
        )
    if len(entries) >= BLOCKER_LIMIT:
        raise BlockedRead(
            read,
            f"{number} returned {BLOCKER_LIMIT} blockers",
            bound="100 blockers, one page",
        )
    blockers: list[dict[str, Any]] = []
    for entry in entries:
        try:
            repository = entry["repository_url"].rsplit("repos/", 1)[-1]
            identity = (
                str(entry["number"])
                if repository == request.store
                else f"{repository}#{entry['number']}"
            )
            blockers.append(
                {
                    "number": identity,
                    "state": entry["state"],
                    "state_reason": entry.get("state_reason"),
                }
            )
        except (KeyError, TypeError, AttributeError) as error:
            raise BlockedRead(read, f"unreadable output: missing {error}") from error
    return blockers


def read_comments(request: Request, number: int) -> list[dict[str, Any]]:
    read = f"comments of {request.store}#{number}"
    document = gh_json(
        read,
        ["issue", "view", str(number), "--repo", request.store, "--json", "comments"],
    )
    try:
        comments = [
            {
                "author": (c.get("author") or {}).get("login"),
                "createdAt": c["createdAt"],
                "body": c["body"],
            }
            for c in document["comments"]
        ]
    except (KeyError, TypeError) as error:
        raise BlockedRead(read, f"unreadable output: missing {error}") from error
    return sorted(comments, key=lambda c: c["createdAt"])


def read_available_moves(request: Request, number: int) -> list[str]:
    read = f"field-change events of {request.store}#{number}"
    moves: list[str] = []
    cursor: str | None = None
    for _page in range(MAX_PAGES):
        variables: dict[str, str | int] = {
            "o": request.owner,
            "r": request.repo,
            "n": number,
        }
        if cursor is not None:
            variables["after"] = cursor
        data = graphql(read, EVENT_QUERY, variables)
        try:
            items = data["repository"]["issue"]["timelineItems"]
            for event in items["nodes"]:
                field = (event.get("issueField") or {}).get("name")
                if field == FIELD_LIFECYCLE and event.get("newValue") == "Available":
                    moves.append(event["createdAt"])
            if not items["pageInfo"]["hasNextPage"]:
                return moves
            cursor = items["pageInfo"]["endCursor"]
        except (KeyError, TypeError) as error:
            raise BlockedRead(read, f"unreadable output: missing {error}") from error
    raise BlockedRead(
        read,
        f"{number} holds more than {PAGE_SIZE * MAX_PAGES} field-change events",
        bound="100 events per page, 10 pages",
    )


def is_handoff(comment: dict[str, Any]) -> bool:
    return comment["body"].lstrip().startswith("Handoff:")


def newest_handoff(comments: list[dict[str, Any]]) -> dict[str, Any] | None:
    handoffs = [c for c in comments if is_handoff(c)]
    return handoffs[-1] if handoffs else None


def winning_claim(
    comments: list[dict[str, Any]], available_moves: list[str]
) -> dict[str, str] | None:
    """Earliest `Claim:` after the newest Handoff that a move to Available follows."""
    start: str | None = None
    if available_moves:
        last_move = max(available_moves)
        followed = [
            c["createdAt"]
            for c in comments
            if is_handoff(c) and c["createdAt"] <= last_move
        ]
        start = max(followed) if followed else None
    for comment in comments:
        if start is not None and comment["createdAt"] <= start:
            continue
        match = (
            CLAIM_PATTERN.match(comment["body"].strip().splitlines()[0])
            if comment["body"].strip()
            else None
        )
        if match:
            return {
                "login": comment["author"],
                "session": match.group(1),
                "claim_root": match.group(2),
            }
    return None


def handoff_line(handoff: dict[str, Any], label: str) -> str | None:
    match = re.search(
        rf"^- {re.escape(label)}: (.+?)\s*$", handoff["body"], re.MULTILINE
    )
    return match.group(1) if match else None


def read_changeset(handoff: dict[str, Any] | None) -> tuple[Any, bool]:
    """Return the changeset value and whether its pull request holds a check not in success."""
    if handoff is None:
        return "none", False
    line = handoff_line(handoff, "Branch or PR")
    if line is None or line == "none":
        return "none", False
    reference, _, head = line.rpartition("@")
    if not reference:
        reference, head = line, ""
    changeset: dict[str, Any] = {"ref": reference, "head": head or None}
    if not PULL_REQUEST_PATTERN.match(reference):
        changeset["kind"] = "branch"
        return changeset, False
    changeset["kind"] = "pull_request"
    read = f"checks of {reference}"
    document = gh_json(read, ["pr", "view", reference, "--json", "statusCheckRollup"])
    try:
        rollup = document["statusCheckRollup"] or []
        checks = []
        for entry in rollup:
            name = entry.get("name") or entry.get("context")
            result = (
                entry.get("conclusion") or entry.get("state") or entry.get("status")
            )
            checks.append({"name": name, "result": str(result).lower()})
    except (KeyError, TypeError, AttributeError) as error:
        raise BlockedRead(read, f"unreadable output: missing {error}") from error
    changeset["checks"] = checks
    return changeset, any(check["result"] != "success" for check in checks)


def root_of(number: int, by_number: dict[int, Change]) -> int | str:
    seen: set[int] = set()
    current = number
    while True:
        if current in seen:
            return "unresolved"
        seen.add(current)
        change = by_number.get(current)
        if change is None:
            return "unresolved"
        if change.parent is None:
            return current
        current = change.parent


def waiting_state(
    change: Change,
    open_blockers: list[str],
    claim: dict[str, str] | None,
    checks_pending: bool,
) -> list[str]:
    if change.lifecycle == "Submitted":
        return [f"confirmation: {change.maturity}"]
    if change.lifecycle == "Claimed":
        if claim is None:
            waiting = [
                f"holder: {', '.join(change.assignees) or 'none recorded'} (claim none recorded)"
            ]
        else:
            waiting = [
                f"holder: {claim['login']} (session {claim['session']}, root {claim['claim_root']})"
            ]
        if checks_pending:
            waiting.append("checks")
        return waiting
    if change.lifecycle == "Available":
        return [f"blockers: {', '.join(open_blockers)}"] if open_blockers else ["claim"]
    return ["none"]


def matches(request: Request, change: Change) -> bool:
    return (
        change.state == "OPEN"
        and (request.product is None or change.product == request.product)
        and (request.maturity is None or change.maturity == request.maturity)
        and (request.lifecycle is None or change.lifecycle == request.lifecycle)
        and (request.holder is None or request.holder in change.assignees)
    )


def priority_rank(request: Request, change: Change) -> int:
    if change.priority is None:
        return len(request.priority_order) - 1
    try:
        return request.priority_order.index(change.priority)
    except ValueError as error:
        raise BlockedRead(
            "priority order",
            f"{request.store}#{change.number} holds Priority {change.priority!r}, "
            f"which --priority-order does not list ({', '.join(request.priority_order)})",
        ) from error


def build_report(request: Request) -> list[dict[str, Any]]:
    changes = read_store(request)
    by_number = {change.number: change for change in changes}
    candidates = [change for change in changes if matches(request, change)]
    blockers_by_number = {
        c.number: read_blockers(request, c.number) for c in candidates
    }
    if request.blocked is not None:
        candidates = [
            c
            for c in candidates
            if any(b["state"] == "open" for b in blockers_by_number[c.number])
            == request.blocked
        ]
    candidates.sort(key=lambda c: (priority_rank(request, c), c.number))

    rows: list[dict[str, Any]] = []
    for change in candidates:
        blockers = blockers_by_number[change.number]
        open_blockers = [b["number"] for b in blockers if b["state"] == "open"]
        comments = read_comments(request, change.number)
        handoff = newest_handoff(comments)
        changeset, checks_pending = read_changeset(handoff)
        claim = None
        if change.lifecycle == "Claimed":
            claim = winning_claim(
                comments, read_available_moves(request, change.number)
            )
        next_action = (
            handoff_line(handoff, "Next block") if handoff else None
        ) or "none recorded"
        rows.append(
            {
                "number": change.number,
                "url": change.url,
                "title": change.title,
                "product": change.product,
                "maturity": change.maturity,
                "lifecycle": change.lifecycle,
                "priority": change.priority,
                "holder": list(change.assignees),
                "parent": change.parent,
                "root": root_of(change.number, by_number),
                "blockers": blockers,
                "changeset": changeset,
                "waiting": waiting_state(change, open_blockers, claim, checks_pending),
                "next_action": next_action,
            }
        )
    return rows


def main(argv: list[str]) -> int:
    try:
        rows = build_report(parse_request(argv))
    except BlockedRead as blocked:
        emit_blocked(blocked)
    emit({"status": "ok", "rows": rows})
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
