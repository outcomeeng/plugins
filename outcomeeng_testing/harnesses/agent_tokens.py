"""Observations of the agent-token owner, the toolchain's agent-token declarations, and a build's rendered agent tokens."""

from __future__ import annotations

import ast
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.build import (
    AGENT_CAPABILITY_REGISTRY,
    CONFIGURED_AGENT_PROMPT_FIELD_NAMES,
    CONFIGURED_AGENT_TERM_NAMES,
    build,
)
from outcomeeng.distribution.contracts import (
    AGENT_TOKEN_DATA_FILENAME,
    AGENT_TOKEN_ENUM_NAME,
    AGENT_TOKEN_OWNER_PATH,
    AGENT_TOKEN_READING_PLUGIN_NAME,
    DIST_DIR_NAME,
    REPOSITORY_ROOT,
    SCRIPTS_SUBDIR_NAME,
    SKILLS_SUBDIR_NAME,
)
from outcomeeng.distribution.orchestration import CATALOG_PATHS
from outcomeeng_testing.harnesses.src_tree import src_tree

# The packages whose modules make up the product's toolchain.
TOOLCHAIN_PACKAGE_NAMES: Final = (
    "outcomeeng",
    "outcomeeng_testing",
    "outcomeeng_evals",
)
# A name ending in one of these suffixes holds the spelling of an executable.
EXECUTABLE_NAME_SUFFIXES: Final = ("_BIN", "_BINARY", "_EXECUTABLE")

TOKEN_READING_SKILL: Final = "token-reader"
TOKEN_READING_SCRIPT: Final = (
    Path(SKILLS_SUBDIR_NAME) / TOKEN_READING_SKILL / SCRIPTS_SUBDIR_NAME / "reader.py"
)
TOKEN_SECOND_READING_SKILL: Final = "token-second-reader"
TOKEN_SECOND_READING_SCRIPT: Final = (
    Path(SKILLS_SUBDIR_NAME)
    / TOKEN_SECOND_READING_SKILL
    / SCRIPTS_SUBDIR_NAME
    / "second_reader.py"
)
TOKEN_READING_SCRIPTS: Final = (TOKEN_READING_SCRIPT, TOKEN_SECOND_READING_SCRIPT)
TOKEN_NON_READING_SKILL: Final = "token-bystander"
TOKEN_NON_READING_SCRIPT: Final = (
    Path(SKILLS_SUBDIR_NAME)
    / TOKEN_NON_READING_SKILL
    / SCRIPTS_SUBDIR_NAME
    / "unrelated.py"
)
OTHER_PLUGIN_NAME: Final = "other-plugin"
OTHER_PLUGIN_READING_SCRIPT: Final = TOKEN_READING_SCRIPT


@dataclass(frozen=True)
class TokenLiteral:
    """One string constant of a toolchain module that spells an agent token."""

    module: Path
    line: int
    value: str


@dataclass(frozen=True)
class RenderedTokenFile:
    """One agent-token data file a build emitted, located within its generated tree."""

    target_directory: str
    path: Path
    document: Mapping[str, object]


@dataclass(frozen=True)
class AgentTokenBuild:
    """What one build of a sample source tree emitted."""

    tree_directories: frozenset[str]
    token_files: tuple[RenderedTokenFile, ...]


@dataclass(frozen=True)
class AgentKeyedTable:
    """One per-agent table of the build and the keys it carries."""

    name: str
    keys: tuple[object, ...]


def owner_source_tokens() -> Mapping[str, str]:
    """Return each member name and token the owner module's source declares.

    The owner's source is parsed, not imported, so the observation does not
    share the build's loader.
    """
    owner_source = (REPOSITORY_ROOT / AGENT_TOKEN_OWNER_PATH).read_text(
        encoding="utf-8"
    )
    for node in ast.parse(owner_source).body:
        if isinstance(node, ast.ClassDef) and node.name == AGENT_TOKEN_ENUM_NAME:
            return {
                statement.targets[0].id: statement.value.value
                for statement in node.body
                if isinstance(statement, ast.Assign)
                and isinstance(statement.targets[0], ast.Name)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            }
    raise LookupError(
        f"{AGENT_TOKEN_ENUM_NAME} is absent from {AGENT_TOKEN_OWNER_PATH}"
    )


def toolchain_module_paths() -> tuple[Path, ...]:
    """Return every Python module of the toolchain packages, relative to the repository root."""
    return tuple(
        module.relative_to(REPOSITORY_ROOT)
        for package in TOOLCHAIN_PACKAGE_NAMES
        for module in sorted((REPOSITORY_ROOT / package).rglob("*.py"))
    )


def _docstring_constants(tree: ast.AST) -> frozenset[int]:
    """Return the identity of every docstring constant in a parsed module."""
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    return frozenset(docstrings)


