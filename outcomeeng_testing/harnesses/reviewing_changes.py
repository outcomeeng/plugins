"""Harness for review-changes scenario, property, and compliance tests.

Provides the shared scaffolding consumed by every test file under
``spx/21-spec-tree.enabler/68-reviewing.enabler/21-reviewing-changes.enabler/tests/``:

- ``SCRIPTS_DIR`` and the per-script paths derived from it. A single source
  keeps every test file from walking ``__file__.parents[...]`` to find
  ``src/plugins/spec-tree/skills/review-changes/scripts``.
- ``REFERENCES_DIR`` and ``REVIEW_PROMPT_PATH``. Tests that assert the
  swappable prompt is a standalone reference file consume the path from
  one source.
- ``SKILL_DIR`` and ``SKILL_FILE``. The compliance tests inspect skill
  prose for the absence of an embedded prompt and presence of a
  ``${CLAUDE_SKILL_DIR}/references/review-prompt.md`` load expression.
- ``WRAPPER_AGENT_PATH``. Compliance tests check the wrapper agent's
  frontmatter shape when the agent file exists; missing files are
  tolerated (the agent is authored in a separate step).
- ``load_review_result_module``. An importlib loader for the
  ``review_result`` policy module, mirroring the pattern that
  ``outcomeeng_testing/harnesses/thread_store.py`` uses for the
  ``thread_store`` facade.
- ``run_script``. A thin ``subprocess.run`` wrapper that mirrors the
  thread-store harness contract for CLI invocations.
- ``make_review_result_dict``. Factory that returns a synthetic
  ``review-result`` JSON-ready dict with every required field populated,
  ready to be mutated by callers to construct invalid documents for
  rejection-path tests.

The harness lives in ``outcomeeng_testing/harnesses/`` per
``spx/15-test-infrastructure.pdr.md`` — shared test scaffolding is
production code with its home outside ``tests/`` and outside ``spx/``.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
from types import ModuleType
from typing import Any

# Two ``parents`` hops land at the repository root: this file lives at
# ``outcomeeng_testing/harnesses/reviewing_changes.py``.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

SKILL_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "skills" / "review-changes"
SKILL_FILE = SKILL_DIR / "SKILL.md"
SCRIPTS_DIR = SKILL_DIR / "scripts"
REFERENCES_DIR = SKILL_DIR / "references"
REVIEW_PROMPT_PATH = REFERENCES_DIR / "review-prompt.md"

REVIEW_RESULT_MODULE_PATH = SCRIPTS_DIR / "review_result.py"
VALIDATE_REVIEW_RESULT_SCRIPT = SCRIPTS_DIR / "validate_review_result.py"
COMPUTE_DIFF_SCRIPT = SCRIPTS_DIR / "compute_diff.py"
RENDER_REVIEW_SCRIPT = SCRIPTS_DIR / "render_review.py"

WRAPPER_AGENT_PATH = (
    REPO_ROOT / "src" / "plugins" / "spec-tree" / "agents" / "changes-reviewer.md"
)
RENDER_TEMPLATES_DIR = REFERENCES_DIR / "render"

# Fixture rule citation: a real path-style citation that satisfies the
# parser's rule-form check. Points at this verification skill's own spec so the citation
# is stable and self-contained — no external rule required.
FIXTURE_RULE_CITATION = (
    "spx/21-spec-tree.enabler/68-reviewing.enabler/"
    "21-reviewing-changes.enabler/reviewing-changes.md:ALWAYS:1"
)


def load_review_result_module() -> ModuleType:
    """Load the ``review_result`` policy module via importlib.

    The review-changes scripts ship under ``src/plugins/`` (the authored
    plugin source directory) and are not importable as a package.
    Tests that introspect ``SCHEMA_VERSION``, the ``Severity`` /
    ``Concern`` enums, the frozen ``Finding`` /
    ``ReviewResult`` dataclasses, or the ``parse_json`` /
    ``ReviewResultValidationError`` entry points load the module here.

    Returns the already-loaded module on subsequent calls so the importlib
    loader runs at most once per test session.
    """
    cached = sys.modules.get("review_result")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "review_result", REVIEW_RESULT_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load review_result from {REVIEW_RESULT_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_result"] = module
    spec.loader.exec_module(module)
    return module


def load_render_review_module() -> ModuleType:
    """Load the ``render_review`` script as a module via importlib.

    Mirrors :func:`load_review_result_module`. Tests that introspect the
    severity → render-class partitioning function or the template-loading
    helpers load the module here. ``render_review`` itself imports
    ``review_result`` and ``thread_store``; both are wired via sibling
    importlib in the script.
    """
    cached = sys.modules.get("render_review")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("render_review", RENDER_REVIEW_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load render_review from {RENDER_REVIEW_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["render_review"] = module
    spec.loader.exec_module(module)
    return module


def run_script(
    script: pathlib.Path,
    *args: str,
    stdin: str | None = None,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke a script as a subprocess and return the result.

    Mirrors the thread-store harness ``run_script`` contract: capture
    stdout/stderr, text mode, optional stdin payload, optional explicit
    environment. ``check=False`` is the default so tests can inspect
    returncode explicitly; success-path tests pass ``check=True``.
    """
    return subprocess.run(  # noqa: S603 — script path comes from the harness, not user input
        [sys.executable, str(script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        check=check,
        env=env,
    )


def make_review_result_dict(
    *,
    findings: list[dict[str, Any]] | None = None,
    acknowledgements: list[str] | None = None,
    summary: str = "Synthetic review for harness tests.",
    schema_version: int | None = None,
) -> dict[str, Any]:
    """Return a synthetic review-result dict with every required field.

    Default shape: one ``debt``-severity finding under the
    ``standards`` concern, one acknowledgement, and a summary. The debt
    finding carries an ``action`` populated with a required change to
    satisfy the required-field check. The defaults make the conforming
    case the trivial caller; rejection-path tests mutate one field on the
    returned dict to construct each violation.

    ``schema_version`` defaults to the module-level ``SCHEMA_VERSION``
    from the loaded ``review_result`` module so tests automatically pick
    up future bumps without re-asserting the version.
    """
    review_result = load_review_result_module()
    version = (
        schema_version if schema_version is not None else review_result.SCHEMA_VERSION
    )
    if findings is None:
        findings = [
            {
                "id": "F-001",
                "concern": review_result.Concern.STANDARDS,
                "severity": review_result.Severity.DEBT,
                "file": "example.py",
                "line": 10,
                "rule": FIXTURE_RULE_CITATION,
                "message": "The identifier is not descriptive.",
                "action": "Rename the symbol to convey its role.",
            }
        ]
    if acknowledgements is None:
        acknowledgements = ["The change improves type coverage."]
    return {
        "schema_version": version,
        "summary": summary,
        "findings": findings,
        "acknowledgements": acknowledgements,
    }
