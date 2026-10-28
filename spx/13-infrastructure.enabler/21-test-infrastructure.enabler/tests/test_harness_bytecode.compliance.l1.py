"""Compliance: harness runs leave no bytecode beside a shipped script.

Importing a harness turns bytecode writing off for the process, an in-process
load of a script leaves no cache beside it, and every harness launch of a script
file carries the interpreter's no-bytecode option. Each mechanism is exercised
against a violating case with its guard off, so the evidence fails when a guard
is off; the launch rule runs against violating and conforming fixture sources and
against every harness module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.validation.harness_bytecode import unguarded_script_launches
from outcomeeng_testing.harnesses.harness_bytecode import (
    conforming_launch_fixtures,
    entries_beside_script_after_load,
    fresh_import_bytecode_flag,
    harness_module_paths,
    unguarded_entries_beside_script_after_load,
    unguarded_import_bytecode_flag,
    violating_launch_fixtures,
)


class TestImportTurnsBytecodeWritingOff:
    def test_fresh_interpreter_importing_the_harness_package_writes_no_bytecode(
        self,
    ) -> None:
        assert fresh_import_bytecode_flag() is True


    def test_fresh_interpreter_importing_a_package_without_the_guard_writes_bytecode(
        self,
    ) -> None:
        assert unguarded_import_bytecode_flag() is False


class TestInProcessLoadLeavesNoCache:
    def test_loading_a_script_leaves_nothing_beside_it(self) -> None:
        assert entries_beside_script_after_load() == ()

    def test_loading_a_script_without_the_guard_leaves_a_cache_beside_it(
        self,
    ) -> None:
        assert unguarded_entries_beside_script_after_load() != ()


class TestScriptLaunchRule:
    @pytest.mark.parametrize(
        "fixture", violating_launch_fixtures(), ids=lambda path: path.name
    )
    def test_rule_flags_a_violating_launch(self, fixture: Path) -> None:
        assert unguarded_script_launches(fixture.read_text(encoding="utf-8")) != ()

    @pytest.mark.parametrize(
        "fixture", conforming_launch_fixtures(), ids=lambda path: path.name
    )
    def test_rule_accepts_a_conforming_launch(self, fixture: Path) -> None:
        assert unguarded_script_launches(fixture.read_text(encoding="utf-8")) == ()


class TestNoHarnessLeavesAScriptLaunchUnguarded:
    @pytest.mark.parametrize(
        "module", harness_module_paths(), ids=lambda path: path.name
    )
    def test_every_harness_script_launch_carries_the_option(self, module: Path) -> None:
        assert unguarded_script_launches(module.read_text(encoding="utf-8")) == ()
