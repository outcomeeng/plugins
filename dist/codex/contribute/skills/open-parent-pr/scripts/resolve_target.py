"""Entrypoint reaching the shared contribution target resolver.

This skill's own command surface for target resolution. The resolver itself is
owned by the `contribution-standards` skill, and this file loads it by a path
resolved relative to `__file__` rather than naming that skill in a permission
grant: a grant that walks out of `${SKILL_DIR}` encodes the provider's
directory name and script layout where nothing can follow it, so moving the
provider breaks the grant silently, while a moved module raises here at load.

Grant locality is governed by `spx/13-plugin-and-runtime-conventions.adr.md`.

Portability: stdlib only — no third-party packages, no `uv`, no project imports.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

_RESOLVER_MODULE = "contribution_target_resolver"
_RESOLVER_RELPATH = ("contribution-standards", "scripts", "resolve_target.py")


def load_resolver() -> ModuleType:
    """Load the provider skill's resolver module via the co-location convention.

    The module sits beside this plugin's other skills, so the skills directory is
    two parents above this script. Cached in `sys.modules` under a name distinct
    from this entrypoint's own so one process can hold both.
    """
    cached = sys.modules.get(_RESOLVER_MODULE)
    if cached is not None:
        return cached
    skills_dir = pathlib.Path(__file__).resolve().parent.parent.parent
    path = skills_dir.joinpath(*_RESOLVER_RELPATH)
    spec = importlib.util.spec_from_file_location(_RESOLVER_MODULE, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load the contribution target resolver from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_RESOLVER_MODULE] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    return int(load_resolver().main())


if __name__ == "__main__":
    sys.exit(main())
