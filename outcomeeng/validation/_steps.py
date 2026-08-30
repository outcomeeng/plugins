"""The fixed recipe definitions for the marketplace verification gate.

The primitive recipe step lists are intentionally module-level constants rather
than config-driven lists. Drift in recipe composition is a regression the fixed
tuples guard against.

The compliance test enforces that the workflow lint, shell lint,
`("ruff", "format", "--check")`, `("ruff", "check")`, the strict mypy package
command, the pyright package command, and `("spx", "validation", "markdown")`
appear in the validation recipe. Pytest-backed `[test]` evidence belongs to
the test recipe.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Final

from outcomeeng.distribution.contracts import (
    BUILD_COMMAND_ARGV,
    DIST_DIFF_ARGV,
    INSTRUCTION_BLOCK_ARGV as _INSTRUCTION_BLOCK_ARGV,
    ORCHESTRATION_VALIDATION_ARGV,
    TEXT_FILE_SUFFIXES,
)
from outcomeeng.validation._model import Recipe, Step

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PYTHON_SOURCE_PATHS: Final = ("outcomeeng", "outcomeeng_testing", "outcomeeng_evals")
INSTRUCTION_BLOCK_ARGV: Final = _INSTRUCTION_BLOCK_ARGV

RECIPE_VALIDATION: Final = "validation"
RECIPE_TEST: Final = "test"
RECIPE_CHECK: Final = "check"
RECIPE_AD_HOC: Final = "ad-hoc"
VERIFICATION_TYPE_VALIDATION: Final = "validation"
VERIFICATION_TYPE_TESTING: Final = "testing"
PURPOSE_CONFORMANCE: Final = "conformance"
PURPOSE_CORRECTNESS: Final = "correctness"

UV_IMPORT_PREFLIGHT_ARGV: Final = ("uv", "run", "python", "-c", "import outcomeeng")
ACTIONLINT_ARGV: Final = ("actionlint",)
SHELLCHECK_ARGV: Final = (
    "uv",
    "run",
    "python",
    "-m",
    "outcomeeng.validation.shellcheck",
)
FMT_CHECK_ARGV: Final = ("dprint", "check")
RUFF_FORMAT_ARGV: Final = ("uv", "run", "ruff", "format", "--check", ".")
RUFF_CHECK_ARGV: Final = ("uv", "run", "ruff", "check", ".")
MYPY_ARGV: Final = ("uv", "run", "mypy", "--strict", *PYTHON_SOURCE_PATHS)
PYRIGHT_ARGV: Final = ("uv", "run", "pyright", *PYTHON_SOURCE_PATHS)
SPX_MARKDOWN_ARGV: Final = ("uv", "run", "spx", "validation", "markdown")
DIST_DIFF_STEP_LABEL: Final = "dist-diff"
SPX_VERSION_FLOOR_ARGV: Final = (
    "uv",
    "run",
    "python",
    "-m",
    "outcomeeng.validation.spx_version",
)
HOOK_SAFETY_ARGV: Final = (
    "uv",
    "run",
    "python",
    "-m",
    "outcomeeng.validation.hook_safety",
)
FOUNDATION_MANIFEST_ARGV: Final = (
    "uv",
    "run",
    "python",
    "-m",
    "outcomeeng.validation.foundation_manifest",
)
PYTEST_ARGV: Final = ("uv", "run", "python", "-m", "pytest")

# Generated eval artifacts. Both derive from `eval.toml` definitions and the
# producers those definitions name; both fail the gate when the committed
# artifact drifts from what the source now renders.
EVALS_ROOT: Final = "spx"
EVAL_TRIGGER_WORKFLOW: Final = ".github/workflows/spec-tree-evals.yml"
EVAL_TRIGGERS_ARGV: Final = (
    "uv",
    "run",
    "outcomeeng-evals",
    "materialize-ci-triggers",
    EVALS_ROOT,
    "--workflow",
    EVAL_TRIGGER_WORKFLOW,
    "--repo-root",
    ".",
    "--check",
)
EVAL_PROMPTS_ARGV: Final = (
    "uv",
    "run",
    "outcomeeng-evals",
    "materialize-prompts",
    EVALS_ROOT,
    "--repo-root",
    ".",
    "--check",
)

# Shipped authored text under src/plugins/ where a non-portable reference can hide.
_REFERENCE_SUFFIXES: Final = (".md", ".py", ".json", ".toml", ".yaml", ".yml")


def _skill_files() -> tuple[str, ...]:
    roots = (
        _REPO_ROOT / "src" / "plugins",
        _REPO_ROOT / "dist" / "claude",
        _REPO_ROOT / "dist" / "codex",
    )
    return tuple(
        sorted(
            str(path)
            for root in roots
            if root.is_dir()
            for path in root.rglob("SKILL.md")
        )
    )


def _reference_files() -> tuple[str, ...]:
    root = _REPO_ROOT / "src" / "plugins"
    if not root.is_dir():
        return ()
    return tuple(
        sorted(
            str(path)
            for path in root.rglob("*")
            if path.is_file() and path.suffix in _REFERENCE_SUFFIXES
        )
    )


def _authored_text_files() -> tuple[str, ...]:
    """Return every authored text file the build renders or inlines.

    Plugin content, the shared fragments plugin files include, and the
    per-plugin templates that fan out into every plugin's generated tree.
    Content in any of the three reaches a generated target, so every rule
    enforcing a property of shipped content reads this one set — declared here
    once so a new root or suffix cannot reach one rule and miss another.
    """
    roots = (
        _REPO_ROOT / "src" / "plugins",
        _REPO_ROOT / "src" / "_shared",
        _REPO_ROOT / "src" / "templates",
    )
    return tuple(
        sorted(
            str(path)
            for root in roots
            if root.is_dir()
            for path in root.rglob("*")
            if path.is_file() and path.suffix in TEXT_FILE_SUFFIXES
        )
    )


def runtime_token_files() -> tuple[str, ...]:
    # A raw runtime token in authored content ships into a generated target.
    return _authored_text_files()


def scratch_path_files() -> tuple[str, ...]:
    # A fixed temporary path in authored content ships to the consumer, where it
    # collides across concurrent runs and writes outside the session boundary.
    return _authored_text_files()


PREFLIGHT_STEPS: Final = (
    Step(label="preflight-uv-import", argv=UV_IMPORT_PREFLIGHT_ARGV),
)

VALIDATION_STEPS: Final = (
    Step(label="build-skills", argv=BUILD_COMMAND_ARGV),
    Step(label=DIST_DIFF_STEP_LABEL, argv=DIST_DIFF_ARGV),
    Step(label="instructions-diff", argv=INSTRUCTION_BLOCK_ARGV),
    Step(label="build-orchestration", argv=ORCHESTRATION_VALIDATION_ARGV),
    Step(label="fmt-check", argv=FMT_CHECK_ARGV),
    Step(label="actionlint", argv=ACTIONLINT_ARGV),
    Step(label="shellcheck", argv=SHELLCHECK_ARGV),
    Step(label="ruff-format", argv=RUFF_FORMAT_ARGV),
    Step(label="ruff", argv=RUFF_CHECK_ARGV),
    Step(label="mypy", argv=MYPY_ARGV),
    Step(label="pyright", argv=PYRIGHT_ARGV),
    Step(
        label="manifests",
        argv=("uv", "run", "python", "-m", "outcomeeng.validation.plugins", "."),
    ),
    Step(
        label="skills",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.validation.skill_frontmatter",
            *_skill_files(),
        ),
    ),
    Step(
        label="skill-injection",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.validation.skill_injection_safety",
            *_skill_files(),
        ),
    ),
    Step(
        label="reference-portability",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.validation.reference_portability",
            *_reference_files(),
        ),
    ),
    Step(
        label="runtime-token",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.validation.runtime_tokens",
            *runtime_token_files(),
        ),
    ),
    Step(
        label="scratch-paths",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.validation.scratch_paths",
            *scratch_path_files(),
        ),
    ),
    Step(
        label="grant-locality",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.validation.grant_locality",
            *_skill_files(),
        ),
    ),
    Step(
        label="hook-safety",
        argv=HOOK_SAFETY_ARGV,
    ),
    Step(
        label="foundation-manifest",
        argv=FOUNDATION_MANIFEST_ARGV,
    ),
    Step(
        label="docs-check",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.catalog.plugin_catalog",
            "--check",
        ),
    ),
    Step(label="eval-triggers", argv=EVAL_TRIGGERS_ARGV),
    Step(label="eval-prompts", argv=EVAL_PROMPTS_ARGV),
    Step(label="markdown", argv=SPX_MARKDOWN_ARGV),
    Step(label="spx-version", argv=SPX_VERSION_FLOOR_ARGV),
)

TEST_STEPS: Final = (Step(label="pytest", argv=PYTEST_ARGV),)

VALIDATION_RECIPE: Final = Recipe(
    name=RECIPE_VALIDATION,
    verification_type=VERIFICATION_TYPE_VALIDATION,
    purpose=PURPOSE_CONFORMANCE,
    preflight_steps=PREFLIGHT_STEPS,
    steps=VALIDATION_STEPS,
)

TEST_RECIPE: Final = Recipe(
    name=RECIPE_TEST,
    verification_type=VERIFICATION_TYPE_TESTING,
    purpose=PURPOSE_CORRECTNESS,
    preflight_steps=PREFLIGHT_STEPS,
    steps=TEST_STEPS,
)

CHECK_RECIPES: Final = (VALIDATION_RECIPE, TEST_RECIPE)


def test_recipe(pytest_args: Sequence[str] = ()) -> Recipe:
    """Return the test recipe with caller-provided pytest arguments appended."""

    if not pytest_args:
        return TEST_RECIPE
    return Recipe(
        name=TEST_RECIPE.name,
        verification_type=TEST_RECIPE.verification_type,
        purpose=TEST_RECIPE.purpose,
        preflight_steps=TEST_RECIPE.preflight_steps,
        steps=(Step(label="pytest", argv=(*PYTEST_ARGV, *pytest_args)),),
    )
