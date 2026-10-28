"""Compliance: harness runs leave no bytecode beside a shipped script.

Importing a harness turns bytecode writing off for the process, and every
harness launch of a script file carries the interpreter's no-bytecode option.
The launch rule is exercised against violating sources and against every
harness module, and the in-process rule against a fresh interpreter.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import outcomeeng_testing.harnesses as harnesses_package
from outcomeeng.distribution.shipped_scripts import NO_BYTECODE_OPTION
from outcomeeng.validation.harness_bytecode import unguarded_script_launches

HARNESS_DIRECTORY = Path(harnesses_package.__file__).parent
PRINT_BYTECODE_FLAG = (
    f"import {harnesses_package.__name__}, sys; print(sys.dont_write_bytecode)"
)


class TestImportTurnsBytecodeWritingOff:
    def test_fresh_interpreter_importing_the_harness_package_writes_no_bytecode(
        self,
    ) -> None:
        result = subprocess.run(
            [sys.executable, NO_BYTECODE_OPTION, "-c", PRINT_BYTECODE_FLAG],
            capture_output=True,
            text=True,
            check=True,
            env={"PATH": "", "PYTHONDONTWRITEBYTECODE": ""},
            cwd=HARNESS_DIRECTORY.parent.parent,
        )
        assert result.stdout.strip() == str(True)


class TestScriptLaunchRule:
    def test_rule_flags_a_script_launch_without_the_option(self) -> None:
        source = "argv = [sys.executable, str(script), 'arg']\n"
        assert unguarded_script_launches(source) == (1,)

    def test_rule_flags_a_launch_with_only_other_options(self) -> None:
        source = "argv = (sys.executable, '-I', str(script))\n"
        assert unguarded_script_launches(source) == (1,)

    def test_rule_accepts_a_launch_carrying_the_option(self) -> None:
        source = (
            f"argv = [sys.executable, {NO_BYTECODE_OPTION!r}, str(script)]\n"
            f"argv = [sys.executable, '-I', {NO_BYTECODE_OPTION!r}, str(script)]\n"
        )
        assert unguarded_script_launches(source) == ()

    def test_rule_accepts_an_inline_program_launch(self) -> None:
        source = "argv = [sys.executable, '-c', program]\n"
        assert unguarded_script_launches(source) == ()


class TestNoHarnessLeavesAScriptLaunchUnguarded:
    def test_every_harness_script_launch_carries_the_option(self) -> None:
        unguarded = {
            f"{path.name}:{line}": None
            for path in sorted(HARNESS_DIRECTORY.glob("*.py"))
            for line in unguarded_script_launches(path.read_text(encoding="utf-8"))
        }
        assert not unguarded, (
            "harness launches of a script file without the interpreter's "
            f"no-bytecode option: {sorted(unguarded)}"
        )
