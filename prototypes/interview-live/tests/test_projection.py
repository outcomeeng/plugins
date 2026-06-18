"""Unit tests for the SPX-projection -> prototype-tree adapter.

These encode the assertions the eventual interview node will declare about the
browser sourcing structure and derived state from the SPX CLI's JSON
projection: the adapter preserves hierarchy and order, carries each node's
derived state through, and uses the projection slug as the display title
because the projection exposes none. Run:
``python3 -m unittest discover -s tests`` from the prototype directory.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from projection import (  # noqa: E402
    is_spx_projection,
    spx_projection_to_tree,
)


def projection_fixture() -> dict:
    return {
        "version": 1,
        "product": {"id": "example.product.md", "title": "example"},
        "nodes": [
            {
                "id": "13-infrastructure.enabler",
                "kind": "enabler",
                "order": 13,
                "slug": "infrastructure",
                "state": "declared",
                "children": [
                    {
                        "id": "13-infrastructure.enabler/21-build.enabler",
                        "kind": "enabler",
                        "order": 21,
                        "slug": "build",
                        "state": "specified",
                        "children": [],
                    },
                ],
            },
            {
                "id": "32-feature.outcome",
                "kind": "outcome",
                "order": 32,
                "slug": "feature",
                "state": "passing",
                "children": [],
            },
        ],
    }


class ProjectionShape(unittest.TestCase):
    def test_hierarchy_and_order_preserved(self) -> None:
        tree = spx_projection_to_tree(projection_fixture())
        self.assertEqual(
            [n["id"] for n in tree],
            [
                "13-infrastructure.enabler",
                "32-feature.outcome",
            ],
        )
        self.assertEqual([n["order"] for n in tree], [13, 32])
        infra = tree[0]
        self.assertEqual([c["slug"] for c in infra["children"]], ["build"])

    def test_derived_state_carried_through(self) -> None:
        tree = spx_projection_to_tree(projection_fixture())
        self.assertEqual(tree[0]["state"], "declared")
        self.assertEqual(tree[0]["children"][0]["state"], "specified")
        self.assertEqual(tree[1]["state"], "passing")

    def test_kind_carried_through(self) -> None:
        tree = spx_projection_to_tree(projection_fixture())
        self.assertEqual(tree[0]["kind"], "enabler")
        self.assertEqual(tree[1]["kind"], "outcome")

    def test_slug_used_as_display_title(self) -> None:
        # The projection carries no title; the adapter falls back to the slug so
        # the existing tree renderer has a label to show.
        tree = spx_projection_to_tree(projection_fixture())
        self.assertEqual(tree[0]["title"], "infrastructure")
        self.assertEqual(tree[0]["children"][0]["title"], "build")

    def test_node_carries_full_tree_shape(self) -> None:
        node = spx_projection_to_tree(projection_fixture())[0]
        self.assertEqual(
            set(node),
            {"id", "slug", "kind", "order", "state", "title", "children"},
        )

    def test_empty_projection_yields_empty_forest(self) -> None:
        self.assertEqual(spx_projection_to_tree({"version": 1, "nodes": []}), [])
        self.assertEqual(spx_projection_to_tree({"version": 1}), [])


class ProjectionDetection(unittest.TestCase):
    def test_recognizes_projection_payload(self) -> None:
        self.assertTrue(is_spx_projection(projection_fixture()))

    def test_rejects_full_state_document(self) -> None:
        self.assertFalse(
            is_spx_projection({"rev": 0, "questions": {}, "tree": [], "nodes": []})
        )

    def test_rejects_bare_tree_seed(self) -> None:
        self.assertFalse(is_spx_projection({"tree": [], "planned": []}))


if __name__ == "__main__":
    unittest.main()
