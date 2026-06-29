"""Scenario evidence for the browser interface prototype.

These tests bind the browser node's current prototype claims to concrete files:
the projection adapter preserves the fields the tree renderer displays, the
shell uses text-safe DOM insertion for dynamic user-facing content, and the
node PLAN tracks the node-detail and commenting gaps that the current SPX
projection cannot satisfy yet.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[4]
NODE = ROOT / "spx" / "16-interfaces.enabler" / "21-browser.enabler"
PROTOTYPE = ROOT / "prototypes" / "interview-live"
SHELL = PROTOTYPE / "shell.html"
PLAN = NODE / "PLAN.md"


def _load_projection() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "browser_projection_under_test",
        PROTOTYPE / "projection.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_projection_adapter_preserves_tree_render_fields() -> None:
    projection = {
        "version": 1,
        "nodes": [
            {
                "id": "16-interfaces.enabler",
                "kind": "enabler",
                "order": 16,
                "slug": "interfaces",
                "state": "declared",
                "children": [
                    {
                        "id": "16-interfaces.enabler/21-browser.enabler",
                        "kind": "enabler",
                        "order": 21,
                        "slug": "browser",
                        "state": "specified",
                        "children": [],
                    }
                ],
            }
        ],
    }

    tree = _load_projection().spx_projection_to_tree(projection)

    assert tree == [
        {
            "id": "16-interfaces.enabler",
            "slug": "interfaces",
            "kind": "enabler",
            "order": 16,
            "state": "declared",
            "title": "interfaces",
            "children": [
                {
                    "id": "16-interfaces.enabler/21-browser.enabler",
                    "slug": "browser",
                    "kind": "enabler",
                    "order": 21,
                    "state": "specified",
                    "title": "browser",
                    "children": [],
                }
            ],
        }
    ]


def test_shell_renders_projection_fields_and_live_interactions() -> None:
    shell = SHELL.read_text(encoding="utf-8")

    assert "state-dot" in shell
    assert 'kind.className = "kind " + node.kind' in shell
    assert "idx.textContent = node.order" in shell
    assert "row.style.paddingLeft = (1 + depth * 1.15)" in shell
    assert 'send({ type: "tree_rename"' in shell
    assert 'send({ type: "tree_add"' in shell
    assert 'send({ type: "tree_remove"' in shell
    assert 'send({ type: "tree_move"' in shell
    assert "li.ondrop" in shell
    assert "new EventSource" in shell
    assert 'send({ type: "chat"' in shell


def test_shell_inserts_dynamic_text_with_text_content() -> None:
    shell = SHELL.read_text(encoding="utf-8")

    assert "text.textContent = q.text" in shell
    assert "b.textContent = opt" in shell
    assert "title.textContent = node.title" in shell
    assert "txt.textContent = m.text" in shell
    assert "node.title" not in _inner_html_assignments(shell)
    assert "q.text" not in _inner_html_assignments(shell)
    assert "m.text" not in _inner_html_assignments(shell)


def test_plan_tracks_deferred_node_detail_and_commenting_gaps() -> None:
    plan = PLAN.read_text(encoding="utf-8")

    assert "not openers, assertions, or" in plan
    assert "evidence links" in plan
    assert "enrich the CLI projection" in plan
    assert "commentable" in plan
    assert "text selection" in plan


def _inner_html_assignments(source: str) -> str:
    return "\n".join(line for line in source.splitlines() if ".innerHTML" in line)