def _command_spellings(tree: ast.AST, tokens: frozenset[str]) -> frozenset[int]:
    """Return the identity of every constant that spells an executable.

    An executable is spelled as the first element of a command vector or as
    the value of a name that holds an executable. A sequence of agent tokens
    is a roster of agents and spells no executable.
    """
    spellings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Tuple | ast.List) and node.elts:
            if not any(
                isinstance(element, ast.Constant) and element.value in tokens
                for element in node.elts[1:]
            ):
                spellings.add(id(node.elts[0]))
        elif isinstance(node, ast.Assign | ast.AnnAssign) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                isinstance(target, ast.Name)
                and target.id.endswith(EXECUTABLE_NAME_SUFFIXES)
                for target in targets
            ):
                spellings.add(id(node.value))
    return frozenset(spellings)


def toolchain_module_token_literals() -> tuple[TokenLiteral, ...]:
    """Observe every string constant in the toolchain's modules equal to an owner token.

    Docstrings and the spelling of an executable in a command vector are not
    declarations of a token.
    """
    tokens = frozenset(owner_source_tokens().values())
    literals: list[TokenLiteral] = []
    for module in toolchain_module_paths():
        tree = ast.parse((REPOSITORY_ROOT / module).read_text(encoding="utf-8"))
        exempt = _docstring_constants(tree) | _command_spellings(tree, tokens)
        literals.extend(
            TokenLiteral(module, node.lineno, node.value)
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in tokens
            and id(node) not in exempt
        )
    return tuple(literals)


def build_sample_agent_token_tree() -> AgentTokenBuild:
    """Build a sample source tree into a temporary directory and observe the emitted tree.

    The sample source carries two spec-tree scripts that name the data file,
    each in a skill directory of its own, a spec-tree script that does not in
    a scripts directory of its own, and a script of another plugin that names
    it.
    """
    reading_source = f'DATA_FILE = "{AGENT_TOKEN_DATA_FILENAME}"\n'.encode()
    with src_tree() as builder:
        builder.add_plugin(
            AGENT_TOKEN_READING_PLUGIN_NAME,
            skills={
                TOKEN_READING_SKILL: "body\n",
                TOKEN_SECOND_READING_SKILL: "body\n",
                TOKEN_NON_READING_SKILL: "body\n",
            },
            artifacts={
                TOKEN_READING_SCRIPT: reading_source,
                TOKEN_SECOND_READING_SCRIPT: reading_source,
                TOKEN_NON_READING_SCRIPT: b"VALUE = 1\n",
            },
        )
        builder.add_plugin(
            OTHER_PLUGIN_NAME,
            skills={TOKEN_READING_SKILL: "body\n"},
            artifacts={OTHER_PLUGIN_READING_SCRIPT: reading_source},
        )
        dist_root = builder.root / DIST_DIR_NAME
        build(builder.src_root, dist_root)
        tree_directories = frozenset(
            entry.name for entry in dist_root.iterdir() if entry.is_dir()
        )
        token_files = tuple(
            RenderedTokenFile(
                target_directory=data_file.relative_to(dist_root).parts[0],
                path=Path(*data_file.relative_to(dist_root).parts[1:]),
                document=json.loads(data_file.read_text(encoding="utf-8")),
            )
            for data_file in sorted(dist_root.rglob(AGENT_TOKEN_DATA_FILENAME))
        )
    return AgentTokenBuild(tree_directories, token_files)


def build_agent_keyed_tables() -> tuple[AgentKeyedTable, ...]:
    """Observe the keys of every per-agent table the build carries."""
    tables = [
        AgentKeyedTable("AGENT_CAPABILITY_REGISTRY", tuple(AGENT_CAPABILITY_REGISTRY)),
        AgentKeyedTable(
            "CONFIGURED_AGENT_PROMPT_FIELD_NAMES",
            tuple(CONFIGURED_AGENT_PROMPT_FIELD_NAMES),
        ),
        AgentKeyedTable("CATALOG_PATHS", tuple(CATALOG_PATHS)),
    ]
    tables.extend(
        AgentKeyedTable(f"CONFIGURED_AGENT_TERM_NAMES[{capability}]", tuple(names))
        for capability, names in CONFIGURED_AGENT_TERM_NAMES.items()
    )
    return tuple(tables)


def stage_agent_tokens_file(
    scripts_dir: Path, *, tokens: str | None, make_directory: bool = False
) -> None:
    """Place the agent-tokens data file beside a copied script in the given state.

    ``tokens`` is the file's text, or ``None`` for an absent file; ``make_directory`` places a
    directory at the file's path so reading it fails as an unreadable file.
    """
    tokens_path = scripts_dir / AGENT_TOKEN_DATA_FILENAME
    if make_directory:
        tokens_path.mkdir()
    elif tokens is not None:
        tokens_path.write_text(tokens, encoding="utf-8")
