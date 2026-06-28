"""Compliance tests for cross-cutting review-changes rules.

Covers the Compliance clauses in ``../reviewing-changes.md`` that are
universal rules across the skill's files rather than per-case scenarios:

- Every script under ``plugins/spec-tree/skills/review-changes/scripts/``
  writes no durable review state. ``compute_diff.py`` may write only the
  caller-owned scratch review-input bundle files; the remaining scripts use no
  direct write primitives.
- The scripts/ directory holds the audit-parity set — the policy module
  plus ``compute_diff.py`` and ``journal_emit.py`` — with no parallel
  validation or renderer script, so the human surface comes only from the
  sealed journal prefix.
- No script under the skill's ``scripts/`` directory imports a third-party
  package, depends on ``uv`` at runtime, or imports any ``outcomeeng_*``
  module.
"""

from __future__ import annotations

import ast
import json
import pathlib
import re
import sys

import pytest

from outcomeeng_testing.harnesses.reviewing_changes import (
    COMPUTE_DIFF_SCRIPT,
    JOURNAL_EMIT_SCRIPT,
    REPO_ROOT,
    REVIEW_PROMPT_PATH,
    REVIEW_RESULT_MODULE_PATH,
    SCRIPTS_DIR,
    SKILL_DIR,
    load_journal_emit_module,
    make_review_result_dict,
    run_journal_emit_in_process,
)

# Filesystem-write primitives the scripts MUST NOT use directly. Read
# primitives (``open(..., 'rb')``, ``Path.read_bytes``, ``Path.read_text``)
# are permitted because ``compute_diff.py`` legitimately reads the diff
# subprocess's stdout and read user-provided payload/template files.
FORBIDDEN_NAME_CALLS = {"open"}
FORBIDDEN_ATTR_CALLS = {
    ("os", "remove"),
    ("os", "rename"),
    ("os", "replace"),
    ("os", "unlink"),
    ("shutil", "rmtree"),
}
FORBIDDEN_METHOD_NAMES = {
    "replace",
    "rename",
    "rmdir",
    "touch",
    "unlink",
    "write_bytes",
    "write_text",
    "mkdir",
}
COMPUTE_DIFF_ALLOWED_WRITE_CALLS = {
    ("safe_bundle_dir", "mkdir"),
    ("diff_path", "write_text"),
    ("manifest_path", "write_text"),
}
WRITE_MODE_RE = re.compile(r"[wax+]")

# Names of modules that ship under the review-changes scripts/ directory
# (sibling-imported via bare names) — these are not "third-party" or
# "outcomeeng_*" violations.
LOCAL_REVIEWING_CHANGES_MODULES = frozenset(
    {
        "review_result",
        "compute_diff",
        "journal_emit",
    }
)
je = load_journal_emit_module()


