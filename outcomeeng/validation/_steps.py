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

from outcomeeng.validation._model import Step

_REPO_ROOT: Final = Path(__file__).resolve().parents[2]


def _skill_files() -> tuple[str, ...]:
    plugins_dir = _REPO_ROOT / "plugins"
    return tuple(sorted(str(path) for path in plugins_dir.rglob("SKILL.md")))


STEPS: Final = (
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
        label="docs-check",
        argv=(
            "uv",
            "run",
            "python",
            "-m",
            "outcomeeng.scripts.generate_plugin_catalog",
            "--check",
        ),
    ),
    Step(label="markdown", argv=("uv", "run", "spx", "validation", "markdown")),
    Step(label="pytest", argv=("uv", "run", "python", "-m", "pytest")),
)
