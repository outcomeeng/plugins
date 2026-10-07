"""Variable spec trees for the link-conversion evidence.

Each generated tree holds a root decision record, one to three top-level nodes,
and an optional child node under each. Every spec file carries a drawn mix of
citation forms: some the conversion rewrites, some it reports, and some it
leaves as written.
"""

from __future__ import annotations

import string
from collections.abc import Sequence
from dataclasses import dataclass

from hypothesis import strategies as st

SPEC_TREE_DIRECTORY = "spx"
MIN_NODE_INDEX = 10
MAX_NODE_INDEX = 99
MAX_NODES = 3
MAX_CITATION_LINES = 8
SLUG_ALPHABET = string.ascii_lowercase + string.digits
MAX_SLUG_LENGTH = 5

_SLUGS = st.text(alphabet=SLUG_ALPHABET, min_size=1, max_size=MAX_SLUG_LENGTH)


@dataclass(frozen=True)
class GeneratedTree:
    """Files of one generated product root, keyed by path from that root."""

    files: dict[str, str]


@dataclass(frozen=True)
class _Node:
    directory: str
    spec: str
    decision: str


@st.composite
def _node(draw: st.DrawFn, node_kinds: Sequence[str], *, top_level: bool) -> _Node:
    slug = draw(_SLUGS)
    index = str(draw(st.integers(MIN_NODE_INDEX, MAX_NODE_INDEX)))
    fraction = draw(st.one_of(st.none(), st.integers(1, MAX_NODE_INDEX)))
    if top_level and fraction is not None:
        index = f"{index}.{fraction}"
    kind = draw(st.sampled_from(sorted(node_kinds)))
    spec_suffix = draw(st.sampled_from([".md", ".spec.md"]))
    decision_kind = draw(st.sampled_from(["adr", "pdr"]))
    return _Node(
        directory=f"{index}-{slug}.{kind}",
        spec=f"{slug}{spec_suffix}",
        decision=f"15-{draw(_SLUGS)}.{decision_kind}.md",
    )


def _citation_forms(
    node: _Node,
    root_decision: str,
    sibling: _Node | None,
    child: _Node | None,
) -> dict[str, str]:
    forms = {
        "code_span_own": f"Rule `{node.decision}` applies.",
        "link_own": f"See [rule]({node.decision}).",
        "climb_root": f"See [root](../{root_decision}).",
        "bare_prose": f"Prose names {node.decision} here.",
        "fenced": f"```text\n[root](../{root_decision})\n```",
        "broken": "Missing [gone](99-missing.adr.md).",
        "placeholder": "Pattern NN-{slug}.adr.md stays.",
        "external": "See [site](https://example.com/page).",
    }
    if sibling is not None:
        forms["climb_sibling"] = (
            f"See [other](../{sibling.directory}/{sibling.decision})."
        )
        forms["slash_sibling"] = (
            f"See [other](/{SPEC_TREE_DIRECTORY}/{sibling.directory}/{sibling.decision})."
        )
    if child is not None:
        forms["descendant"] = f"See [child]({child.directory}/{child.decision})."
    return forms


@st.composite
def _spec_text(
    draw: st.DrawFn,
    node: _Node,
    root_decision: str,
    sibling: _Node | None,
    child: _Node | None,
) -> str:
    forms = _citation_forms(node, root_decision, sibling, child)
    names = draw(
        st.lists(
            st.sampled_from(sorted(forms)),
            min_size=1,
            max_size=MAX_CITATION_LINES,
        )
    )
    return "\n".join(["# Node", "", *(forms[name] for name in names), ""])


@st.composite
def link_conversion_trees(
    draw: st.DrawFn,
    node_kinds: Sequence[str],
) -> GeneratedTree:
    """Draw a product root whose nodes use every given node kind in turn."""
    root_decision = f"15-{draw(_SLUGS)}.pdr.md"
    nodes = draw(
        st.lists(
            _node(node_kinds, top_level=True),
            min_size=1,
            max_size=MAX_NODES,
            unique_by=lambda node: node.directory,
        )
    )
    files = {
        f"{SPEC_TREE_DIRECTORY}/{root_decision}": "# Root decision\n",
    }
    for position, node in enumerate(nodes):
        sibling = nodes[(position + 1) % len(nodes)] if len(nodes) > 1 else None
        child = draw(st.one_of(st.none(), _node(node_kinds, top_level=False)))
        node_path = f"{SPEC_TREE_DIRECTORY}/{node.directory}"
        files[f"{node_path}/{node.decision}"] = "# Decision\n"
        files[f"{node_path}/{node.spec}"] = draw(
            _spec_text(node, root_decision, sibling, child)
        )
        if child is not None:
            child_path = f"{node_path}/{child.directory}"
            files[f"{child_path}/{child.decision}"] = "# Decision\n"
            files[f"{child_path}/{child.spec}"] = (
                f"# Child\n\nSee [parent](../{node.decision}).\n"
                f"Rule `{child.decision}` applies.\n"
            )
    return GeneratedTree(files=files)
