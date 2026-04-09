"""Sync spx/EXCLUDE → pyproject.toml tool exclusions.

Reads ``spx/EXCLUDE`` for nodes in specified state (specs and tests exist,
implementation doesn't) and updates ``pyproject.toml`` to exclude their tests
from the quality gate:

- **pytest**: ``--ignore`` flags in ``[tool.pytest.ini_options] addopts``
- **mypy**: regex patterns in ``[tool.mypy] exclude``
- **pyright**: directory paths in ``[tool.pyright] exclude``
- **ruff**: NOT excluded (style is checked regardless of implementation)

Uses ``tomlkit`` for safe TOML round-tripping (preserves comments, formatting,
and whitespace).

Usage::

    uv run python -m outcomeeng.scripts.sync_exclude
    # or: just sync-exclude
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import tomlkit

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXCLUDE = REPO_ROOT / "spx" / "EXCLUDE"
DEFAULT_PYPROJECT = REPO_ROOT / "pyproject.toml"


def read_excluded_nodes(path: Path) -> list[str]:
    """Read node paths from spx/EXCLUDE, stripping comments and blanks."""
    nodes: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            nodes.append(line)
    return nodes


def to_pytest_ignore(node: str) -> str:
    """Convert a node path to a pytest --ignore flag."""
    return f"--ignore=spx/{node}/"


def to_mypy_regex(node: str) -> str:
    """Convert a node path to a mypy exclude regex.

    Example: ``57-subsystems.outcome/32-risc-v.outcome``
    → ``^spx/57\\-subsystems\\.outcome/32\\-risc\\-v\\.outcome/``
    """
    escaped = re.escape(f"spx/{node}/")
    return f"^{escaped}"


def to_pyright_path(node: str) -> str:
    """Convert a node path to a pyright exclude path."""
    return f"spx/{node}/"


def _update_pytest_addopts(doc: tomlkit.TOMLDocument, nodes: list[str]) -> None:
    """Update [tool.pytest.ini_options] addopts with --ignore flags."""
    pytest_opts = doc["tool"]["pytest"]["ini_options"]  # type: ignore[index]
    current_addopts: str = pytest_opts["addopts"]  # type: ignore[assignment,index]

    # Remove existing excluded --ignore flags
    parts = current_addopts.split()
    kept = [p for p in parts if not is_excluded_entry(p)]

    # Add new excluded --ignore flags
    for node in nodes:
        kept.append(to_pytest_ignore(node))

    pytest_opts["addopts"] = " ".join(kept)  # type: ignore[index]


def is_excluded_entry(val: str) -> bool:
    """Check if a TOML array value was generated from an excluded node."""
    s = str(val)
    # Match patterns like "spx/57-subsystems.outcome/" or "^spx/57\-subsystems\.outcome/"
    return (".outcome/" in s or ".enabler/" in s) and "spx/" in s


def _update_list_section(
    exclude_list: tomlkit.items.Array,
    new_entries: list[str],
) -> None:
    """Replace excluded node entries in a TOML array with new entries."""
    # Remove old excluded entries
    indices_to_remove = [
        i for i, item in enumerate(exclude_list) if is_excluded_entry(item)
    ]
    for i in reversed(indices_to_remove):
        del exclude_list[i]

    # Append new entries
    for entry in new_entries:
        exclude_list.append(entry)


def _ensure_tool_exclude_list(
    doc: tomlkit.TOMLDocument, tool_name: str
) -> tomlkit.items.Array:
    """Return ``[tool.{tool_name}] exclude`` array, creating the section if missing."""
    tool_table = doc.setdefault("tool", tomlkit.table())
    section = tool_table.setdefault(tool_name, tomlkit.table())  # type: ignore[union-attr]
    if "exclude" not in section:  # type: ignore[operator]
        section["exclude"] = tomlkit.array()  # type: ignore[index]
    return section["exclude"]  # type: ignore[index,return-value]


def sync(pyproject_path: Path, excluded_nodes: list[str]) -> bool:
    """Sync excluded nodes into pyproject.toml. Returns True if changes were made."""
    original = pyproject_path.read_text()
    doc = tomlkit.parse(original)

    # 1. pytest addopts
    _update_pytest_addopts(doc, excluded_nodes)

    # 2. mypy exclude
    mypy_exclude = _ensure_tool_exclude_list(doc, "mypy")
    mypy_entries = [to_mypy_regex(n) for n in excluded_nodes]
    _update_list_section(mypy_exclude, mypy_entries)

    # 3. pyright exclude
    pyright_exclude = _ensure_tool_exclude_list(doc, "pyright")
    pyright_entries = [to_pyright_path(n) for n in excluded_nodes]
    _update_list_section(pyright_exclude, pyright_entries)

    updated = tomlkit.dumps(doc)
    if updated == original:
        return False

    pyproject_path.write_text(updated)
    return True


def main(
    exclude_path: Path | None = None,
    pyproject_path: Path | None = None,
) -> int:
    """Sync spx/EXCLUDE to pyproject.toml."""
    exclude_file = exclude_path or DEFAULT_EXCLUDE
    pyproject_file = pyproject_path or DEFAULT_PYPROJECT

    if not exclude_file.exists():
        print(f"error: {exclude_file} not found", file=sys.stderr)
        return 1

    if not pyproject_file.exists():
        print(f"error: {pyproject_file} not found", file=sys.stderr)
        return 1

    nodes = read_excluded_nodes(exclude_file)
    if not nodes:
        print("spx/EXCLUDE is empty — no excluded nodes to sync.")
        return 0

    changed = sync(pyproject_file, nodes)
    if changed:
        print(f"Updated pyproject.toml from spx/EXCLUDE ({len(nodes)} nodes).")
    else:
        print("pyproject.toml is already in sync with spx/EXCLUDE.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
