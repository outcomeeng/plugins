"""The fixed step list for the marketplace's quality gate.

`STEPS` is intentionally a module-level constant rather than a config-driven
list. Drift in the gate's composition is a regression the fixed tuple guards
against.

The compliance test enforces that `("ruff", "format", "--check")`,
`("ruff", "check")`, the strict mypy package command, the pyright package
command, and `("spx", "validation", "markdown")` appear in the declared step
list.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from outcomeeng.distribution.orchestration import (
    BUILD_COMMAND_ARGV,
    DIST_DIFF_ARGV,
    ORCHESTRATION_VALIDATION_ARGV,
)
from outcomeeng.validation._model import Step

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]
PYTHON_SOURCE_PATHS: Final = ("outcomeeng", "outcomeeng_testing", "outcomeeng_evals")

RUFF_FORMAT_ARGV: Final = ("uv", "run", "ruff", "format", "--check", ".")
RUFF_CHECK_ARGV: Final = ("uv", "run", "ruff", "check", ".")
MYPY_ARGV: Final = ("uv", "run", "mypy", "--strict", *PYTHON_SOURCE_PATHS)
PYRIGHT_ARGV: Final = ("uv", "run", "pyright", *PYTHON_SOURCE_PATHS)
SPX_MARKDOWN_ARGV: Final = ("uv", "run", "spx", "validation", "markdown")
PYTEST_ARGV: Final = ("uv", "run", "python", "-m", "pytest")

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


STEPS: Final = (
    Step(label="build-skills", argv=BUILD_COMMAND_ARGV),
    Step(label="dist-diff", argv=DIST_DIFF_ARGV),
    Step(label="build-orchestration", argv=ORCHESTRATION_VALIDATION_ARGV),
    Step(label="fmt-check", argv=("dprint", "check")),
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
    Step(label="markdown", argv=SPX_MARKDOWN_ARGV),
    Step(label="pytest", argv=PYTEST_ARGV),
)
