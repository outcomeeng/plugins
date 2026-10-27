"""Compliance test for 13-agent-environment.enabler (agent-environment.md compliance).

L1: the NEVER rule bars the compact entry's command from running a script, the
``spx`` CLI, or an external command, from embedding ``.spx/``, git, transcript, or
session logic, and from printing anything other than the reminder resource. The
observation that detects a violation is the command run through ``/bin/sh`` with
an empty ``PATH`` — so only shell builtins resolve — in an empty working
directory: a conforming command still prints exactly the resource and leaves the
directory empty, while a violating command prints something else or leaves state.

The shipped compact entry is the conforming case. Each inert ``hooks.json``
fixture under ``outcomeeng_testing/fixtures/agent_environment/compact_entry/``
is a real violating entry: an external command, the spx CLI, a script, extra
output, and a state write.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng_testing.harnesses.hooks import (
    compact_entry_command,
    compact_entry_violation_fixtures,
    compact_recovery_resource,
    run_compact_entry,
    shipped_plugin_root,
)

# An empty PATH leaves no external command resolvable; only shell builtins run.
_NO_EXTERNAL_COMMANDS_PATH = ""


def test_shipped_compact_entry_prints_only_the_resource_through_shell_builtins(
    tmp_path: Path,
) -> None:
    plugin_root = shipped_plugin_root()
    resource = compact_recovery_resource(plugin_root).read_text(encoding="utf-8")
    result = run_compact_entry(
        plugin_root=plugin_root,
        project_dir=tmp_path,
        path=_NO_EXTERNAL_COMMANDS_PATH,
    )
    assert result.returncode == 0
    assert result.stdout.rstrip("\n") == resource.rstrip("\n")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "fixture", compact_entry_violation_fixtures(), ids=lambda path: path.name
)
def test_a_violating_compact_entry_is_observably_not_resource_only(
    fixture: Path, tmp_path: Path
) -> None:
    plugin_root = shipped_plugin_root()
    resource = compact_recovery_resource(plugin_root).read_text(encoding="utf-8")
    result = run_compact_entry(
        plugin_root=plugin_root,
        project_dir=tmp_path,
        command=compact_entry_command(hooks_file=fixture),
        path=_NO_EXTERNAL_COMMANDS_PATH,
    )
    prints_only_the_resource = result.stdout.rstrip("\n") == resource.rstrip("\n")
    leaves_no_state = list(tmp_path.iterdir()) == []
    assert not (prints_only_the_resource and leaves_no_state)
