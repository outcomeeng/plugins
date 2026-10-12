"""Observations of where Python sources hold model price entries."""

import ast
import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import ModelPrice
from outcomeeng_testing.harnesses.dist_tree import DistTreeReader

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[2]
PRICE_DATA_FILE: Final = Path(
    "coding-agents/skills/control-token-spend/scripts/model-prices.json"
)
SOURCE_ROOTS: Final = (
    "outcomeeng",
    "outcomeeng_evals",
    "outcomeeng_testing",
    "src",
)


@dataclass(frozen=True)
class PriceSite:
    """One place a source names a priced identifier or builds a price."""

    path: Path
    line: int
    identifier: str | None


def shipped_price_document(target: Target) -> object:
    """Read the price data file the build renders beside the shipped skill scripts."""
    path = DistTreeReader(REPOSITORY_ROOT).target_root(target) / PRICE_DATA_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def production_python_sources() -> Iterator[Path]:
    """Yield every Python source file under the repository's source roots."""
    for root in SOURCE_ROOTS:
        yield from sorted((REPOSITORY_ROOT / root).rglob("*.py"))


def observe_price_sites(
    paths: Iterable[Path], identifiers: frozenset[str]
) -> list[PriceSite]:
    """Report each priced-identifier string and each price construction in the sources."""
    sites: list[PriceSite] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        constructors = _price_constructors(
            tree, _module_name(path), path.name == "__init__.py"
        )
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in identifiers
            ):
                sites.append(PriceSite(path, node.lineno, node.value))
            elif isinstance(node, ast.Call) and _dotted_name(node.func) in constructors:
                sites.append(PriceSite(path, node.lineno, None))
    return sites


def _module_name(path: Path) -> str | None:
    """Return the dotted module name of a source under the repository, else None."""
    try:
        relative = path.resolve().relative_to(REPOSITORY_ROOT)
    except ValueError:
        return None
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _import_origin(
    node: ast.ImportFrom, module: str | None, path_is_package: bool
) -> str | None:
    """Return the absolute dotted module an import-from statement names."""
    if node.level == 0:
        return node.module
    if module is None:
        return None
    package = module.split(".")
    if not path_is_package:
        package = package[:-1]
    package = package[: len(package) - (node.level - 1)]
    if node.module:
        package = [*package, node.module]
    return ".".join(package)


def _dotted_name(expression: ast.expr) -> str | None:
    """Return a Name or Attribute chain as dotted text, else None."""
    if isinstance(expression, ast.Name):
        return expression.id
    if isinstance(expression, ast.Attribute):
        base = _dotted_name(expression.value)
        return None if base is None else f"{base}.{expression.attr}"
    return None


def _price_constructors(
    tree: ast.Module, module: str | None, is_package: bool
) -> set[str]:
    """Return every dotted spelling that the module binds to the price class.

    A binding is resolved through the module's imports, the price class's
    definition, and plain aliases of an already bound spelling, so the
    spelled name never decides identity.
    """
    owner_module = ModelPrice.__module__
    owner_name = ModelPrice.__name__
    bound: set[str] = set()
    modules: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ClassDef)
            and node.name == owner_name
            and module == owner_module
        ):
            bound.add(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == owner_module:
                    modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            origin = _import_origin(node, module, is_package)
            for alias in node.names:
                local = alias.asname or alias.name
                if origin == owner_module and alias.name == owner_name:
                    bound.add(local)
                elif origin is not None and f"{origin}.{alias.name}" == owner_module:
                    modules.add(local)
    bound |= {f"{name}.{owner_name}" for name in modules}
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and _dotted_name(node.value) in bound:
                for target in node.targets:
                    name = _dotted_name(target)
                    if name is not None and name not in bound:
                        bound.add(name)
                        changed = True
    return bound
