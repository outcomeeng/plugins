"""Pure, transport-free state core for the live interview loop.

This module is the conflict-handling spine. It owns the canonical state
document and the rule that turns an incoming event into a new revision. It
has no HTTP, no threading, no filesystem dependency, so it is unit-testable
in isolation and portable to the Python 3.11 stdlib floor the shipped skill
scripts target.

State document shape::

    {
      "rev": int,                  # monotonic; bumped on every accepted mutation
      "questions": {
        "planned": [Question],     # upcoming, in order
        "current": Question | None,# the one being asked now
        "settled": [Question],     # answered, each carrying a "choice"
      },
      "tree": [Node],              # spec-tree nodes, nested
      "updatedAt": str | None,     # ISO-8601 of last mutation
    }

A Question is ``{"id", "text", "options": [str], "choice": str | None}``.
A Node is ``{"id", "slug", "kind", "order", "title", "children": [Node]}``.

The model is deliberately single-writer-friendly: one local user in a browser
and one agent. Concurrency is reconciled with a single monotonic ``rev`` and
last-writer-wins, except that a structural tree op naming a node that no longer
exists is rejected as a conflict so the stale party refetches.
"""

from __future__ import annotations

import copy
import itertools
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Result -----------------------------------------------------------------


@dataclass
class Result:
    """Outcome of applying one event to the store."""

    ok: bool
    rev: int
    state: dict | None = None
    event: dict | None = None
    conflict: str | None = None


# --- Errors -----------------------------------------------------------------


class EventError(ValueError):
    """Raised when an event is structurally malformed (caller bug)."""


# --- Tree helpers (pure functions over a list[Node]) ------------------------


def _walk(nodes: list[dict]) -> Iterator[tuple[dict, list[dict]]]:
    """Yield (node, sibling_list) for every node in the forest."""
    for node in nodes:
        yield node, nodes
        yield from _walk(node["children"])


def _find(nodes: list[dict], node_id: str) -> dict | None:
    for node, _siblings in _walk(nodes):
        if node["id"] == node_id:
            return node
    return None


def _find_siblings(nodes: list[dict], node_id: str) -> list[dict] | None:
    for node, siblings in _walk(nodes):
        if node["id"] == node_id:
            return siblings
    return None


def _is_descendant(ancestor: dict, node_id: str) -> bool:
    return any(
        child["id"] == node_id or _is_descendant(child, node_id)
        for child in ancestor["children"]
    )


def _collect_ids(nodes: list[dict]) -> set[str]:
    return {node["id"] for node, _siblings in _walk(nodes)}


# --- Store ------------------------------------------------------------------


def initial_state(
    tree: list[dict] | None = None, planned: list[dict] | None = None
) -> dict:
    return {
        "rev": 0,
        "questions": {
            "planned": planned or [],
            "current": None,
            "settled": [],
        },
        "tree": tree or [],
        "updatedAt": None,
    }


class Store:
    """Holds the canonical state and applies events to it.

    Not thread-safe by itself; the server wraps every call in a lock. Keeping
    the lock out here is deliberate — it lets tests drive the model directly.
    """

    def __init__(self, state: dict | None = None) -> None:
        self.state = state if state is not None else initial_state()
        self.journal: list[dict] = []
        self._ids = itertools.count(1)

    @property
    def rev(self) -> int:
        return self.state["rev"]

    def snapshot(self) -> dict:
        return copy.deepcopy(self.state)

    def _new_node_id(self) -> str:
        # Skip ids already present in the current tree. A seed (e.g. from
        # `spx spec status`) carries its own ids, so a bare counter would
        # collide with them; advance past any in use.
        existing = _collect_ids(self.state["tree"])
        while True:
            candidate = f"n{next(self._ids)}"
            if candidate not in existing:
                return candidate

    def apply(self, event: dict) -> Result:
        if not isinstance(event, dict) or "type" not in event:
            raise EventError("event must be a dict with a 'type'")

        handler = _HANDLERS.get(event["type"])
        if handler is None:
            raise EventError(f"unknown event type: {event['type']!r}")

        # A net-new node needs a server-assigned id when the client omits one;
        # stamp it onto the event before dispatch so the handler stays pure.
        if event["type"] == "tree_add" and not event.get("nodeId"):
            event = {**event, "nodeId": self._new_node_id()}

        working = copy.deepcopy(self.state)
        conflict = handler(working, event)
        if conflict is not None:
            return Result(ok=False, rev=self.rev, conflict=conflict)

        working["rev"] = self.rev + 1
        working["updatedAt"] = _now()
        normalized = {
            "seq": len(self.journal) + 1,
            "rev": working["rev"],
            "baseRev": event.get("baseRev"),
            "type": event["type"],
            "event": {k: v for k, v in event.items() if k != "baseRev"},
            "ts": working["updatedAt"],
        }
        self.state = working
        self.journal.append(normalized)
        return Result(ok=True, rev=self.rev, state=self.snapshot(), event=normalized)


