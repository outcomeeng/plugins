"""Print each watched session's model, cost, context and weekly quota, costliest first.

Every backend is read through the typed operations of its sibling adapter, so
the table covers each session the backends report.

Usage: python3 costs.py
"""

from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from pathlib import Path

import environment

UNKNOWN = "?"
COST_READ_LINES = 8
COST = re.compile(r"\$([\d,]+\.\d+)")
CONTEXT = re.compile(r"tokens\)\s*(\d+)%")
MODEL = re.compile(r"\[(Opus[^\]]*|Sonnet[^\]]*|Haiku[^\]]*)\]")
WEEK = re.compile(r"7d:\s*(\d+)%")
CODEX_USED = re.compile(r"(\d+(?:\.\d+)?[KM]) used")
CODEX_MODEL = "codex"


def figures(text: str) -> tuple[str, str, str, str]:
    """The model, cost, context percent and weekly percent a status line shows."""
    cost = COST.findall(text)
    context = CONTEXT.findall(text)
    model = MODEL.findall(text)
    week = WEEK.findall(text)
    codex = CODEX_USED.findall(text)
    return (
        model[-1] if model else (CODEX_MODEL if codex else UNKNOWN),
        cost[-1] if cost else (codex[-1] if codex else UNKNOWN),
        context[-1] if context else UNKNOWN,
        week[-1] if week else UNKNOWN,
    )


def dollars(cost: str) -> float:
    try:
        return float(cost.replace(",", ""))
    except ValueError:
        return -1.0


def rows() -> list[tuple[str, str, str, str, str, str]]:
    found = []
    for name, backend in environment.BACKENDS.items():
        try:
            sessions = backend.sessions()
        except environment.AdapterError as error:
            found.append((name, f"inventory failed: {error}", *figures("")))
            continue
        for session in sessions:
            try:
                text = backend.read(session, COST_READ_LINES)
            except environment.AdapterError:
                text = ""
            label = Path(session.cwd).name or session.handle
            found.append((name, label, *figures(text)))
    return found


def render(table: Sequence[tuple[str, str, str, str, str, str]]) -> str:
    lines = []
    for backend, label, model, cost, context, week in sorted(
        table, key=lambda row: dollars(row[3]), reverse=True
    ):
        lines.append(
            f"{backend:6} | {label[:34]:34} | {model[:22]:22} | ${cost:>9} "
            f"| ctx {context:>3}% | 7d {week}%"
        )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str]) -> int:
    if argv:
        print("usage: costs.py", file=sys.stderr)
        return 2
    sys.stdout.write(render(rows()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
