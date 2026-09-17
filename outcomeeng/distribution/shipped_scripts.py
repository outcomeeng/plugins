"""Loading a shipped script as a module.

A script the plugin ships under ``dist/`` is loaded through its file boundary
so a test or gate reaches its pure seams directly. The load writes no bytecode
cache beside the script, so the generated tree stays free of one.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_shipped_module(name: str, path: Path) -> ModuleType:
    """Load the shipped script at ``path`` as module ``name``, cached in ``sys.modules``."""
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass type introspection can resolve the module by name.
    sys.modules[name] = module
    dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    except Exception:
        # A module that failed to execute never stays cached as if it loaded.
        del sys.modules[name]
        raise
    finally:
        sys.dont_write_bytecode = dont_write_bytecode
    return module
