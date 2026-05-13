"""Test-directory bridge that exposes ``_helpers`` to sibling test modules.

The repo runs pytest with ``--import-mode=importlib`` (see
``pyproject.toml``). importlib mode does not prepend a test file's
directory to ``sys.path``, so a sibling module like ``_helpers.py``
cannot be imported by name from ``test_*.py`` without help.

This conftest is the help: it runs once per test session (pytest
auto-discovers conftest.py per directory) and prepends this directory
to ``sys.path`` before any sibling test module is collected. Sibling
tests can then do ``from _helpers import ...`` to share the constants
and ``run_script`` helper defined there.

The shared scaffolding itself lives in ``_helpers.py`` because the
top-level ``conftest.py`` at the repo root claims the ``conftest``
module name — a second ``conftest`` module in this directory cannot be
imported by name from a sibling test file (the root conftest wins on
``from conftest import ...``).
"""

from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
