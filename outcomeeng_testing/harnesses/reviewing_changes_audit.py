"""Static-inspection observations for the review-changes shipped scripts.

The compliance evidence under
``spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/``
asserts two portability boundaries over every script the skill ships:

- no script writes durable review state through direct filesystem primitives,
  outside the caller-owned review-input bundle exception ``compute_diff.py``
  holds and the runner-owned scratch state ``review_run.py`` holds;
- no script imports a third-party package, imports an ``outcomeeng`` or
  ``outcomeeng_*`` module, or references ``uv`` at runtime.

Every function here returns observations — the violations a source file
exhibits — and never a verdict; the linked test owns each predicate. The same
observers run against the real shipped scripts and against the violating
fixtures under ``outcomeeng_testing/fixtures/reviewing_changes/``.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

from outcomeeng_testing.harnesses.reviewing_changes import (
    COMPUTE_DIFF_SCRIPT,
    REPO_ROOT,
    REVIEW_RUN_SCRIPT,
    SCRIPTS_DIR,
)

VIOLATING_FIXTURES_DIR = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "reviewing_changes"
)
THIRD_PARTY_IMPORT_FIXTURE = VIOLATING_FIXTURES_DIR / "imports_third_party.py.txt"
OUTCOMEENG_IMPORT_FIXTURE = VIOLATING_FIXTURES_DIR / "imports_outcomeeng.py.txt"
RUNTIME_UV_FIXTURE = VIOLATING_FIXTURES_DIR / "references_uv.py.txt"
DIRECT_WRITE_FIXTURE = VIOLATING_FIXTURES_DIR / "writes_directly.py.txt"

# Filesystem-write primitives a shipped script MUST NOT call directly. Read
# primitives (``open(..., "rb")``, ``Path.read_bytes``, ``Path.read_text``) stay
# permitted because ``compute_diff.py`` legitimately reads the diff subprocess
# output and caller-provided payload files.
FORBIDDEN_NAME_CALLS = frozenset({"open"})
FORBIDDEN_ATTR_CALLS = frozenset(
    {
        ("os", "remove"),
        ("os", "rename"),
        ("os", "replace"),
        ("os", "unlink"),
        ("shutil", "rmtree"),
    }
)
FORBIDDEN_METHOD_NAMES = frozenset(
    {
        "replace",
        "rename",
        "rmdir",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
        "mkdir",
    }
)
COMPUTE_DIFF_ALLOWED_WRITE_CALLS = frozenset(
    {
        ("safe_bundle_dir", "mkdir"),
        ("diff_path", "write_text"),
        ("manifest_path", "write_text"),
    }
)
REVIEW_RUN_ALLOWED_WRITE_CALLS = frozenset(
    {
        ("path", "write_text"),
        ("shutil", "rmtree"),
    }
)
WRITE_MODE_RE = re.compile(r"[wax+]")

# Modules that ship beside each other under the skill's ``scripts/`` directory
# and import one another by bare name; they are neither third-party nor
# ``outcomeeng_*`` imports.
LOCAL_REVIEWING_CHANGES_MODULES = frozenset(
    {"review_result", "compute_diff", "journal_emit", "review_run"}
)


def script_files() -> list[pathlib.Path]:
    """Return every ``.py`` file under the review-changes ``scripts/`` directory."""
    if not SCRIPTS_DIR.is_dir():
        return []
    return [
        p for p in sorted(SCRIPTS_DIR.rglob("*.py")) if "__pycache__" not in p.parts
    ]


def _top_level_name(module: str) -> str:
    return module.split(".", 1)[0]


def imported_modules(source: str) -> list[str]:
    """Return the top-level module name of every absolute import in ``source``."""
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(_top_level_name(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0 or node.module is None:
                continue
            modules.append(_top_level_name(node.module))
    return modules


def non_stdlib_imports(script_path: pathlib.Path) -> list[str]:
    """Return the imports in ``script_path`` that are neither stdlib nor local siblings."""
    stdlib = set(sys.stdlib_module_names)
    source = script_path.read_text(encoding="utf-8")
    return [
        module
        for module in imported_modules(source)
        if module not in stdlib and module not in LOCAL_REVIEWING_CHANGES_MODULES
    ]


def outcomeeng_imports(script_path: pathlib.Path) -> list[str]:
    """Return the ``outcomeeng`` and ``outcomeeng_*`` imports in ``script_path``."""
    source = script_path.read_text(encoding="utf-8")
    return [
        module
        for module in imported_modules(source)
        if module == "outcomeeng" or module.startswith("outcomeeng_")
    ]


def runtime_uv_references(script_path: pathlib.Path) -> list[str]:
    """Return every string-literal ``uv`` reference in ``script_path`` with its line."""
    tree = ast.parse(script_path.read_text(encoding="utf-8"))
    return [
        f"runtime reference to 'uv' at line {node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and node.value == "uv"
    ]


def _string_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_string_argument(node: ast.Call, *, position: int, name: str) -> str | None:
    if len(node.args) > position:
        value = _string_literal(node.args[position])
        if value is not None:
            return value
    for keyword in node.keywords:
        if keyword.arg == name:
            return _string_literal(keyword.value)
    return None


def _path_open_write_violation(node: ast.Call, func: ast.Attribute) -> str | None:
    if func.attr != "open":
        return None
    mode = _call_string_argument(node, position=0, name="mode")
    if mode is not None and WRITE_MODE_RE.search(mode):
        return f".open({mode!r}) at line {node.lineno}"
    return None


def _attribute_write_violation(
    *, script_path: pathlib.Path, node: ast.Call, func: ast.Attribute
) -> str | None:
    value = func.value
    if script_path == COMPUTE_DIFF_SCRIPT and isinstance(value, ast.Name):
        if (value.id, func.attr) in COMPUTE_DIFF_ALLOWED_WRITE_CALLS:
            return None
    if script_path == REVIEW_RUN_SCRIPT and isinstance(value, ast.Name):
        if (value.id, func.attr) in REVIEW_RUN_ALLOWED_WRITE_CALLS:
            return None
    path_open_violation = _path_open_write_violation(node, func)
    if path_open_violation is not None:
        return path_open_violation
    if func.attr in FORBIDDEN_METHOD_NAMES:
        return f".{func.attr}() at line {func.lineno}"
    if isinstance(value, ast.Name) and (value.id, func.attr) in FORBIDDEN_ATTR_CALLS:
        return f"{value.id}.{func.attr}() at line {func.lineno}"
    return None


def direct_write_violations(script_path: pathlib.Path) -> list[str]:
    """Return every direct filesystem-write call in ``script_path``.

    The caller-owned bundle writes in ``compute_diff.py`` and the runner-owned
    scratch writes in ``review_run.py`` are the declared exceptions and are not
    reported for those two scripts.
    """
    tree = ast.parse(script_path.read_text(encoding="utf-8"))
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in FORBIDDEN_NAME_CALLS:
            violations.append(f"call to {func.id}() at line {node.lineno}")
        elif isinstance(func, ast.Attribute):
            violation = _attribute_write_violation(
                script_path=script_path, node=node, func=func
            )
            if violation is not None:
                violations.append(violation)
    return violations
