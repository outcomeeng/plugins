"""Run the `contribution-standards` resolver from this skill's own directory.

Reached by a path relative to this file, so a moved provider raises here instead
of a grant into a sibling's directory that would degrade to a permission prompt.
Stdlib only.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

RESOLVER_MODULE = "contribution_target_resolver"
RESOLVER = (
    Path(__file__)
    .resolve()
    .parents[2]
    .joinpath("contribution-standards", "scripts", "resolve_target.py")
)


def load_resolver() -> ModuleType:
    """Import the provider's resolver once, registered under its own name."""
    if RESOLVER_MODULE not in sys.modules:
        spec = importlib.util.spec_from_file_location(RESOLVER_MODULE, RESOLVER)
        if not RESOLVER.is_file() or spec is None or spec.loader is None:
            raise RuntimeError(
                f"No contribution target resolver at {RESOLVER}. The "
                "contribution-standards skill is missing or moved; reinstall "
                "the contribute plugin."
            )
        module = importlib.util.module_from_spec(spec)
        sys.modules[RESOLVER_MODULE] = module
        spec.loader.exec_module(module)
    return sys.modules[RESOLVER_MODULE]


if __name__ == "__main__":
    sys.exit(int(load_resolver().main()))
