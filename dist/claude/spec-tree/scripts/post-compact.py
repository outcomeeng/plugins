#!/usr/bin/env python3
"""PostCompact hook: re-anchor the resuming agent after compaction.

The active node comes first from the spx CLI's resume stash
(`spx compact retrieve`), which the PreCompact hook populated from the
transcript. When the CLI returns no stash — it is absent, the command is not yet
available, or nothing was captured — the hook falls back to parsing the active
node and foundation marker out of the compact summary the harness injected.

It then emits, via stdout, a `<SPEC-TREE_RESUMED .../>` marker and, when a
foundation was active pre-compact, a plain instruction telling the agent its
loaded skills are gone and to re-invoke /spec-tree:understanding and
/spec-tree:contextualizing on the node, passing it as the argument (a bare
invocation loads nothing). The hook owns only this presentation; `.spx/`
mechanics live in the spx CLI.

Reads (from the PostCompact JSON payload on stdin):
  .session_id       Conversation id; passed to the spx CLI.
  .compact_summary  Compaction output; the fallback node source.

Invokes: spx compact retrieve --session-id <id>
($SPX_BIN overrides the `spx` executable; tests point it at a fake.)

stdlib only (python3); no third-party packages.
"""

import json
import os
import re
import subprocess
import sys

_NODE = re.compile(r"spx/[A-Za-z0-9._/-]+")


def section_lines(summary: str, header: str) -> list[str]:
    """Body lines of the '### <header>' section, up to the next '### ' header."""
    out: list[str] = []
    found = False
    for line in summary.splitlines():
        if line.startswith(f"### {header}"):
            found = True
            continue
        if found and line.startswith("### "):
            break
        if found:
            out.append(line)
    return out


def summary_has_foundation(summary: str) -> bool:
    # Scope to the markers section so a token quoted elsewhere does not trigger.
    return any(
        "<SPEC_TREE_FOUNDATION>" in line
        for line in section_lines(summary, "Pre-compact markers")
    )


def summary_active_node(summary: str) -> str:
    # Tolerate backticks/bullets by searching for the spx/ token anywhere on the line.
    for line in section_lines(summary, "Active spec-tree node"):
        match = _NODE.search(line)
        if match:
            return match.group(0)
    return ""


def resume_from_spx(session_id: str) -> dict | None:
    """Return the spx CLI's resume stash as a dict, or None when there is none."""
    if not session_id:
        return None
    spx = os.environ.get("SPX_BIN", "spx")
    try:
        result = subprocess.run(
            [spx, "compact", "retrieve", "--session-id", session_id],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def reanchoring_instruction(active_node: str) -> list[str]:
    lines = [
        "",
        "Compaction expired your loaded spec-tree skills. The methodology foundation",
        "and the node context you had are gone from this conversation — the summary is a",
        "record of them, not the live skills. Before any further spec-tree work, re-invoke:",
        "",
        "  /spec-tree:understanding",
    ]
    if active_node:
        lines += [
            f"  /spec-tree:contextualizing {active_node}",
            "",
            "Run /spec-tree:contextualizing with the node path above — it is the node you",
            "were working on, and a bare invocation without it loads nothing.",
        ]
    else:
        lines += [
            "  /spec-tree:contextualizing <full-node-path>",
            "",
            "The summary did not preserve which node you were working on. Determine the full",
            "node path and pass it to /spec-tree:contextualizing — a bare invocation loads nothing.",
        ]
    return lines


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return 0

    session_id = (payload.get("session_id") or "").strip()

    active_node = ""
    has_foundation = False
    have_source = False

    # Prefer the spx CLI's transcript-derived stash over the model-written summary.
    stash = resume_from_spx(session_id)
    if stash is not None:
        active_node = stash.get("active_node") or ""
        has_foundation = bool(stash.get("has_foundation"))
        have_source = True

    # Fall back to parsing the compact summary when the CLI returns no stash.
    if not have_source:
        summary = payload.get("compact_summary")
        if not summary:
            return 0
        has_foundation = summary_has_foundation(summary)
        active_node = summary_active_node(summary)

    out = [
        f'<SPEC-TREE_RESUMED active-node="{active_node}"/>'
        if active_node
        else "<SPEC-TREE_RESUMED/>"
    ]
    if has_foundation:
        out += reanchoring_instruction(active_node)
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