# --- Event handlers ---------------------------------------------------------
#
# Each handler mutates ``state`` in place and returns None on success, or a
# conflict string when the event cannot be applied against this revision.


def _h_answer(state: dict, event: dict) -> str | None:
    qid = event.get("questionId")
    choice = event.get("choice")
    if not qid:
        raise EventError("answer requires questionId")
    questions = state["questions"]
    current = questions["current"]
    if current and current["id"] == qid:
        current["choice"] = choice
        questions["settled"].append(current)
        questions["current"] = (
            questions["planned"].pop(0) if questions["planned"] else None
        )
        return None
    for i, q in enumerate(questions["planned"]):
        if q["id"] == qid:
            q["choice"] = choice
            questions["settled"].append(questions["planned"].pop(i))
            return None
    return "missing_question"


def _h_set_questions(state: dict, event: dict) -> str | None:
    incoming = event.get("questions")
    if not isinstance(incoming, dict):
        raise EventError("set_questions requires a 'questions' object")
    state["questions"] = {
        "planned": incoming.get("planned", []),
        "current": incoming.get("current"),
        "settled": incoming.get("settled", []),
    }
    return None


def _h_set_tree(state: dict, event: dict) -> str | None:
    tree = event.get("tree")
    if not isinstance(tree, list):
        raise EventError("set_tree requires a 'tree' list")
    state["tree"] = tree
    return None


def _h_tree_rename(state: dict, event: dict) -> str | None:
    node = _find(state["tree"], event.get("nodeId", ""))
    if node is None:
        return "missing_node"
    if "title" in event:
        node["title"] = event["title"]
    if "slug" in event:
        node["slug"] = event["slug"]
    return None


def _h_tree_add(state: dict, event: dict) -> str | None:
    parent_id = event.get("parentId")
    siblings: list[dict]
    if parent_id is None:
        siblings = state["tree"]
    else:
        parent = _find(state["tree"], parent_id)
        if parent is None:
            return "missing_node"
        # Node-type nesting rules (e.g. enablers cannot hold outcome children)
        # are intentionally NOT enforced here: that domain constraint belongs to
        # the spec-tree layer this spike feeds, not to the generic core.
        siblings = parent["children"]
    new_node = {
        "id": event["nodeId"],
        "slug": event.get("slug", "new-node"),
        "kind": event.get("kind", "enabler"),
        "order": event.get("order", (len(siblings) + 1) * 10),
        "title": event.get("title", "New node"),
        "children": [],
    }
    index = event.get("index")
    if index is None or index < 0 or index > len(siblings):
        siblings.append(new_node)
    else:
        siblings.insert(index, new_node)
    return None


def _h_tree_remove(state: dict, event: dict) -> str | None:
    node_id = event.get("nodeId", "")
    siblings = _find_siblings(state["tree"], node_id)
    if siblings is None:
        return "missing_node"
    siblings[:] = [n for n in siblings if n["id"] != node_id]
    return None


def _h_tree_move(state: dict, event: dict) -> str | None:
    node_id = event.get("nodeId", "")
    new_parent_id = event.get("newParentId")
    node = _find(state["tree"], node_id)
    if node is None:
        return "missing_node"
    if new_parent_id is not None:
        new_parent = _find(state["tree"], new_parent_id)
        if new_parent is None:
            return "missing_node"
        if new_parent_id == node_id or _is_descendant(node, new_parent_id):
            return "cyclic_move"
        target = new_parent["children"]
    else:
        target = state["tree"]
    # Detach from current siblings. _find located the node, so _find_siblings
    # must too; raise rather than assert so -O cannot strip the guard.
    old_siblings = _find_siblings(state["tree"], node_id)
    if old_siblings is None:
        raise EventError(
            f"internal: node {node_id!r} found by _find but not _find_siblings"
        )
    old_siblings[:] = [n for n in old_siblings if n["id"] != node_id]
    index = event.get("newIndex")
    if index is None or index < 0 or index > len(target):
        target.append(node)
    else:
        target.insert(index, node)
    # The spike treats list position as authoritative and leaves the node's
    # `order` untouched. On graduation, where `spx spec status` reads sparse
    # integer `order`, the move must recompute `order` from the new position.
    return None


_HANDLERS = {
    "answer": _h_answer,
    "set_questions": _h_set_questions,
    "set_tree": _h_set_tree,
    "tree_rename": _h_tree_rename,
    "tree_add": _h_tree_add,
    "tree_remove": _h_tree_remove,
    "tree_move": _h_tree_move,
}
