"""Generated import-statement domain for the static import index.

Each case is built from the names it imports, so its expected dependency set
follows from that construction rather than from the resolver under test.
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Final

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.validation.infrastructure_index import (
    TEST_INFRASTRUCTURE_PACKAGE,
)

SUBPACKAGE_NAME: Final = "harnesses"
SUBMODULE_NAME: Final = "gate"
SIBLING_MODULE_NAME: Final = "spawner"
ATTRIBUTE_NAME: Final = "run_gate"


@dataclass(frozen=True)
class ImportStatementCase:
    """One import statement form with its construction-derived dependencies."""

    form: str
    source: str
    importing_package: str | None
    modules: frozenset[str]
    expected: frozenset[str]


def import_statement_cases(
    package: str = TEST_INFRASTRUCTURE_PACKAGE,
) -> tuple[ImportStatementCase, ...]:
    """Every import statement form an indexed file can carry.

    The module set names one subpackage with two submodules. Expected
    dependencies are the imported module and every package on its dotted
    path, plus the submodule when a ``from`` import names one.
    """

    subpackage = f"{package}.{SUBPACKAGE_NAME}"
    submodule = f"{subpackage}.{SUBMODULE_NAME}"
    sibling = f"{subpackage}.{SIBLING_MODULE_NAME}"
    modules = frozenset({package, subpackage, submodule, sibling})
    path_to_subpackage = frozenset({package, subpackage})
    return (
        ImportStatementCase(
            form="import a.b",
            source=f"import {subpackage}\n",
            importing_package=None,
            modules=modules,
            expected=path_to_subpackage,
        ),
        ImportStatementCase(
            form="from a.b import c naming a submodule",
            source=f"from {subpackage} import {SUBMODULE_NAME}\n",
            importing_package=None,
            modules=modules,
            expected=path_to_subpackage | {submodule},
        ),
        ImportStatementCase(
            form="from a.b import c naming an attribute",
            source=f"from {subpackage} import {ATTRIBUTE_NAME}\n",
            importing_package=None,
            modules=modules,
            expected=path_to_subpackage,
        ),
        ImportStatementCase(
            form="from . import c",
            source=f"from . import {SIBLING_MODULE_NAME}\n",
            importing_package=subpackage,
            modules=modules,
            expected=path_to_subpackage | {sibling},
        ),
        ImportStatementCase(
            form="from .c import d",
            source=f"from .{SIBLING_MODULE_NAME} import {ATTRIBUTE_NAME}\n",
            importing_package=subpackage,
            modules=modules,
            expected=path_to_subpackage | {sibling},
        ),
    )


CHAIN_MODULE_PREFIX: Final = "chain_"
MAX_CHAIN_LENGTH: Final = 6


def import_chains() -> SearchStrategy[tuple[str, ...]]:
    """Distinct module names forming one import chain, first to last.

    Each generated name is prefixed so it is a valid identifier that collides
    with no keyword; the chain length varies from one module upward.
    """

    return st.lists(
        st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=6),
        min_size=1,
        max_size=MAX_CHAIN_LENGTH,
        unique=True,
    ).map(lambda names: tuple(f"{CHAIN_MODULE_PREFIX}{name}" for name in names))
