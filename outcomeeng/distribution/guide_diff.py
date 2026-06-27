"""Actionable spx-guide writer and drift reporter for the validation gate.

The ``just build-guides`` recipe and the ``just guide-check`` gate run this module
to enforce the render-model ADR's gate: regenerate ``spx/CLAUDE.md`` and
``spx/AGENTS.md`` from the rendered runtime templates committed under ``dist/``,
then fail when either guide drifts from its committed content. It is the guide
analogue of ``dist-diff``: authored templates first become runtime-specific plugin
output, then the product guide files render from that output.

A guide absent from the index — a first run, or a worktree where the guides were
never committed — registers as drift via ``--intent-to-add``, because a plain
``git diff`` reports only tracked changes and would otherwise pass silently while
leaving the freshly written guides uncommitted.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, Protocol, cast

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
_GENERATOR: Final = (
    REPO_ROOT / "src/plugins/spec-tree/skills/update-spx/scripts/update_spx.py"
)
DIST_TEMPLATE_RELATIVE_PATH: Final = Path(
    "spec-tree/skills/understand/templates/spx-claude.md"
)
HEADER: Final = "spx/ guide files differ from a fresh render."
REMEDIATION: Final = "Run `just build-guides` and commit the regenerated spx/CLAUDE.md and spx/AGENTS.md."
UNRESOLVED_BUILD_TEMPLATE_TOKENS: Final = ("{{!", "!}}", "{!%", "%!}", "{!#", "#!}")
BUILD_GUIDES_RECIPE: Final = "build-guides"
GUIDE_CHECK_RECIPE: Final = "guide-check"
WRITE_FLAG: Final = "--write"
JUSTFILE_NAME: Final = "justfile"


class GuideRenderError(RuntimeError):
    """Base error for product-guide rendering failures."""


class UnresolvedGuideTemplateError(GuideRenderError):
    """Raised when a rendered runtime template still contains build macros."""


class GuideModule(Protocol):
    """Subset of the shipped update-spx generator reused by the product gate."""

    RUNTIME_GUIDE_FILENAMES: dict[str, str]

    def parse_template_version(self, text: str) -> str | None: ...

    def detect_languages_from_tree(self, spx_dir: Path) -> tuple[str, ...]: ...

    def render(
        self,
        template_text: str,
        languages: tuple[str, ...],
        installed_version: str,
        runtime: str,
    ) -> str: ...


def _run(args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )


def load_update_spx_module() -> GuideModule:
    """Load the shipped update-spx generator to reuse its pure render contract."""
    spec = importlib.util.spec_from_file_location("update_spx", _GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load update_spx from {_GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(GuideModule, module)


def guide_paths(module: GuideModule | None = None) -> tuple[str, ...]:
    """Derive the spx-relative guide paths from the generator's own enumeration."""
    guide_module = module or load_update_spx_module()
    return tuple(
        f"spx/{name}" for name in guide_module.RUNTIME_GUIDE_FILENAMES.values()
    )


def dist_template_path(runtime: str, *, repo_root: Path = REPO_ROOT) -> Path:
    """Return the rendered runtime template path for one guide runtime."""
    return repo_root / "dist" / runtime / DIST_TEMPLATE_RELATIVE_PATH


def load_runtime_templates(
    module: GuideModule | None = None, *, repo_root: Path = REPO_ROOT
) -> dict[str, str]:
    """Read rendered runtime templates from ``dist/`` for every guide runtime."""
    guide_module = module or load_update_spx_module()
    templates: dict[str, str] = {}
    for runtime in guide_module.RUNTIME_GUIDE_FILENAMES:
        path = dist_template_path(runtime, repo_root=repo_root)
        templates[runtime] = path.read_text(encoding="utf-8")
    return templates


def assert_no_unresolved_build_macros(text: str, *, path: Path | str) -> None:
    """Reject dist templates that still contain build-time macro delimiters."""
    for token in UNRESOLVED_BUILD_TEMPLATE_TOKENS:
        if token in text:
            raise UnresolvedGuideTemplateError(
                f"{path} contains unresolved build macro token {token!r}; "
                "run `just build-skills` before regenerating guides"
            )


def render_guides_from_runtime_templates(
    module: GuideModule,
    runtime_templates: Mapping[str, str],
    languages: tuple[str, ...],
    *,
    template_paths: Mapping[str, Path | str] | None = None,
) -> dict[str, str]:
    """Render every product guide from its runtime-specific dist template."""
    versions: dict[str, str] = {}
    for runtime, template_text in runtime_templates.items():
        path = (
            template_paths[runtime]
            if template_paths is not None and runtime in template_paths
            else runtime
        )
        assert_no_unresolved_build_macros(template_text, path=path)
        version = module.parse_template_version(template_text)
        if version is None:
            raise GuideRenderError(f"{path} has no template_version")
        versions[runtime] = version

    if len(set(versions.values())) != 1:
        details = ", ".join(
            f"{runtime}={version}" for runtime, version in sorted(versions.items())
        )
        raise GuideRenderError(
            f"runtime guide templates disagree on version: {details}"
        )

    return {
        module.RUNTIME_GUIDE_FILENAMES[runtime]: module.render(
            runtime_templates[runtime], languages, versions[runtime], runtime
        )
        for runtime in module.RUNTIME_GUIDE_FILENAMES
    }


def regenerate_guides() -> None:
    """Render both guide files in place from the committed runtime dist templates."""
    module = load_update_spx_module()
    spx_dir = REPO_ROOT / "spx"
    templates = load_runtime_templates(module)
    paths = {
        runtime: dist_template_path(runtime)
        for runtime in module.RUNTIME_GUIDE_FILENAMES
    }
    rendered = render_guides_from_runtime_templates(
        module,
        templates,
        module.detect_languages_from_tree(spx_dir),
        template_paths=paths,
    )
    for filename, content in rendered.items():
        (spx_dir / filename).write_text(content, encoding="utf-8")


def drifting_guides() -> list[str]:
    """Return the guide paths that drift from their committed content.

    ``--intent-to-add`` makes an absent-from-index guide register as drift; a plain
    ``git diff`` reports only tracked changes and would pass silently on a first run.
    """
    paths = guide_paths()
    _run(["git", "add", "--intent-to-add", *paths])
    result = _run(["git", "diff", "--name-only", "--", *paths])
    return [line for line in result.stdout.splitlines() if line.strip()]


def render_report(drift: Sequence[str]) -> str:
    """Render the actionable drift report from the drifting guide paths."""
    return "\n".join([HEADER, "", *(f"  {path}" for path in drift), "", REMEDIATION])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate spx guide files from rendered dist templates."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write guides without checking git drift.",
    )
    args = parser.parse_args(argv)
    try:
        regenerate_guides()
        if args.write:
            return 0
        drift = drifting_guides()
    except GuideRenderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        # Surface the failed command's own diagnostic; captured output is otherwise
        # swallowed by the default traceback, leaving the reporter unactionable.
        sys.stderr.write(exc.stderr or "")
        print(f"{HEADER}\n  the spx-guide gate failed; see the error above.")
        return 1
    if not drift:
        return 0
    print(render_report(drift))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
