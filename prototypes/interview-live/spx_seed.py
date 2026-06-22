#!/usr/bin/env python3
"""Project the SPX spec-tree JSON into the interview-live seed format.

Realizes the rendering input for `spx/16-interfaces.enabler/21-browser.enabler`:
the browser surface renders from the SPX CLI's JSON projection
(`13-rendering.adr.md`), never by re-deriving the tree. This adapter consumes
`spx spec status --format json` and emits the prototype's `{tree, planned}` seed
so the live surface renders this product's actual spec tree.

Each projection node `{id, kind, order, slug, state, children}` maps to the
prototype tree shape `{id, slug, kind, order, title, state, children}`, deriving
a display title from the slug. The projection is the source of truth; this script
only reshapes it.

Usage:
    spx spec status --format json | python3 spx_seed.py > real-tree-seed.json
    python3 spx_seed.py > real-tree-seed.json   # runs spx itself when no stdin
"""

from __future__ import annotations

import json
import subprocess
import sys


def title_from_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").strip().title()


def map_node(node: dict) -> dict:
    return {
        "id": node["id"],
        "slug": node["slug"],
        "kind": node["kind"],
        "order": node["order"],
        "title": title_from_slug(node["slug"]),
        "state": node.get("state"),
        "children": [map_node(child) for child in node.get("children", [])],
    }


def load_projection() -> dict:
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            return json.loads(data)
    completed = subprocess.run(
        ["spx", "spec", "status", "--format", "json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    projection = load_projection()
    seed = {
        "tree": [map_node(node) for node in projection.get("nodes", [])],
        "planned": [],
    }
    json.dump(seed, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
