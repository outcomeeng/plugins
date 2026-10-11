"""Observations of where Python sources hold model price entries."""

import ast
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.profiles import ModelPrice

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[2]
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
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value in identifiers:
                sites.append(PriceSite(path, node.lineno, node.value))
            elif (
                isinstance(node, ast.Call) and _callee_name(node) == ModelPrice.__name__
            ):
                sites.append(PriceSite(path, node.lineno, None))
    return sites


def _callee_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None
