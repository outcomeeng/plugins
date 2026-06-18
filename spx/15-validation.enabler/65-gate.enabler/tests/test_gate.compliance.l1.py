"""Level 1 compliance tests for the gate orchestrator.

Verifies architectural compliance rules that can be falsified by inspecting
source code or module-level data:

- The declared step list includes a `ruff format --check` step, a
  `ruff check` step, a `mypy --strict` package step, a `pyright` package step, a
  `spx validation markdown` step, a hook-safety step, and a `dprint check` step.
- The production process spawner passes `start_new_session=True` so
  signal forwarding targets a process group.
- The SIGKILL grace-period wait uses a single `time.monotonic()` deadline
  per signal-handler invocation, followed by a fixed-count post-kill reap check.
- The orchestrator source contains no `gh run watch` literal and no
  `while True:` loop with an embedded `time.sleep` call.

The compliance scope is the gate's underscore-prefixed modules (`_engine`,
`_model`, `_spawner`, `_steps`, plus `__init__` and `__main__`). Sibling
validator modules (`plugins`, `skill_frontmatter`, `install`, `eval_links`)
in the same `outcomeeng.validation` package are independent CLIs and not
governed by these assertions.
"""

from __future__ import annotations

import ast
import io
import json
import inspect
from pathlib import Path
from typing import cast
from typing import Final

from outcomeeng import validation as pkg
from outcomeeng.validation import (
    HOOK_SAFETY_ARGV,
    FMT_CHECK_ARGV,
    MYPY_ARGV,
    PURPOSE_CONFORMANCE,
    PURPOSE_CORRECTNESS,
    PYRIGHT_ARGV,
    PYTEST_ARGV,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    RUFF_CHECK_ARGV,
    RUFF_FORMAT_ARGV,
    SPX_MARKDOWN_ARGV,
    STEPS,
    SUMMARY_KEY_PURPOSE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_VERIFICATION_TYPE,
    TEST_RECIPE,
    TEST_STEPS,
    VALIDATION_RECIPE,
    VALIDATION_STEPS,
    VERIFICATION_TYPE_TESTING,
    VERIFICATION_TYPE_VALIDATION,
    Step,
    run_check,
    run_recipe,
)
from outcomeeng_testing.harnesses.gate import RecordingSpawner

STATIC_ANALYSIS_ARGVS: Final = (RUFF_CHECK_ARGV, MYPY_ARGV, PYRIGHT_ARGV)
PASS: Final = 0
HIGH_VOLUME_CHILD_OUTPUT: Final = "\n".join("captured child output" for _ in range(200))


class TestDeclaredSteps:
    """Validation recipe includes validators; test recipe owns pytest."""

    def test_steps_is_non_empty_tuple_of_step(self) -> None:
        assert isinstance(STEPS, tuple)
        assert len(STEPS) >= 1
        for step in STEPS:
            assert isinstance(step, Step)

    def test_validation_recipe_reports_validation_conformance(self) -> None:
        assert VALIDATION_RECIPE.name == RECIPE_VALIDATION
        assert VALIDATION_RECIPE.verification_type == VERIFICATION_TYPE_VALIDATION
        assert VALIDATION_RECIPE.purpose == PURPOSE_CONFORMANCE

    def test_test_recipe_reports_testing_correctness(self) -> None:
        assert TEST_RECIPE.name == RECIPE_TEST
        assert TEST_RECIPE.verification_type == VERIFICATION_TYPE_TESTING
        assert TEST_RECIPE.purpose == PURPOSE_CORRECTNESS

    def test_steps_includes_fmt_check(self) -> None:
        assert any(step.argv == FMT_CHECK_ARGV for step in VALIDATION_STEPS)

    def test_steps_includes_ruff_check(self) -> None:
        assert any(step.argv == RUFF_CHECK_ARGV for step in VALIDATION_STEPS)

    def test_steps_includes_ruff_format(self) -> None:
        assert any(step.argv == RUFF_FORMAT_ARGV for step in VALIDATION_STEPS)

    def test_steps_include_mypy_strict_and_pyright(self) -> None:
        step_argvs = {step.argv for step in VALIDATION_STEPS}
        assert set(STATIC_ANALYSIS_ARGVS).issubset(step_argvs)
        assert "--strict" in MYPY_ARGV

    def test_steps_includes_spx_validation_markdown(self) -> None:
        assert any(step.argv == SPX_MARKDOWN_ARGV for step in VALIDATION_STEPS)

    def test_validation_recipe_excludes_pytest_step(self) -> None:
        assert PYTEST_ARGV not in {step.argv for step in VALIDATION_STEPS}

    def test_test_recipe_executes_only_pytest_evidence_step(self) -> None:
        assert TEST_STEPS == (Step(label="pytest", argv=PYTEST_ARGV),)


