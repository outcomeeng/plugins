"""Static checks against github-actions helper source for forbidden patterns."""

from __future__ import annotations

import ast
import pathlib

import pytest

SCRIPTS_DIR = (
    pathlib.Path(__file__).resolve().parents[6]
    / "plugins"
    / "spec-tree"
    / "skills"
    / "github-actions"
    / "scripts"
)

HELPERS = (
    SCRIPTS_DIR / "gh_access.py",
    SCRIPTS_DIR / "workflow_inspect.py",
    SCRIPTS_DIR / "mutation_gate.py",
)


@pytest.mark.parametrize("helper", HELPERS, ids=lambda p: p.name)
def test_subprocess_run_uses_capture_output(helper: pathlib.Path) -> None:
    """Every `subprocess.run(...)` invocation passes `capture_output=True`; `subprocess.Popen` is forbidden in helpers."""
    source = helper.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)):
            continue
        if func.value.id != "subprocess":
            continue
        if func.attr == "Popen":
            pytest.fail(
                f"{helper.name}: uses subprocess.Popen — streaming subprocesses are forbidden"
            )
        if func.attr == "run":
            has_capture_output = any(
                kw.arg == "capture_output"
                and isinstance(kw.value, ast.Constant)
                and kw.value.value is True
                for kw in node.keywords
            )
            assert has_capture_output, (
                f"{helper.name}: subprocess.run called without capture_output=True"
            )


@pytest.mark.parametrize("helper", HELPERS, ids=lambda p: p.name)
def test_no_gh_run_watch_reference(helper: pathlib.Path) -> None:
    """Helper source contains no `gh run watch` reference and no other streaming gh subcommand."""
    source = helper.read_text(encoding="utf-8")
    forbidden_phrases = (
        "gh run watch",
        "gh run rerun --watch",
    )
    for phrase in forbidden_phrases:
        assert phrase not in source, (
            f"{helper.name}: contains forbidden phrase {phrase!r}"
        )


@pytest.mark.parametrize("helper", HELPERS, ids=lambda p: p.name)
def test_no_polling_waits(helper: pathlib.Path) -> None:
    """Helper source contains no polling-wait constructs — no `time.sleep` calls, no `import time`."""
    source = helper.read_text(encoding="utf-8")
    assert "time.sleep" not in source, f"{helper.name}: contains time.sleep"
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "time", f"{helper.name}: imports the time module"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "time", f"{helper.name}: imports from the time module"
