#!/usr/bin/env python3
"""Publish one Change Draft: check its form, then write it to a GitHub Change Store only on a pass.

The form check that change-standards owns runs on the exact Draft first. On a
fail the command prints the check's result and writes nothing. On a pass it
writes the title and body, then the Product, Parent, Predecessors and Base
fields and the native blockers from the Draft, clearing each of them the Draft
empties or leaves out, and leaves every other field as the store holds it.
Recording a new Change also writes its Maturity and Lifecycle, which the store
does not yet hold, and recording a Child writes its Parent's stored Priority.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
from collections.abc import Sequence
from types import ModuleType
from typing import Any

PROVIDER = (
    pathlib.Path(__file__).resolve().parents[2]
    / "change-standards"
    / "scripts"
    / "form_check.py"
)
FIELDS_QUERY = (
    "query($l:String!){organization(login:$l){issueFields(first:50){nodes{"
    "... on IssueFieldSingleSelect{id name options{id name}} "
    "... on IssueFieldText{id name} ... on IssueFieldNumber{id name}}}}}"
)
ISSUE_QUERY = (
    "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r)"
    "{issue(number:$n){id createdAt lastEditedAt}}}"
)
PRIORITY_QUERY = (
    "query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){issue(number:$n)"
    "{issueFieldValues(first:50){nodes{... on IssueFieldSingleSelectValue{name "
    "field{... on IssueFieldSingleSelect{name}}}}}}}}"
)
SET_SELECT = (
    "mutation($i:ID!,$f:ID!,$v:ID!){setIssueFieldValue(input:{issueId:$i,"
    "issueFields:[{fieldId:$f,singleSelectOptionId:$v}]}){clientMutationId}}"
)
SET_TEXT = (
    "mutation($i:ID!,$f:ID!,$v:String!){setIssueFieldValue(input:{issueId:$i,"
    "issueFields:[{fieldId:$f,textValue:$v}]}){clientMutationId}}"
)
SET_NUMBER = (
    "mutation($i:ID!,$f:ID!,$v:Float!){setIssueFieldValue(input:{issueId:$i,"
    "issueFields:[{fieldId:$f,numberValue:$v}]}){clientMutationId}}"
)
DELETE = (
    "mutation($i:ID!,$f:ID!){deleteIssueFieldValue(input:{issueId:$i,fieldId:$f})"
    "{clientMutationId}}"
)
FIELD_LIMIT = 50


class PublishError(Exception):
    """A store read or write failed; the result names it."""


def load_form_check() -> ModuleType:
    """Load the change-standards form check from its provider path."""
    spec = (
        importlib.util.spec_from_file_location("form_check", PROVIDER)
        if PROVIDER.is_file()
        else None
    )
    if spec is None or spec.loader is None:
        raise PublishError(
            f"the form check is absent at {PROVIDER}; reinstall the product-tree plugin"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["form_check"] = module
    spec.loader.exec_module(module)
    return module


class Store:
    """The GitHub Change Store, reached through the form check's command runner."""

    def __init__(self, repo: str, root: pathlib.Path, runner: Any) -> None:
        self.repo = repo
        self.owner, _, self.name = repo.partition("/")
        self.root = root
        self.runner = runner
        self.writes: list[str] = []

    def gh(self, *argv: str) -> str:
        result = self.runner(["gh", *argv], cwd=self.root)
        if result.exit_code != 0:
            raise PublishError(
                f"gh {' '.join(argv[:2])} failed: {result.stderr.strip()}"
            )
        return str(result.stdout)

    def graphql(self, query: str, **variables: str) -> Any:
        argv = ["api", "graphql", "-f", f"query={query}"]
        for key, value in variables.items():
            flag = "-F" if key in ("n", "v_number") else "-f"
            argv += [flag, f"{key.removesuffix('_number')}={value}"]
        return json.loads(self.gh(*argv) or "{}")

    def issue(self, number: int) -> dict[str, str]:
        data = self.graphql(ISSUE_QUERY, o=self.owner, r=self.name, n=str(number))
        node = data.get("data", {}).get("repository", {}).get("issue")
        if not node:
            raise PublishError(f"the store holds no issue {self.repo}#{number}")
        return dict(node)

    def priority(self, number: int) -> str | None:
        """Return the Priority issue ``number`` holds, or None when it holds none."""
        data = self.graphql(PRIORITY_QUERY, o=self.owner, r=self.name, n=str(number))
        issue = data.get("data", {}).get("repository", {}).get("issue")
        if not issue:
            raise PublishError(f"the store holds no issue {self.repo}#{number}")
        for node in issue.get("issueFieldValues", {}).get("nodes", []):
            if node.get("field", {}).get("name") == "Priority":
                return str(node.get("name"))
        return None

    def fields(self) -> dict[str, Any]:
        data = self.graphql(FIELDS_QUERY, l=self.owner)
        nodes = (
            data.get("data", {})
            .get("organization", {})
            .get("issueFields", {})
            .get("nodes", [])
        )
        if len(nodes) >= FIELD_LIMIT:
            raise PublishError(f"blocked read: {FIELD_LIMIT} issue fields")
        return {str(n["name"]): n for n in nodes if n.get("name")}

    def set_field(self, issue_id: str, field: Any, value: str) -> None:
        name = str(field["name"])
        if "options" in field:
            option = next(
                (o["id"] for o in field["options"] if o["name"] == value),
                None,
            )
            if option is None:
                raise PublishError(f"the field {name} offers no option {value!r}")
            self.graphql(SET_SELECT, i=issue_id, f=str(field["id"]), v=str(option))
        elif name == "Parent":
            self.graphql(SET_NUMBER, i=issue_id, f=str(field["id"]), v_number=value)
        else:
            self.graphql(SET_TEXT, i=issue_id, f=str(field["id"]), v=value)
        self.writes.append(f"set {name}")

    def clear_field(self, issue_id: str, field: Any) -> None:
        self.graphql(DELETE, i=issue_id, f=str(field["id"]))
        self.writes.append(f"clear {field['name']}")

    def sync_blockers(self, number: int, wanted: list[int]) -> None:
        listed = json.loads(
            self.gh(
                "api",
                f"repos/{self.repo}/issues/{number}/dependencies/blocked_by",
                "--method",
                "GET",
                "-F",
                "per_page=100",
            )
            or "[]"
        )
        if len(listed) >= 100:
            raise PublishError("blocked read: 100 blockers, one page")
        held = {int(item["number"]): int(item["id"]) for item in listed}
        for blocker in sorted(set(wanted) - set(held)):
            blocker_id = self.gh(
                "api", f"repos/{self.repo}/issues/{blocker}", "--jq", ".id"
            ).strip()
            self.gh(
                "api",
                f"repos/{self.repo}/issues/{number}/dependencies/blocked_by",
                "--method",
                "POST",
                "-F",
                f"issue_id={blocker_id}",
            )
            self.writes.append(f"add blocker #{blocker}")
        for blocker in sorted(set(held) - set(wanted)):
            self.gh(
                "api",
                f"repos/{self.repo}/issues/{number}/dependencies/blocked_by/{held[blocker]}",
                "--method",
                "DELETE",
            )
            self.writes.append(f"remove blocker #{blocker}")


