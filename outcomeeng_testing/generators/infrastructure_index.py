"""Generated import-statement domain for the static import index.

Each case is built from the names it imports, so its expected dependency set
follows from that construction rather than from the resolver under test.
"""

from __future__ import annotations

import string
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.spec_tree_structure import (
    MIN_NODE_INDEX,
    NodeKind,
    format_node_directory_name,
)
from outcomeeng.validation.infrastructure_index import (
    EXECUTED_TEST_PREFIX,
    PYTHON_SUFFIX,
    SPEC_TREE_ROOT,
    TEST_INFRASTRUCTURE_PACKAGE,
    TESTS_DIRECTORY_NAME,
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


CHAIN_NODE: Final = (
    f"{SPEC_TREE_ROOT}/"
    f"{format_node_directory_name(MIN_NODE_INDEX, 'chain', NodeKind.ENABLER)}"
)
CHAIN_TEST_NAME: Final = "chain"


@dataclass(frozen=True)
class ChainSources:
    """Source text of an import chain and of one executed test importing its first module.

    ``chain`` lists the chain's module names first to last; every module in it
    imports the next. ``module_sources`` also holds the package and subpackage
    modules the chain lives in, as an indexed package carries them.
    """

    package: str
    chain: tuple[str, ...]
    module_sources: Mapping[str, str]
    test: str
    test_sources: Mapping[str, str]


def chain_sources(
    names: tuple[str, ...], package: str = TEST_INFRASTRUCTURE_PACKAGE
) -> ChainSources:
    """Build the chain's sources from ``names``; each module imports the next."""

    subpackage = f"{package}.{SUBPACKAGE_NAME}"
    chain = tuple(f"{subpackage}.{name}" for name in names)
    module_sources = {package: "", subpackage: ""}
    for position, module in enumerate(chain):
        following = names[position + 1 : position + 2]
        module_sources[module] = "".join(
            f"from {subpackage} import {name}\n" for name in following
        )
    test = (
        f"{CHAIN_NODE}/{TESTS_DIRECTORY_NAME}/"
        f"{EXECUTED_TEST_PREFIX}{CHAIN_TEST_NAME}{PYTHON_SUFFIX}"
    )
    return ChainSources(
        package=package,
        chain=chain,
        module_sources=module_sources,
        test=test,
        test_sources={test: f"from {subpackage} import {names[0]}\n"},
    )


def import_chain_sources() -> SearchStrategy[ChainSources]:
    """Generated import chains, as the source text the index reads."""

    return import_chains().map(chain_sources)
