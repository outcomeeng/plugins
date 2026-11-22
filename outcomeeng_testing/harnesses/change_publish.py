"""Recording-store harness for the author-change publish command.

Backs the ``[test]`` evidence of ``publish-checked`` and ``github-clear`` in
``spx/31-outcomeeng.enabler/32-changes.enabler/54-change-record.pdr.md``. The
harness loads ``publish.py``, answers each GitHub read the command and its form
check make, records every command, and runs ``git`` for real. It decides
nothing: every predicate belongs to the linked test.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Final

from outcomeeng_testing.harnesses.form_check import load_form_check

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
SCRIPT: Final = (
    REPO_ROOT / "src/plugins/product-tree/skills/author-change/scripts/publish.py"
)
STORE: Final = "outcomeeng/changes"
STAMP: Final = "2026-01-01T00:00:00Z"
FIELDS: Final = [
    {
        "id": "F_product",
        "name": "Product",
        "options": [{"id": "O_plugins", "name": "plugins"}],
    },
    {
        "id": "F_maturity",
        "name": "Maturity",
        "options": [{"id": "O_proposed", "name": "Proposed"}],
    },
    {
        "id": "F_lifecycle",
        "name": "Lifecycle",
        "options": [
            {"id": "O_submitted", "name": "Submitted"},
            {"id": "O_available", "name": "Available"},
        ],
    },
    {
        "id": "F_priority",
        "name": "Priority",
        "options": [{"id": "O_normal", "name": "Normal"}],
    },
    {"id": "F_parent", "name": "Parent"},
    {"id": "F_predecessors", "name": "Predecessors"},
    {"id": "F_base", "name": "Base"},
]


def load_publish() -> ModuleType:
    """Return the publish module, loading it from ``SCRIPT`` on first use."""
    loaded = sys.modules.get("change_publish")
    if loaded is not None:
        return loaded
    spec = importlib.util.spec_from_file_location("change_publish", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["change_publish"] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class RecordingStore:
    """Answer the store's reads, record every command, and run ``git`` for real."""

    blocked_by: list[int] = field(default_factory=list)
    calls: list[list[str]] = field(default_factory=list)

    def __call__(self, argv: Sequence[str], /, *, cwd: Path) -> object:
        fc = load_form_check()
        command = list(argv)
        self.calls.append(command)
        if command[0] != "gh":
            return fc.run_subprocess(command, cwd=cwd)
        joined = " ".join(command)
        if command[1:3] == ["api", "graphql"]:
            answer: dict[str, object]
            if "issueFields" in joined:
                answer = {"data": {"organization": {"issueFields": {"nodes": FIELDS}}}}
            elif "issueFieldValues" in joined:
                priority = {"name": "Normal", "field": {"name": "Priority"}}
                answer = {
                    "data": {
                        "repository": {
                            "issue": {"issueFieldValues": {"nodes": [priority]}}
                        }
                    }
                }
            elif "mutation" in joined:
                answer = {"data": {}}
            else:
                answer = {
                    "data": {
                        "repository": {
                            "issue": {
                                "id": "I_7",
                                "createdAt": STAMP,
                                "lastEditedAt": STAMP,
                            }
                        }
                    }
                }
            return fc.CommandResult(0, json.dumps(answer), "")
        if command[1:3] == ["issue", "create"]:
            return fc.CommandResult(0, f"https://github.com/{STORE}/issues/7\n", "")
        if "blocked_by" in joined and "GET" in command:
            listed = [{"number": n, "id": 9000 + n} for n in self.blocked_by]
            return fc.CommandResult(0, json.dumps(listed), "")
        if "--jq" in command:
            return fc.CommandResult(0, "9001\n", "")
        return fc.CommandResult(0, "", "")

    def writes(self) -> list[list[str]]:
        """Return every command that writes to the store."""
        return [
            call
            for call in self.calls
            if call[0] == "gh"
            and (
                call[1:3] in (["issue", "create"], ["issue", "edit"])
                or "mutation" in " ".join(call)
                or "POST" in call
                or "DELETE" in call
            )
        ]

    def mutations(self, name: str) -> list[str]:
        """Return the field ids each mutation called ``name`` wrote."""
        return [
            arg.removeprefix("f=")
            for call in self.writes()
            if any(name in arg for arg in call)
            for arg in call
            if arg.startswith("f=")
        ]