def number_of(reference: str | None, repo: str) -> int | None:
    """Return the issue number of an ``owner/repo#N`` reference in ``repo``."""
    if not reference:
        return None
    store, _, number = reference.partition("#")
    if store.lower() != repo.lower() or not number.isdigit():
        raise PublishError(f"{reference} is no issue of the store {repo}")
    return int(number)


def write_text(
    fc: ModuleType,
    store: Store,
    draft: Any,
    issue: str | None,
    read_edited_at: str | None,
) -> int:
    """Create the issue or edit its title and body from the Draft; return its number."""
    body = draft.body[draft.body.index("## Statement of Intent") :]
    title = fc.scalar(draft.values.get("title", "")) or ""
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="publish-"))
    try:
        body_file = scratch / "body.md"
        body_file.write_text(body, encoding="utf-8")
        text_args = [
            "--repo",
            store.repo,
            "--title",
            title,
            "--body-file",
            str(body_file),
        ]
        if issue is None:
            url = store.gh("issue", "create", *text_args).strip()
            store.writes.append("create issue")
            return int(url.rstrip("/").rsplit("/", 1)[-1])
        number = number_of(issue, store.repo) or 0
        node = store.issue(number)
        stamp = node.get("lastEditedAt") or node.get("createdAt")
        if stamp != read_edited_at:
            raise PublishError(
                f"the stored revision was edited at {stamp}, after the read at {read_edited_at}; read the record again and redo the publish"
            )
        store.gh("issue", "edit", str(number), *text_args)
        store.writes.append("edit title and body")
        return number
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def write_fields(
    fc: ModuleType, store: Store, values: dict[str, str], number: int, recording: bool
) -> None:
    """Write the fields and blockers a publish owns, clearing each the Draft empties or leaves out."""
    issue_id = store.issue(number)["id"]
    fields = store.fields()
    parent = number_of(fc.scalar(values.get("parent", "")), store.repo)
    wanted = {
        "Product": fc.scalar(values.get("product", "")),
        "Parent": str(parent) if parent is not None else None,
        "Predecessors": ", ".join(fc.flow_list(values.get("predecessors", "")) or [])
        or None,
        "Base": fc.scalar(values.get("base", "")),
    }
    if recording:
        wanted["Maturity"] = fc.scalar(values.get("maturity", ""))
        wanted["Lifecycle"] = fc.scalar(values.get("lifecycle", ""))
        if parent is not None:
            wanted["Priority"] = store.priority(parent)
    for name, value in wanted.items():
        field = fields.get(name)
        if field is None:
            raise PublishError(f"the organization holds no issue field {name}")
        if value:
            store.set_field(issue_id, field, value)
        elif not recording:
            store.clear_field(issue_id, field)
    blockers = [
        number_of(ref, store.repo) or 0
        for ref in fc.flow_list(values.get("blockers", "")) or []
    ]
    store.sync_blockers(number, blockers)