def _write_review_manifest(
    root: pathlib.Path,
    *,
    base_ref: str = "HEAD",
    head_ref: str = "HEAD",
) -> pathlib.Path:
    manifest = {
        "schema_version": je.MANIFEST_SCHEMA_VERSION,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "diff_path": "diff.md",
        "diff_sha256": "a" * 64,
        "diff_bytes": 1,
        "sections": [
            {
                "title": "Committed diff",
                "files": ["README.md"],
                "start_line": 1,
                "line_count": 1,
                "byte_start": 0,
                "byte_length": 1,
            }
        ],
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _script_files() -> list[pathlib.Path]:
    """Return every ``.py`` file under the review-changes ``scripts/`` dir."""
    if not SCRIPTS_DIR.is_dir():
        return []
    return [
        p for p in sorted(SCRIPTS_DIR.rglob("*.py")) if "__pycache__" not in p.parts
    ]


def _top_level_name(module: str) -> str:
    return module.split(".", 1)[0]


def _imported_modules(source: str) -> list[str]:
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(_top_level_name(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                continue
            if node.module is None:
                continue
            modules.append(_top_level_name(node.module))
    return modules


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
    path_open_violation = _path_open_write_violation(node, func)
    if path_open_violation is not None:
        return path_open_violation
    if func.attr in FORBIDDEN_METHOD_NAMES:
        return f".{func.attr}() at line {func.lineno}"
    if isinstance(value, ast.Name) and (value.id, func.attr) in FORBIDDEN_ATTR_CALLS:
        return f"{value.id}.{func.attr}() at line {func.lineno}"
    return None


def _direct_write_violations(script_path: pathlib.Path) -> list[str]:
    source = script_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
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


def _runtime_uv_violations(script_path: pathlib.Path) -> list[str]:
    source = script_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    violations: list[str] = []
    for node in ast.walk(tree):
        value = _string_literal(node)
        if value == "uv":
            violations.append(f"runtime reference to 'uv' at line {node.lineno}")
    return violations


class TestScriptsDoNotWriteStorageDirectly:
    """Review scripts write no durable review state directly."""

    @pytest.mark.parametrize(
        "script_path",
        [
            REVIEW_RESULT_MODULE_PATH,
            COMPUTE_DIFF_SCRIPT,
            JOURNAL_EMIT_SCRIPT,
        ],
    )
    def test_script_uses_no_direct_write_primitives(
        self, script_path: pathlib.Path
    ) -> None:
        violations = _direct_write_violations(script_path)
        assert not violations, (
            f"{script_path.name} uses forbidden direct-write filesystem "
            f"primitives outside the caller-owned review-input bundle exception: "
            f"{'; '.join(violations)}"
        )


class TestScriptsAreStdlibOnly:
    """No script imports a third-party package or any ``outcomeeng_*`` module."""

    def test_no_third_party_or_outcomeeng_imports(self) -> None:
        violations: list[str] = []
        stdlib = set(sys.stdlib_module_names)
        for script in _script_files():
            source = script.read_text(encoding="utf-8")
            for module in _imported_modules(source):
                if module in stdlib:
                    continue
                if module in LOCAL_REVIEWING_CHANGES_MODULES:
                    continue
                violations.append(f"{script.name}: import '{module}'")
        assert not violations, (
            "review-changes scripts import non-stdlib, non-local modules:\n"
            + "\n".join(violations)
        )

    def test_no_outcomeeng_imports(self) -> None:
        violations: list[str] = []
        for script in _script_files():
            source = script.read_text(encoding="utf-8")
            for module in _imported_modules(source):
                if module.startswith("outcomeeng_") or module == "outcomeeng":
                    violations.append(f"{script.name}: import '{module}'")
        assert not violations, (
            "review-changes scripts import outcomeeng_* modules "
            "(forbidden by Plugin Portability Constraints):\n" + "\n".join(violations)
        )

    def test_no_runtime_uv_references(self) -> None:
        violations: list[str] = []
        for script in _script_files():
            for violation in _runtime_uv_violations(script):
                violations.append(f"{script.name}: {violation}")
        assert not violations, (
            "review-changes scripts reference uv at runtime "
            "(forbidden by Plugin Portability Constraints):\n" + "\n".join(violations)
        )


class TestNoSecondSchemaRepresentation:
    """The schema lives in one Python module. Alternate representations forbidden.

    ADR clause: ``review_result.py`` is the canonical schema; a JSON
    Schema document, OpenAPI fragment, or duplicate dataclass set would
    invite drift between representations. The check globs the skill
    directory for the artifact shapes a second representation would
    take.
    """

    def test_no_alternate_schema_file_exists(self) -> None:
        forbidden_globs = ("*.schema.json", "*.xsd", "openapi.*", "schema.*")
        violations: list[str] = []
        for pattern in forbidden_globs:
            for match in SKILL_DIR.rglob(pattern):
                if "__pycache__" in match.parts:
                    continue
                violations.append(str(match.relative_to(SKILL_DIR)))
        assert not violations, (
            "alternate schema representation found in review-changes "
            f"skill directory (forbidden — the canonical schema lives in "
            f"review_result.py): {violations}"
        )


class TestComputeDiffHasNoThreadAddressing:
    """``compute_diff.py`` does not accept thread-addressing arguments."""

    def test_compute_diff_has_no_slug_argument(self) -> None:
        if not COMPUTE_DIFF_SCRIPT.is_file():
            pytest.skip("compute_diff.py not yet present")
        source = COMPUTE_DIFF_SCRIPT.read_text(encoding="utf-8")
        assert "--slug" not in source
        assert "thread_store" not in source


# The audit-parity script set: the policy module plus the two CLI scripts.
# No parallel validation script (`validate_review_result.py`) and no parallel
# renderer (`render_review.py`) — validity is the `journal_emit finding-reported`
# per-finding parse, and the human surface is rendered only from the sealed
# journal prefix.
EXPECTED_SCRIPT_NAMES = frozenset(
    {"__init__.py", "review_result.py", "compute_diff.py", "journal_emit.py"}
)


class TestNoParallelReviewResultRenderer:
    """The human surface is rendered only from the sealed journal prefix.

    ``reviewing-changes.md`` NEVER clause: no script renders a parallel
    surface from the review-result JSON payload — the journal is the
    review's sole source of truth. The deleted ``render_review.py`` was
    exactly that parallel renderer; its absence, and the absence of a
    render-templates directory it consumed, is the falsifiable evidence.
    """

    def test_script_set_is_the_audit_parity_set(self) -> None:
        present = {p.name for p in _script_files()}
        unexpected = present - EXPECTED_SCRIPT_NAMES
        assert not unexpected, (
            "review-changes scripts/ carries unexpected scripts "
            f"(audit parity is {sorted(EXPECTED_SCRIPT_NAMES)}): {sorted(unexpected)}"
        )
        assert "render_review.py" not in present, (
            "render_review.py renders a parallel surface from the review-result "
            "JSON — the surface is rendered only from the sealed journal prefix"
        )
        assert "validate_review_result.py" not in present, (
            "validate_review_result.py is the removed parallel validation script "
            "— validity is the journal_emit finding-reported per-finding parse, "
            "matching the audit kind"
        )

    def test_no_render_templates_directory(self) -> None:
        render_dir = REVIEW_PROMPT_PATH.parent / "render"
        assert not render_dir.exists(), (
            f"{render_dir} holds render templates for the removed parallel "
            "renderer — the surface comes from the shared journal projection"
        )

    def test_render_command_projects_from_journal_events(
        self, tmp_path: pathlib.Path
    ) -> None:
        manifest_path = _write_review_manifest(tmp_path)
        metadata = run_journal_emit_in_process(
            "metadata",
            "--started-at",
            "2026-01-01T00:00:00Z",
            "--manifest",
            str(manifest_path),
            repo=REPO_ROOT,
            env={
                je.ENV_BASE_REF: "HEAD",
                je.ENV_HEAD_REF: "HEAD",
                je.ENV_BRANCH: "work/example",
            },
        )
        assert metadata.returncode == 0, metadata.stderr

        finding = make_review_result_dict()["findings"][0]
        finding_event = run_journal_emit_in_process(
            "finding-reported",
            "--now",
            "2026-01-01T00:00:00Z",
            stdin=json.dumps(finding),
        )
        assert finding_event.returncode == 0, finding_event.stderr

        event_prefix = [json.loads(finding_event.stdout)]
        run_completed = run_journal_emit_in_process(
            "run-completed",
            "--now",
            "2026-01-01T00:00:01Z",
            "--completed-at",
            "2026-01-01T00:00:01Z",
            "--metadata",
            metadata.stdout,
            stdin=json.dumps(event_prefix),
        )
        assert run_completed.returncode == 0, run_completed.stderr

        rendered = run_journal_emit_in_process(
            "render",
            stdin=json.dumps([*event_prefix, json.loads(run_completed.stdout)]),
        )
        assert rendered.returncode == 0, rendered.stderr
        payload = json.loads(rendered.stdout)
        assert payload["countLine"] == "BLOCKING: 0, DEBT: 1"
        assert payload["overall"] == "approved"
        assert finding["message"] in payload["surface"]
        assert finding["action"] in payload["surface"]
        assert "**Overall: approved (status: approved)**" in payload["surface"]
