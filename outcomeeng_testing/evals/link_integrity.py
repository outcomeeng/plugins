"""Walk spec-tree markdown for ``[eval](path)`` links and validate their targets.

A ``[eval](path)`` link must resolve to an existing ``eval.toml`` file. The
walker is the engine; the ``outcomeeng/scripts/validate_eval_links.py``
script wires it into ``just check``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


EVAL_TOML_FILENAME = "eval.toml"
MARKDOWN_GLOB = "**/*.md"

_EVAL_LINK_PATTERN = re.compile(r"\[eval\]\(([^)]+)\)")


@dataclass(frozen=True)
class EvalLink:
    """An ``[eval](path)`` reference found in a markdown file."""

    source: Path
    target: Path


@dataclass(frozen=True)
class BrokenEvalLink:
    """An eval link whose target failed validation."""

    source: Path
    target: Path
    reason: str


def find_eval_links(root: Path) -> list[EvalLink]:
    """Walk ROOT for markdown files and collect every ``[eval](path)`` reference."""
    links: list[EvalLink] = []
    for md_path in sorted(root.glob(MARKDOWN_GLOB)):
        if not md_path.is_file():
            continue
        text = md_path.read_text(encoding="utf-8")
        for match in _EVAL_LINK_PATTERN.finditer(text):
            target_rel = match.group(1).strip()
            target = (md_path.parent / target_rel).resolve()
            links.append(EvalLink(source=md_path, target=target))
    return links


def validate_eval_links(root: Path) -> list[BrokenEvalLink]:
    """Return broken links: target missing, not a file, or not an eval.toml."""
    broken: list[BrokenEvalLink] = []
    for link in find_eval_links(root):
        if not link.target.exists():
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason="target does not exist",
                )
            )
            continue
        if not link.target.is_file():
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason="target is not a file",
                )
            )
            continue
        if link.target.name != EVAL_TOML_FILENAME:
            broken.append(
                BrokenEvalLink(
                    source=link.source,
                    target=link.target,
                    reason=f"target must be a {EVAL_TOML_FILENAME} file",
                )
            )
    return broken
