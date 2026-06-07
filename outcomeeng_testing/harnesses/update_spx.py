"""Test harness for the update-spx render module.

Exposes:

- An importlib loader for ``update_spx.py``. The module ships under a
  runtime-substituted plugin skill directory and is not importable by package
  name; tests load it through ``importlib`` instead.
- ``build_template``. Constructs a synthetic spx-claude.md-shaped template with a
  brace-delimited illustration token, a language-conditional block per language in
  ``TEMPLATE_LANGUAGES``, and (optionally) a section that exists only in a newer
  template — for exercising new-section propagation on update. The lang-block
  marker syntax mirrors the module's ``_LANG_BLOCK`` contract; a test that drifts
  from it fails to render, which is the intended coupling.

The render and parse functions take document strings, so the harness builds
documents as strings; no filesystem is involved.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
# Coupled to the update-spx skill directory name; a rename there must update this
# path or load_update_spx_module raises RuntimeError at import time.
UPDATE_SPX_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "update-spx"
    / "scripts"
    / "update_spx.py"
)

# Invented scenario payload owned by the harness.
LANG_PRIMARY = "python"
LANG_SECONDARY = "typescript"
TEMPLATE_LANGUAGES = (LANG_PRIMARY, LANG_SECONDARY)
BASE_SECTION = "Test Naming"
NEW_SECTION = "Process Hygiene"
# A brace-delimited illustration token the render must pass through unchanged.
ILLUSTRATION_TOKEN = "{product-slug}"


def load_update_spx_module() -> ModuleType:
    """Load the ``update_spx`` module via importlib and cache it."""
    cached = sys.modules.get("update_spx")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("update_spx", UPDATE_SPX_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load update_spx from {UPDATE_SPX_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["update_spx"] = module
    spec.loader.exec_module(module)
    return module


def _language_heading(language: str) -> str:
    """The H3 heading the harness emits inside a language block — what render keeps or drops."""
    return f"### {language.capitalize()}"


def build_template(version: str, *, extra_section: bool = False) -> str:
    """Build a synthetic template at ``version`` with a block per template language.

    With ``extra_section`` the template also carries ``NEW_SECTION`` — a section a
    newer template introduces, absent from an older one.
    """
    module = load_update_spx_module()
    delimiter = module.FRONTMATTER_DELIMITER
    frontmatter = (
        f"{delimiter}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{version}"\n'
        f"{module.TEMPLATE_SOURCE_KEY}: {module.DEFAULT_TEMPLATE_SOURCE}\n"
        f"{delimiter}\n"
    )
    parts = [
        "",
        "# spx/ Directory Guide",
        "",
        f"The root spec is `{ILLUSTRATION_TOKEN}.product.md`.",
        "",
        f"## {BASE_SECTION}",
        "",
    ]
    for language in TEMPLATE_LANGUAGES:
        parts += [
            f"<!-- lang:{language} -->",
            "",
            _language_heading(language),
            f"{language} naming rules",
            "",
            f"<!-- /lang:{language} -->",
        ]
    if extra_section:
        parts += ["", f"## {NEW_SECTION}", "", "new methodology guidance"]
    return frontmatter + "\n".join(parts) + "\n"


def write_template(
    directory: pathlib.Path, version: str, *, extra_section: bool = False
) -> pathlib.Path:
    """Write ``build_template(...)`` into ``directory`` and return the file path.

    Lets CLI-edge tests drive ``main([...])`` against a real template file under a
    pytest ``tmp_path``; the harness owns the on-disk setup.
    """
    path = directory / "spx-claude.md"
    path.write_text(
        build_template(version, extra_section=extra_section), encoding="utf-8"
    )
    return path