class TestVerificationVocabulary:
    """The check wrapper remains orchestration, not a verification type."""

    def test_check_name_is_wrapper_only(self) -> None:
        assert RECIPE_CHECK not in {
            VALIDATION_RECIPE.verification_type,
            TEST_RECIPE.verification_type,
        }

    def test_check_summary_has_no_verification_type(
        self,
        tmp_path: Path,
    ) -> None:
        summary_path = tmp_path / "check-summary.json"
        spawner = RecordingSpawner(
            exit_codes=[PASS]
            * (len(VALIDATION_RECIPE.preflight_steps) + len(VALIDATION_RECIPE.steps))
        )
        sink = io.StringIO()

        exit_code = run_check(
            spawner=spawner,
            sink=sink,
            recipes=(VALIDATION_RECIPE,),
            summary_path=summary_path,
        )

        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert isinstance(summary, dict)
        typed_summary = cast("dict[str, object]", summary)
        assert exit_code == PASS
        assert typed_summary[SUMMARY_KEY_RECIPE] == RECIPE_CHECK
        assert typed_summary[SUMMARY_KEY_VERIFICATION_TYPE] is None
        assert typed_summary[SUMMARY_KEY_PURPOSE] is None


class TestBoundedLiveOutput:
    """Passing child output is captured and omitted from the live sink."""

    def test_passing_child_output_is_not_streamed_line_by_line(self) -> None:
        recipe = TEST_RECIPE
        spawner = RecordingSpawner(
            exit_codes=[PASS, PASS],
            outputs=[HIGH_VOLUME_CHILD_OUTPUT, HIGH_VOLUME_CHILD_OUTPUT],
        )
        sink = io.StringIO()

        exit_code = run_recipe(spawner=spawner, sink=sink, recipe=recipe)

        output = sink.getvalue()
        assert exit_code == PASS
        assert HIGH_VOLUME_CHILD_OUTPUT not in output
        assert len(output.splitlines()) < len(HIGH_VOLUME_CHILD_OUTPUT.splitlines())

    def test_steps_includes_hook_safety(self) -> None:
        assert any(step.argv == HOOK_SAFETY_ARGV for step in STEPS)


def _package_modules() -> list[Path]:
    """Return the gate orchestrator's own modules.

    The `outcomeeng.validation` package contains the gate orchestrator
    (`_engine`, `_model`, `_spawner`, `_steps`, plus `__init__` and
    `__main__`) and four sibling validator CLIs (`plugins`,
    `skill_frontmatter`, `install`, `eval_links`). Only the gate's own
    modules — those whose filename starts with `_` — are governed by this
    spec's compliance assertions.
    """
    package_dir = Path(inspect.getfile(pkg)).parent
    return sorted(p for p in package_dir.glob("*.py") if p.name.startswith("_"))


