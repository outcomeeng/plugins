"""Map the SPX CLI's spec-tree projection into the prototype tree shape.

The browser interface sources spec-tree structure and derived state from the
SPX CLI's JSON projection (`spx spec status --format json`) rather than
re-parsing directory suffixes or deriving node state itself. This module is the
pure, transport-free adapter between that projection and the tree shape the
state core and browser shell consume.

`spx spec status --format json` shape (the part this adapter reads)::

    {
      "version": 1,
      "product": {"id": ..., "title": ...},
      "nodes": [
        {"id", "kind", "order", "slug", "state", "children": [ ... ]}
      ]
    }

A projection node carries derived `state` (declared | specified | failing |
passing) and a `slug`, but no display title, no opener, and no assertions —
those richer fields are not yet exposed by the CLI projection, so the tree pane
renders structure, state, category, and index, while node-detail awaits a
richer projection.

A prototype tree Node is
``{"id", "slug", "kind", "order", "state", "title", "children": [Node]}`` — the
same shape ``state.py`` documents, with ``state`` carried through and the
projection's ``slug`` used as the display ``title`` (the projection has none).
"""

from __future__ import annotations


def spx_projection_to_tree(projection: dict) -> list[dict]:
    """Return the prototype tree forest for an `spx spec status` projection.

    Reads the projection's ``nodes`` list and maps each node recursively. A
    projection without ``nodes`` yields an empty forest rather than raising, so
    a product with an empty spec tree seeds an empty browser.
    """
    return [_node(n) for n in projection.get("nodes", [])]


def is_spx_projection(data: dict) -> bool:
    """True when ``data`` looks like an `spx spec status --format json` payload.

    Distinguishes the projection from the two seed shapes ``boot.py`` already
    accepts (a full state document with ``rev``/``questions``, or a bare
    ``{tree, planned}``): the projection carries a top-level ``nodes`` list and
    neither a ``rev`` nor a ``tree`` key.
    """
    return (
        isinstance(data.get("nodes"), list) and "rev" not in data and "tree" not in data
    )


def _node(node: dict) -> dict:
    return {
        "id": node["id"],
        "slug": node["slug"],
        "kind": node["kind"],
        "order": node["order"],
        "state": node.get("state"),
        "title": node["slug"],
        "children": [_node(child) for child in node.get("children", [])],
    }
