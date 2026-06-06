"""Unit tests for the pure state/conflict core.

These encode the assertions the eventual interviewing outcome node will declare:
the question lifecycle (planned -> current -> settled), structural tree
integrity under move/add/remove/rename, the conflict cases, and revision
monotonicity. Run: ``python3 -m unittest discover -s tests`` from the prototype
directory.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from state import EventError, Store, initial_state  # noqa: E402


def tree_fixture() -> list[dict]:
    return [
        {
            "id": "a",
            "slug": "infra",
            "kind": "enabler",
            "order": 10,
            "title": "Infra",
            "children": [
                {
                    "id": "a1",
                    "slug": "build",
                    "kind": "enabler",
                    "order": 10,
                    "title": "Build",
                    "children": [],
                },
            ],
        },
        {
            "id": "b",
            "slug": "feature",
            "kind": "outcome",
            "order": 20,
            "title": "Feature",
            "children": [],
        },
    ]


class QuestionLifecycle(unittest.TestCase):
    def setUp(self) -> None:
        planned = [
            {"id": "q1", "text": "Who?", "options": ["A", "B"], "choice": None},
            {"id": "q2", "text": "What?", "options": ["X", "Y"], "choice": None},
        ]
        self.store = Store(initial_state(planned=planned))
        # Promote the first planned question to current via an agent mutation.
        self.store.apply(
            {
                "type": "set_questions",
                "questions": {
                    "planned": [planned[1]],
                    "current": planned[0],
                    "settled": [],
                },
            }
        )

    def test_answering_current_advances_to_next_planned(self) -> None:
        res = self.store.apply({"type": "answer", "questionId": "q1", "choice": "A"})
        self.assertTrue(res.ok)
        q = res.state["questions"]
        self.assertEqual(q["current"]["id"], "q2")
        self.assertEqual(q["settled"][0]["id"], "q1")
        self.assertEqual(q["settled"][0]["choice"], "A")
        self.assertEqual(q["planned"], [])

    def test_answering_planned_out_of_order_keeps_current(self) -> None:
        # Path 2 of _h_answer: answering a planned question settles it without
        # promoting a new current (the current question stays put).
        res = self.store.apply({"type": "answer", "questionId": "q2", "choice": "X"})
        self.assertTrue(res.ok)
        q = res.state["questions"]
        self.assertEqual(q["current"]["id"], "q1")  # current unchanged
        self.assertEqual(q["planned"], [])  # q2 left the planned list
        self.assertEqual([s["id"] for s in q["settled"]], ["q2"])
        self.assertEqual(q["settled"][0]["choice"], "X")

    def test_answering_unknown_question_is_a_conflict(self) -> None:
        res = self.store.apply({"type": "answer", "questionId": "nope", "choice": "A"})
        self.assertFalse(res.ok)
        self.assertEqual(res.conflict, "missing_question")
        self.assertEqual(res.rev, self.store.rev)  # no rev bump on conflict

    def test_answer_without_question_id_raises(self) -> None:
        with self.assertRaises(EventError):
            self.store.apply({"type": "answer", "choice": "A"})


class TreeEditing(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(initial_state(tree=tree_fixture()))

    def test_rename(self) -> None:
        res = self.store.apply(
            {"type": "tree_rename", "nodeId": "a1", "title": "Build Pipeline"}
        )
        self.assertTrue(res.ok)
        self.assertEqual(res.state["tree"][0]["children"][0]["title"], "Build Pipeline")

    def test_add_assigns_id_and_appends(self) -> None:
        res = self.store.apply(
            {"type": "tree_add", "parentId": "b", "kind": "enabler", "title": "New"}
        )
        self.assertTrue(res.ok)
        children = res.state["tree"][1]["children"]
        self.assertEqual(len(children), 1)
        self.assertTrue(children[0]["id"])  # server-assigned

    def test_add_does_not_collide_with_seeded_ids(self) -> None:
        # Regression: a seed carrying n1..n4 must not have the id counter
        # reissue n1/n2 for new nodes. Live use produced duplicate ids that
        # broke find()/move() because they return the first id match.
        before = {"a", "a1", "b"}  # ids carried by tree_fixture()
        res1 = self.store.apply(
            {"type": "tree_add", "parentId": "a", "kind": "enabler"}
        )
        res2 = self.store.apply(
            {"type": "tree_add", "parentId": None, "kind": "outcome"}
        )
        new1 = res1.state["tree"][0]["children"][-1]["id"]
        new2 = res2.state["tree"][-1]["id"]
        self.assertNotIn(new1, before)
        self.assertNotIn(new2, before | {new1})

    def test_add_to_missing_parent_conflicts(self) -> None:
        res = self.store.apply({"type": "tree_add", "parentId": "ghost"})
        self.assertFalse(res.ok)
        self.assertEqual(res.conflict, "missing_node")

    def test_remove(self) -> None:
        res = self.store.apply({"type": "tree_remove", "nodeId": "a1"})
        self.assertTrue(res.ok)
        self.assertEqual(res.state["tree"][0]["children"], [])

    def test_move_into_other_parent(self) -> None:
        res = self.store.apply(
            {"type": "tree_move", "nodeId": "a1", "newParentId": "b", "newIndex": 0}
        )
        self.assertTrue(res.ok)
        tree = res.state["tree"]
        self.assertEqual(tree[0]["children"], [])
        self.assertEqual(tree[1]["children"][0]["id"], "a1")

    def test_move_inserts_at_index_among_roots(self) -> None:
        # Drop "before" the first root: b should land ahead of a.
        res = self.store.apply(
            {"type": "tree_move", "nodeId": "b", "newParentId": None, "newIndex": 0}
        )
        self.assertTrue(res.ok)
        self.assertEqual([n["id"] for n in res.state["tree"]], ["b", "a"])

    def test_move_reorders_within_same_parent(self) -> None:
        store = Store(
            initial_state(
                tree=[
                    {
                        "id": "x",
                        "slug": "x",
                        "kind": "enabler",
                        "order": 10,
                        "title": "X",
                        "children": [],
                    },
                    {
                        "id": "y",
                        "slug": "y",
                        "kind": "enabler",
                        "order": 20,
                        "title": "Y",
                        "children": [],
                    },
                    {
                        "id": "z",
                        "slug": "z",
                        "kind": "enabler",
                        "order": 30,
                        "title": "Z",
                        "children": [],
                    },
                ]
            )
        )
        # Move x to the end: detach shifts indices, so index 2 lands x last.
        res = store.apply(
            {"type": "tree_move", "nodeId": "x", "newParentId": None, "newIndex": 2}
        )
        self.assertTrue(res.ok)
        self.assertEqual([n["id"] for n in res.state["tree"]], ["y", "z", "x"])

    def test_move_into_own_descendant_is_cyclic(self) -> None:
        res = self.store.apply(
            {"type": "tree_move", "nodeId": "a", "newParentId": "a1"}
        )
        self.assertFalse(res.ok)
        self.assertEqual(res.conflict, "cyclic_move")

    def test_move_missing_node_conflicts(self) -> None:
        res = self.store.apply({"type": "tree_move", "nodeId": "ghost"})
        self.assertFalse(res.ok)
        self.assertEqual(res.conflict, "missing_node")


class RevisionAndJournal(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(initial_state(tree=tree_fixture()))

    def test_rev_is_monotonic_only_on_acceptance(self) -> None:
        self.assertEqual(self.store.rev, 0)
        self.store.apply({"type": "tree_rename", "nodeId": "a", "title": "X"})
        self.assertEqual(self.store.rev, 1)
        self.store.apply({"type": "tree_rename", "nodeId": "ghost", "title": "X"})
        self.assertEqual(self.store.rev, 1)  # conflict did not bump
        self.store.apply({"type": "tree_rename", "nodeId": "b", "title": "Y"})
        self.assertEqual(self.store.rev, 2)

    def test_journal_records_each_accepted_event_with_resulting_rev(self) -> None:
        self.store.apply({"type": "tree_rename", "nodeId": "a", "title": "X"})
        self.store.apply({"type": "tree_remove", "nodeId": "b"})
        self.assertEqual([e["rev"] for e in self.store.journal], [1, 2])
        self.assertEqual([e["seq"] for e in self.store.journal], [1, 2])
        self.assertEqual(self.store.journal[0]["type"], "tree_rename")

    def test_base_rev_is_recorded_for_staleness_detection(self) -> None:
        self.store.apply(
            {"type": "tree_rename", "nodeId": "a", "title": "X", "baseRev": 0}
        )
        self.assertEqual(self.store.journal[0]["baseRev"], 0)

    def test_snapshot_is_deep_copy(self) -> None:
        snap = self.store.snapshot()
        snap["tree"][0]["title"] = "mutated"
        self.assertEqual(self.store.state["tree"][0]["title"], "Infra")

    def test_unknown_event_type_raises(self) -> None:
        with self.assertRaises(EventError):
            self.store.apply({"type": "nonsense"})


if __name__ == "__main__":
    unittest.main()