def _subprocess_importers() -> list[Path]:
    importers: list[Path] = []
    for module_path in _package_modules():
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "subprocess" or alias.name.startswith(
                        "subprocess.",
                    ):
                        importers.append(module_path)
                        break
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module is not None
                and (
                    node.module == "subprocess" or node.module.startswith("subprocess.")
                )
            ):
                importers.append(module_path)
    return importers


class TestSubprocessImportContainment:
    """Exactly one module in the package imports `subprocess`."""

    def test_exactly_one_module_imports_subprocess(self) -> None:
        importers = _subprocess_importers()
        assert len(importers) == 1, (
            f"`subprocess` must be imported by exactly one module "
            f"(the production adapter); found: {importers}"
        )


def _find_function_def(tree: ast.AST, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def _signal_handler_source() -> str:
    """Return the source of every function that calls signal.signal()'s callback.

    The orchestrator registers handlers via signal.signal(). For source
    inspection, we walk every function in the package and pick those that
    call send_signal_to_group — the orchestrator's grace-period path.
    """
    fragments: list[str] = []
    for module_path in _package_modules():
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            calls = [
                child
                for child in ast.walk(node)
                if isinstance(child, ast.Call)
                and isinstance(child.func, ast.Attribute)
                and child.func.attr == "send_signal_to_group"
            ]
            if calls:
                fragments.append(ast.unparse(node))
    return "\n\n".join(fragments)


def _monotonic_call_count(func_source: str) -> int:
    tree = ast.parse(func_source)
    count = 0
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "monotonic"
        ):
            count += 1
    return count


class TestBoundedGracePeriod:
    """Signal waits are bounded by one deadline and a fixed post-kill check."""

    def test_signal_handler_computes_one_monotonic_deadline(self) -> None:
        source = _signal_handler_source()
        assert source, "no signal-handling function found in package"
        count = _monotonic_call_count(source)
        # Allow up to 2 calls: one to compute the deadline, one inside the
        # poll loop to compare against it.
        assert 1 <= count <= 2, (
            f"signal handler must use a single bounded deadline; "
            f"found {count} time.monotonic() calls"
        )

    def test_signal_handler_uses_fixed_count_post_kill_reap_check(self) -> None:
        source = _signal_handler_source()
        assert "range(_POST_KILL_REAP_ATTEMPTS)" in source


def _package_source_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in _package_modules())


class TestNoForbiddenWaitPatterns:
    """The orchestrator source contains no `gh run watch` or `while True: sleep`."""

    def test_no_gh_run_watch_literal(self) -> None:
        source = _package_source_text()
        assert "gh run watch" not in source

    def test_no_while_true_with_time_sleep(self) -> None:
        for module_path in _package_modules():
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.While):
                    continue
                test = node.test
                is_while_true = isinstance(test, ast.Constant) and test.value is True
                if not is_while_true:
                    continue
                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr == "sleep"
                    ):
                        msg = (
                            f"{module_path.name} contains a `while True:` loop "
                            f"with `time.sleep()` — forbidden polling pattern"
                        )
                        raise AssertionError(msg)


class TestProductionSpawnerSessionFlag:
    """The production ProcessSpawner adapter passes start_new_session=True."""

    def test_popen_call_includes_start_new_session_true(self) -> None:
        importers = _subprocess_importers()
        assert len(importers) == 1, (
            "production spawner module must be the sole subprocess importer"
        )
        spawner_path = importers[0]
        tree = ast.parse(spawner_path.read_text(encoding="utf-8"))
        popen_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Attribute) and node.func.attr == "Popen")
                or (isinstance(node.func, ast.Name) and node.func.id == "Popen")
            )
        ]
        assert popen_calls, "production spawner must call subprocess.Popen"
        for call in popen_calls:
            kwargs = {kw.arg: kw.value for kw in call.keywords}
            assert "start_new_session" in kwargs, (
                "Popen call must pass start_new_session"
            )
            value = kwargs["start_new_session"]
            assert isinstance(value, ast.Constant) and value.value is True, (
                "start_new_session must be the literal True"
            )
