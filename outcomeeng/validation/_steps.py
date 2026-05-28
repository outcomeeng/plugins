"""The fixed step list for the marketplace's quality gate.

`STEPS` is intentionally a module-level constant rather than a config-driven
list. Drift in the gate's composition is the regression `spx/ISSUES.md`
records; the fixed tuple is the safeguard.

The compliance test enforces that `("ruff", "check")` and
`("spx", "validation", "markdown")` appear as contiguous argv subsequences
in at least one step each.
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


STEPS: Final = (
    Step(label="build-skills", argv=BUILD_COMMAND_ARGV),
    Step(label="dist-diff", argv=DIST_DIFF_ARGV),
    Step(label="build-orchestration", argv=ORCHESTRATION_VALIDATION_ARGV),
    Step(label="fmt-check", argv=("dprint", "check")),
    Step(label="ruff", argv=("uv", "run", "ruff", "check", ".")),
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
    Step(label="markdown", argv=("uv", "run", "spx", "validation", "markdown")),
    Step(label="pytest", argv=("uv", "run", "python", "-m", "pytest")),
)
