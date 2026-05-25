"""Compliance tests for the CRUD CLI scripts.

Covers the Compliance clauses in ``../thread-store.md`` and
``../21-backend-abstraction.adr.md`` that constrain CLI behavior as
universal rules:

- Every CRUD CLI invokes the ``thread_store`` facade for filesystem
  effects — verified by AST inspection that each CLI calls one of
  ``thread_store.write``, ``thread_store.read``, ``thread_store.delete``,
  ``thread_store.list``, or ``thread_store.get_backend``.
- No CRUD CLI calls ``open()``, ``os.remove``/``os.unlink``,
  ``shutil.rmtree``, or ``Path.write_text``/``write_bytes``/``unlink`` —
  verified by AST inspection.
- Every CRUD CLI's ``--slug`` argparse argument is optional and falls
  back to ``thread_store.current_slug()`` when omitted — verified by
  source-level inspection of the ``add_argument`` call.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

from outcomeeng_testing.harnesses.thread_store import (
    DELETE_RECORD_SCRIPT,
    LIST_RECORDS_SCRIPT,
    READ_RECORD_SCRIPT,
    WRITE_RECORD_SCRIPT,
)


FACADE_ENTRY_POINTS = {"write", "read", "delete", "list", "get_backend"}


class TestCliRoutesThroughFacade:
    """AST inspection: every CLI calls the facade for filesystem effects.

    Substring matching is insufficient — a script that mentions
    ``thread_store.write`` only inside a comment would pass. The AST
    walk inspects actual call expressions, ignoring string and comment
    content.
    """

    @pytest.mark.parametrize(
        "script_path",
        [
            WRITE_RECORD_SCRIPT,
            READ_RECORD_SCRIPT,
            DELETE_RECORD_SCRIPT,
            LIST_RECORDS_SCRIPT,
        ],
    )
    def test_script_calls_facade_entry_point(self, script_path: pathlib.Path) -> None:
        source = script_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        facade_calls: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            value = func.value
            if not isinstance(value, ast.Name):
                continue
            # ``thread_store.write(...)``, ``thread_store.read(...)``, etc.
            if value.id == "thread_store" and func.attr in FACADE_ENTRY_POINTS:
                facade_calls.append(func.attr)
        assert facade_calls, (
            f"{script_path.name} does not call any thread_store facade entry "
            f"point ({sorted(FACADE_ENTRY_POINTS)})"
        )


class TestCliAvoidsDirectFilesystemPrimitives:
    """AST inspection: every CLI avoids direct filesystem write primitives.

    Walks every ``ast.Call`` and flags ``open(...)``, ``os.remove(...)``,
    ``os.unlink(...)``, ``shutil.rmtree(...)``, and method calls named
    ``write_text``, ``write_bytes``, or ``unlink``. Read-only ``open(...,
    'rb')`` and similar reads are nonetheless flagged because the CLIs'
    read entry point is ``thread_store.read``; a CLI that needs to read
    from a *user-provided* payload file (e.g. ``write_record.py --file``)
    accesses ``args.file.read_bytes()`` which is permitted — that call
    is on the user's input file, not on the thread-store storage.

    The test scope limits the AST scan to module-level ``ast.Call``
    nodes; ``Path.read_bytes()`` against ``args.file`` does not appear in
    the forbidden set.
    """

    @pytest.mark.parametrize(
        "script_path",
        [
            WRITE_RECORD_SCRIPT,
            READ_RECORD_SCRIPT,
            DELETE_RECORD_SCRIPT,
            LIST_RECORDS_SCRIPT,
        ],
    )
    def test_script_uses_no_forbidden_primitives(
        self, script_path: pathlib.Path
    ) -> None:
        source = script_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_attr_calls = {
            ("os", "remove"),
            ("os", "unlink"),
            ("shutil", "rmtree"),
        }
        forbidden_method_names = {"write_text", "write_bytes", "unlink"}
        forbidden_name_calls = {"open"}

        violations: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id in forbidden_name_calls:
                violations.append(f"call to {func.id}() at line {node.lineno}")
            elif isinstance(func, ast.Attribute):
                if func.attr in forbidden_method_names:
                    violations.append(f".{func.attr}() at line {node.lineno}")
                value = func.value
                if (
                    isinstance(value, ast.Name)
                    and (value.id, func.attr) in forbidden_attr_calls
                ):
                    violations.append(f"{value.id}.{func.attr}() at line {node.lineno}")
        assert not violations, (
            f"{script_path.name} uses forbidden filesystem primitives: "
            + "; ".join(violations)
        )


class TestCrudCliSlugIsOptional:
    """Source-level check: ``--slug`` is optional on every CRUD CLI.

    The agent never names the thread address; every CRUD CLI falls back
    to ``thread_store.current_slug()`` when ``--slug`` is omitted.
    Guards against an accidental regression where ``--slug`` is made
    ``required=True`` again. Mirrors the analogous
    ``TestComputeDiffSlugIsOptional`` check in the reviewing-changes
    verification skill's compliance test.
    """

    @pytest.mark.parametrize(
        "script_path",
        [
            WRITE_RECORD_SCRIPT,
            READ_RECORD_SCRIPT,
            DELETE_RECORD_SCRIPT,
            LIST_RECORDS_SCRIPT,
        ],
    )
    def test_slug_argument_is_optional(self, script_path: pathlib.Path) -> None:
        source = script_path.read_text(encoding="utf-8")
        slug_arg_match = re.search(
            r"add_argument\(\s*['\"]--slug['\"][^)]*\)", source, re.DOTALL
        )
        assert slug_arg_match is not None, (
            f"{script_path.name} must declare a --slug argparse argument so "
            "callers can override slug derivation in tests"
        )
        assert "required=True" not in slug_arg_match.group(0), (
            f"{script_path.name} --slug must NOT be required=True — the CLI "
            "derives the slug via thread_store.current_slug() when omitted"
        )