def write_record(
    fc: ModuleType,
    store: Store,
    draft: Any,
    issue: str | None,
    read_edited_at: str | None,
) -> str:
    """Write the Draft's title, body, fields and blockers; return the issue reference."""
    number = write_text(fc, store, draft, issue, read_edited_at)
    write_fields(fc, store, draft.values, number, recording=issue is None)
    return f"{store.repo}#{number}"


def publish(
    root: pathlib.Path,
    draft_path: pathlib.Path,
    repo: str,
    issue: str | None,
    read_edited_at: str | None,
    published: pathlib.Path | None,
    runner: Any | None = None,
) -> tuple[int, dict[str, object]]:
    """Check the Draft's form and write it only on a pass; return the exit code and result."""
    fc = load_form_check()
    run = runner if runner is not None else fc.run_subprocess
    code, result = fc.check(root, draft_path, issue, read_edited_at, published, run)
    if code != fc.ExitCode.PASS:
        return int(code), {"status": "refused", "check": result, "writes": []}
    store = Store(repo, root, run)
    draft = fc.parse_draft(draft_path.read_text(encoding="utf-8"))
    try:
        reference = write_record(fc, store, draft, issue, read_edited_at)
    except PublishError as exc:
        return 1, {"status": "failed", "detail": str(exc), "writes": store.writes}
    return 0, {"status": "published", "issue": reference, "writes": store.writes}


def main(argv: Sequence[str] | None = None, runner: Any | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--root", required=True, help="absolute path of the checkout root"
    )
    parser.add_argument("--draft", required=True, help="path of the Change Draft")
    parser.add_argument("--store", required=True, help="owner/repo of the Change Store")
    parser.add_argument(
        "--issue", help="owner/repo#N of the stored record a publish replaces"
    )
    parser.add_argument(
        "--read-edited-at", help="lastEditedAt, or createdAt, read with the record"
    )
    parser.add_argument(
        "--published", help="path of a Draft composed from the stored Sliced record"
    )
    arguments = parser.parse_args(argv)
    try:
        code, result = publish(
            pathlib.Path(arguments.root),
            pathlib.Path(arguments.draft),
            arguments.store,
            arguments.issue,
            arguments.read_edited_at,
            pathlib.Path(arguments.published) if arguments.published else None,
            runner,
        )
    except PublishError as exc:
        print(json.dumps({"status": "unusable", "detail": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
