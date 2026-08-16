"""Run the review-journal inspection provider from this skill's entrypoint."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType
from typing import Sequence

_PROVIDER_SCRIPTS = (
    pathlib.Path(__file__).resolve().parents[2]
    / "verification-run-journal-standards"
    / "scripts"
)


def _load_module(name: str, path: pathlib.Path) -> ModuleType:
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: Sequence[str] | None = None) -> int:
    _load_module("journal_projection", _PROVIDER_SCRIPTS / "journal_projection.py")
    provider = _load_module(
        "render_review_run",
        _PROVIDER_SCRIPTS / "render_review_run.py",
    )
    return int(provider.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
