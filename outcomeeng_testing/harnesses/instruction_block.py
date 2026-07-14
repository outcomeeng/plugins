"""Test harness for the instruction-block render module.

Exposes:

- Access to the shipped ``instruction_block.py`` module through the production
  distribution loader, which owns its importlib path and cache contract.
- ``build_template``. Constructs a synthetic instruction-block.md-shaped template for
  focused render scenarios. Canonical language-block mapping evidence reads the real
  template instead, so the governed domain follows every language the template defines.
- Root-instruction topology and root-content-pair fixture loaders. These read inert
  whole-payload fixtures and materialize temporary repositories for filesystem behavior.

The render and parse functions take document strings. Filesystem-facing scenarios use
fixture files and temporary directories owned and cleaned up by this harness.
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import re
import shlex
import subprocess
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final, cast

from hypothesis import given
from hypothesis import strategies as st
from hypothesis import settings

from outcomeeng.distribution import instruction_block as distribution
from outcomeeng_testing.generators import instruction_block as generators

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_TEMPLATE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "understand"
    / "templates"
    / "instruction-block.md"
)

SOURCE_MODULE: Final = cast(ModuleType, distribution.load_instruction_block_module())
INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS = tuple(
    SOURCE_MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES.values()
)
ROOT_TOPOLOGY_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "instruction_block"
)
ROOT_CONTENT_PAIR_FIXTURES_DIR: Final = (
    ROOT_TOPOLOGY_FIXTURES_DIR / "root-content-pairs"
)
ROOT_CONTENT_CORPUS_FIXTURE: Final = ROOT_CONTENT_PAIR_FIXTURES_DIR / "corpus.json"
RETIRED_SESSION_RESULT_FIXTURE: Final = (
    ROOT_TOPOLOGY_FIXTURES_DIR / "retired-session-result.md"
)
TOPOLOGY_ONLY_CLAUDE: Final = "only-claude.json"
TOPOLOGY_ONLY_AGENTS: Final = "only-agents.json"
TOPOLOGY_SEPARATE: Final = "separate.json"
TOPOLOGY_CLAUDE_SYMLINK: Final = "claude-symlink.json"
TOPOLOGY_AGENTS_SYMLINK: Final = "agents-symlink.json"
SYNTHETIC_TEMPLATE: Final = "synthetic-template.md"
SYNTHETIC_TEMPLATE_WITH_EXTRA_SECTION: Final = (
    "synthetic-template-with-extra-section.md"
)

SHARED_REGION_NAME: Final = cast(str, SOURCE_MODULE.BOOTSTRAP_SHARED_REGION_NAME)
PROPERTY_EXAMPLES: Final = 100
PROPERTY_SETTINGS: Final = settings(
    max_examples=PROPERTY_EXAMPLES,
    print_blob=True,
)

BUILD_MACRO_CAPABILITY = "ask_user"
BUILD_MACRO_HARNESS = "codex"


@dataclass(frozen=True)
class RootInstructionTopology:
    """Root instruction files and symlinks a consumer repository may already contain."""

    files: dict[str, str]
    symlinks: dict[str, str]


@dataclass(frozen=True)
class RootContentPair:
    """Two inert root-instruction payloads used to exercise span and wrap mapping."""

    name: str
    claude: str
    agents: str


@dataclass(frozen=True)
class RootContentCorpus:
    """Fixture-owned semantic roles for the bootstrap content-pair corpus."""

    shared: RootContentPair
    alternate_shared: RootContentPair
    near_identical: RootContentPair
    straddling: RootContentPair
    midline_boundary: RootContentPair


@dataclass(frozen=True)
class RootInstructionBodies:
    """Bodies observed at the two root instruction-file paths."""

    claude: str
    agents: str


@dataclass(frozen=True)
class InstructionFileState:
    """Observable filesystem state for one instruction-file path."""

    is_file: bool
    is_symlink: bool


@dataclass(frozen=True)
class RootInstructionFileStates:
    """Filesystem states observed at both root instruction-file paths."""

    claude: InstructionFileState
    agents: InstructionFileState


@dataclass(frozen=True)
class MaterializedRootInstructionState:
    """Observable state after a root instruction topology is materialized."""

    paths: RootInstructionFileStates
    files: RootInstructionBodies
    mapping: RootInstructionBodies


@dataclass(frozen=True)
class CliCheckMappingObservation:
    """Observed and expected CLI ``--check`` outcomes for a finite state mapping."""

    actual: tuple[tuple[int, str], ...]
    expected: tuple[tuple[int, str], ...]


REGULAR_INSTRUCTION_FILE_STATE: Final = InstructionFileState(
    is_file=True,
    is_symlink=False,
)


def _template_fixture_text(name: str) -> str:
    """Read one inert whole-template fixture."""
    return (ROOT_TOPOLOGY_FIXTURES_DIR / name).read_text(encoding="utf-8")


def _conditional_block_bodies(document: str, kind: str) -> dict[str, str]:
    """Extract complete conditional-block bodies from a template document."""
    blocks: dict[str, str] = {}
    active_name: str | None = None
    active_lines: list[str] = []
    for line in document.splitlines(keepends=True):
        stripped = line.strip()
        prefix = f"<!-- {kind}:"
        if stripped.startswith(prefix) and stripped.endswith(" -->"):
            if active_name is not None:
                raise RuntimeError(f"Nested {kind} block before closing {active_name}")
            active_name = stripped.removeprefix(prefix).removesuffix(" -->")
            active_lines = []
            continue
        if active_name is not None and stripped == f"<!-- /{kind}:{active_name} -->":
            blocks[active_name] = "".join(active_lines).strip()
            active_name = None
            active_lines = []
            continue
        if active_name is not None:
            active_lines.append(line)
    if active_name is not None:
        raise RuntimeError(f"Unclosed {kind} block: {active_name}")
    if not blocks:
        raise RuntimeError(f"Template fixture defines no {kind} blocks")
    return blocks


def _template_version(document: str) -> str:
    """Read the dotted version from a complete template fixture."""
    match = re.search(r'^template_version:\s*"(?P<version>[0-9.]+)"$', document, re.M)
    if match is None:
        raise RuntimeError("Template fixture has no dotted template version")
    return match.group("version")


def _previous_dotted_version(version: str) -> str:
    """Return an adjacent lower dotted version for stale-version scenarios."""
    parts = [int(part) for part in version.split(".")]
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] > 0:
            parts[index] -= 1
            return ".".join(str(part) for part in parts)
    raise RuntimeError("Template fixture version has no lower dotted version")


def _added_h2_heading(base: str, extended: str) -> str:
    """Return the one H2 heading introduced by the extended template fixture."""
    base_headings = {line for line in base.splitlines() if line.startswith("## ")}
    additions = [
        line.removeprefix("## ")
        for line in extended.splitlines()
        if line.startswith("## ") and line not in base_headings
    ]
    if len(additions) != 1:
        raise RuntimeError("Extended template fixture must introduce exactly one H2")
    return additions[0]


def _illustration_token(document: str) -> str:
    """Return the brace-delimited illustration carried by the template fixture."""
    match = re.search(r"`(?P<token>\{[^{}]+\})\.product\.md`", document)
    if match is None:
        raise RuntimeError("Template fixture has no product illustration token")
    return match.group("token")


_SYNTHETIC_TEMPLATE_TEXT: Final = _template_fixture_text(SYNTHETIC_TEMPLATE)
_EXTENDED_SYNTHETIC_TEMPLATE_TEXT: Final = _template_fixture_text(
    SYNTHETIC_TEMPLATE_WITH_EXTRA_SECTION
)
NEW_VERSION: Final = _template_version(_SYNTHETIC_TEMPLATE_TEXT)
OLD_VERSION: Final = _previous_dotted_version(NEW_VERSION)
TEMPLATE_LANGUAGES: Final = tuple(
    _conditional_block_bodies(_SYNTHETIC_TEMPLATE_TEXT, "lang")
)
if len(TEMPLATE_LANGUAGES) < 2:
    raise RuntimeError("Synthetic template fixture must define two language blocks")
LANG_PRIMARY: Final = TEMPLATE_LANGUAGES[0]
LANG_SECONDARY: Final = TEMPLATE_LANGUAGES[1]
TEMPLATE_HARNESSES: Final = tuple(
    _conditional_block_bodies(_SYNTHETIC_TEMPLATE_TEXT, "harness")
)
if len(TEMPLATE_HARNESSES) < 2:
    raise RuntimeError("Synthetic template fixture must define two harness blocks")
HARNESS_CLAUDE: Final = TEMPLATE_HARNESSES[0]
HARNESS_CODEX: Final = TEMPLATE_HARNESSES[1]
NEW_SECTION: Final = _added_h2_heading(
    _SYNTHETIC_TEMPLATE_TEXT,
    _EXTENDED_SYNTHETIC_TEMPLATE_TEXT,
)
ILLUSTRATION_TOKEN: Final = _illustration_token(_SYNTHETIC_TEMPLATE_TEXT)


def _load_root_instruction_topology(fixture_name: str) -> RootInstructionTopology:
    """Load one inert whole-topology fixture from disk."""
    payload = json.loads(
        (ROOT_TOPOLOGY_FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")
    )
    return RootInstructionTopology(
        files=cast(dict[str, str], payload["files"]),
        symlinks=cast(dict[str, str], payload["symlinks"]),
    )


def root_instruction_topology_only_claude() -> RootInstructionTopology:
    """Return a root topology with only the Claude harness instruction file present."""
    return _load_root_instruction_topology(TOPOLOGY_ONLY_CLAUDE)


def root_instruction_topology_only_agents() -> RootInstructionTopology:
    """Return a root topology with only the Codex harness instruction file present."""
    return _load_root_instruction_topology(TOPOLOGY_ONLY_AGENTS)


def root_instruction_topology_separate() -> RootInstructionTopology:
    """Return a root topology with two independent harness instruction files."""
    return _load_root_instruction_topology(TOPOLOGY_SEPARATE)


def root_instruction_topology_claude_symlink() -> RootInstructionTopology:
    """Return a root topology whose Claude instruction path is a symlink."""
    return _load_root_instruction_topology(TOPOLOGY_CLAUDE_SYMLINK)


def root_instruction_topology_agents_symlink() -> RootInstructionTopology:
    """Return a root topology whose Agents instruction path is a symlink."""
    return _load_root_instruction_topology(TOPOLOGY_AGENTS_SYMLINK)


def root_content_pairs() -> tuple[RootContentPair, ...]:
    """Load the complete inert root-content-pair fixture corpus."""
    return tuple(
        RootContentPair(
            name=case_dir.name,
            claude=(case_dir / INSTRUCTION_CLAUDE).read_text(encoding="utf-8"),
            agents=(case_dir / INSTRUCTION_AGENTS).read_text(encoding="utf-8"),
        )
        for case_dir in sorted(ROOT_CONTENT_PAIR_FIXTURES_DIR.iterdir())
        if case_dir.is_dir()
    )


def root_content_pair(name: str) -> RootContentPair:
    """Load one named root-content fixture pair."""
    return next(pair for pair in root_content_pairs() if pair.name == name)


def root_content_corpus() -> RootContentCorpus:
    """Load fixture-owned semantic roles for the bootstrap content corpus."""
    roles = cast(
        Mapping[str, str],
        json.loads(ROOT_CONTENT_CORPUS_FIXTURE.read_text(encoding="utf-8")),
    )
    pairs = {pair.name: pair for pair in root_content_pairs()}
    return RootContentCorpus(
        shared=pairs[roles["shared"]],
        alternate_shared=pairs[roles["alternate_shared"]],
        near_identical=pairs[roles["near_identical"]],
        straddling=pairs[roles["straddling"]],
        midline_boundary=pairs[roles["midline_boundary"]],
    )


def retired_session_result_lines() -> tuple[str, ...]:
    """Read the rule-owned violating lines retired from the instruction block."""
    return tuple(
        line
        for line in RETIRED_SESSION_RESULT_FIXTURE.read_text(
            encoding="utf-8"
        ).splitlines()
        if line and not line.startswith("#")
    )


ROOT_CONTENT_CORPUS: Final = root_content_corpus()
ROOT_CLAUDE_BODY: Final = root_instruction_topology_only_claude().files[
    INSTRUCTION_CLAUDE
]
ROOT_AGENTS_BODY: Final = root_instruction_topology_only_agents().files[
    INSTRUCTION_AGENTS
]
ROOT_SHARED_BODY: Final = root_instruction_topology_claude_symlink().files[
    INSTRUCTION_AGENTS
]
SHARED_REGION_BODY: Final = ROOT_CONTENT_CORPUS.shared.claude.strip("\n")
SHARED_REGION_BODY_ALT: Final = ROOT_CONTENT_CORPUS.alternate_shared.claude.strip("\n")
ROOT_NEAR_IDENTICAL_CLAUDE: Final = ROOT_CONTENT_CORPUS.near_identical.claude
ROOT_NEAR_IDENTICAL_CODEX: Final = ROOT_CONTENT_CORPUS.near_identical.agents
ROOT_STRADDLING_CLAUDE: Final = ROOT_CONTENT_CORPUS.straddling.claude
ROOT_STRADDLING_CODEX: Final = ROOT_CONTENT_CORPUS.straddling.agents
ROOT_MIDLINE_CLAUDE: Final = ROOT_CONTENT_CORPUS.midline_boundary.claude
ROOT_MIDLINE_CODEX: Final = ROOT_CONTENT_CORPUS.midline_boundary.agents


@contextmanager
def temporary_instruction_root() -> Iterator[pathlib.Path]:
    """Yield an isolated instruction-file root and remove it on exit."""
    with TemporaryDirectory() as directory:
        yield pathlib.Path(directory)


def _replace_path_with_text(path: pathlib.Path, body: str) -> None:
    """Write ``body`` as a regular file, replacing a symlink or file at ``path``."""
    if path.exists() or path.is_symlink():
        path.unlink()
    path.write_text(body, encoding="utf-8")


def _seed_body(
    root: pathlib.Path, instruction_name: str, fallback: str | None
) -> str | None:
    """Read an instruction file's body, following symlinks, or return ``fallback`` when absent."""
    path = root / instruction_name
    if path.exists() or path.is_symlink():
        return path.read_text(encoding="utf-8")
    return fallback


def materialize_root_instruction_topology(
    root: pathlib.Path, topology: RootInstructionTopology
) -> dict[str, str]:
    """Create ``topology`` under ``root`` and normalize harness instruction files."""
    root.mkdir(parents=True, exist_ok=True)
    for name, body in topology.files.items():
        _replace_path_with_text(root / name, body)
    for name, target in topology.symlinks.items():
        link_path = root / name
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        link_path.symlink_to(target)

    claude_seed = _seed_body(root, INSTRUCTION_CLAUDE, None)
    agents_seed = _seed_body(root, INSTRUCTION_AGENTS, claude_seed)
    if claude_seed is None:
        claude_seed = agents_seed
    if claude_seed is None or agents_seed is None:
        claude_seed = agents_seed = ""

    seeds = {INSTRUCTION_CLAUDE: claude_seed, INSTRUCTION_AGENTS: agents_seed}
    for name, body in seeds.items():
        _replace_path_with_text(root / name, body)
    return seeds


def _root_instruction_bodies(values: dict[str, str]) -> RootInstructionBodies:
    """Project an instruction-name mapping into an immutable observation record."""
    return RootInstructionBodies(
        claude=values[INSTRUCTION_CLAUDE],
        agents=values[INSTRUCTION_AGENTS],
    )


def _observe_root_instruction_mapping(
    topology: RootInstructionTopology,
) -> RootInstructionBodies:
    """Materialize one topology while the harness owns its temporary root."""
    with temporary_instruction_root() as root:
        actual = _root_instruction_bodies(
            materialize_root_instruction_topology(root, topology)
        )
    return actual


def observe_only_claude_topology_mapping() -> RootInstructionBodies:
    """Observe materialized bodies for the only-Claude topology."""
    topology = root_instruction_topology_only_claude()
    return _observe_root_instruction_mapping(topology)


def observe_only_agents_topology_mapping() -> RootInstructionBodies:
    """Observe materialized bodies for the only-Agents topology."""
    topology = root_instruction_topology_only_agents()
    return _observe_root_instruction_mapping(topology)


def observe_separate_topology_mapping() -> RootInstructionBodies:
    """Observe materialized bodies for separate instruction files."""
    topology = root_instruction_topology_separate()
    return _observe_root_instruction_mapping(topology)


def observe_claude_symlink_topology_mapping() -> RootInstructionBodies:
    """Observe materialized bodies for the Claude-symlink topology."""
    topology = root_instruction_topology_claude_symlink()
    return _observe_root_instruction_mapping(topology)


def observe_agents_symlink_topology_mapping() -> RootInstructionBodies:
    """Observe materialized bodies for the Agents-symlink topology."""
    topology = root_instruction_topology_agents_symlink()
    return _observe_root_instruction_mapping(topology)


def _observe_symlink_materialization(
    topology: RootInstructionTopology,
) -> MaterializedRootInstructionState:
    """Observe symlink normalization while owning all filesystem lifecycle state."""
    with temporary_instruction_root() as root:
        materialized = materialize_root_instruction_topology(root, topology)
        claude_path = root / INSTRUCTION_CLAUDE
        agents_path = root / INSTRUCTION_AGENTS
        actual = MaterializedRootInstructionState(
            paths=RootInstructionFileStates(
                claude=InstructionFileState(
                    is_file=claude_path.is_file(),
                    is_symlink=claude_path.is_symlink(),
                ),
                agents=InstructionFileState(
                    is_file=agents_path.is_file(),
                    is_symlink=agents_path.is_symlink(),
                ),
            ),
            files=RootInstructionBodies(
                claude=claude_path.read_text(encoding="utf-8"),
                agents=agents_path.read_text(encoding="utf-8"),
            ),
            mapping=_root_instruction_bodies(materialized),
        )
    return actual


def observe_claude_symlink_materialization() -> MaterializedRootInstructionState:
    """Observe normalization when the Claude instruction path is a symlink."""
    topology = root_instruction_topology_claude_symlink()
    return _observe_symlink_materialization(topology)


def observe_agents_symlink_materialization() -> MaterializedRootInstructionState:
    """Observe normalization when the Agents instruction path is a symlink."""
    topology = root_instruction_topology_agents_symlink()
    return _observe_symlink_materialization(topology)


def harness_line(harness: str) -> str:
    """Return the fixture-owned body of one synthetic harness block."""
    return _conditional_block_bodies(_SYNTHETIC_TEMPLATE_TEXT, "harness")[harness]


def render_build_macro() -> str:
    """Build an unresolved macro-shaped token owned by the render harness."""
    return f"\n{{{{! tool('{BUILD_MACRO_CAPABILITY}', '{BUILD_MACRO_HARNESS}') !}}}}\n"


def load_instruction_block_module() -> ModuleType:
    """Return the generator loaded through the production distribution contract."""
    return SOURCE_MODULE


def _version_string(parts: tuple[int, int, int]) -> str:
    """Render generated numeric version components as a dotted version."""
    return ".".join(str(part) for part in parts)


def _shared_document(module: ModuleType, name: str, body: str) -> str:
    """Wrap a generated body in one shared-region fence."""
    return (
        f"{module.shared_open_marker(name)}\n\n{body}\n\n"
        f"{module.shared_close_marker(name)}\n"
    )


def instruction_block_properties_hold() -> bool:
    """Exercise every generated invariant declared by instruction-block property evidence."""
    module = load_instruction_block_module()

    @PROPERTY_SETTINGS
    @given(
        agent_harness=st.sampled_from(TEMPLATE_HARNESSES),
        installed=generators.version_parts(),
    )
    def render_version_matches_installed(
        agent_harness: str,
        installed: tuple[int, int, int],
    ) -> None:
        installed_text = _version_string(installed)
        rendered = module.render(
            build_template(_version_string((0, 0, 0))),
            TEMPLATE_LANGUAGES,
            installed_text,
            agent_harness,
        )
        assert module.parse_template_version(rendered) == installed_text

    @PROPERTY_SETTINGS
    @given(installed=generators.version_parts())
    def managed_surfaces_end_with_one_newline(
        installed: tuple[int, int, int],
    ) -> None:
        installed_text = _version_string(installed)
        blocks = {
            agent_harness: module.render(
                build_template(_version_string((0, 0, 0))),
                TEMPLATE_LANGUAGES,
                installed_text,
                agent_harness,
            )
            for agent_harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
        }
        seeds = {
            agent_harness: ROOT_SHARED_BODY
            for agent_harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
        }
        documents = module.build_root_instruction_documents(seeds, blocks)
        for document in documents.values():
            assert document.endswith("\n")
            assert not document.endswith("\n\n")

    @PROPERTY_SETTINGS
    @given(
        left=generators.version_parts(),
        right=generators.version_parts(),
    )
    def staleness_matches_numeric_order(
        left: tuple[int, int, int],
        right: tuple[int, int, int],
    ) -> None:
        assert module.is_stale(_version_string(left), _version_string(right)) is (
            left < right
        )

    @PROPERTY_SETTINGS
    @given(
        body_a=generators.shared_region_bodies(),
        body_b=generators.shared_region_bodies(),
    )
    def reconcile_makes_regions_identical(body_a: str, body_b: str) -> None:
        document_a = _shared_document(module, SHARED_REGION_NAME, body_a)
        document_b = _shared_document(module, SHARED_REGION_NAME, body_b)
        for winner in ("a", "b"):
            new_a, new_b = module.reconcile_shared_regions(
                document_a,
                document_b,
                winner,
            )
            assert (
                module.parse_shared_regions(new_a)[SHARED_REGION_NAME]
                == module.parse_shared_regions(new_b)[SHARED_REGION_NAME]
            )

    @PROPERTY_SETTINGS
    @given(body=generators.shared_region_bodies())
    def identical_region_reconcile_is_idempotent(body: str) -> None:
        document_a = _shared_document(module, SHARED_REGION_NAME, body)
        document_b = _shared_document(module, SHARED_REGION_NAME, body)
        for winner in ("a", "b", None):
            assert module.reconcile_shared_regions(
                document_a,
                document_b,
                winner,
            ) == (document_a, document_b)

    @PROPERTY_SETTINGS
    @given(
        content_a=generators.free_instruction_content(),
        content_b=generators.free_instruction_content(),
    )
    def bootstrap_wraps_at_most_one_region(
        content_a: str,
        content_b: str,
    ) -> None:
        wrapped_a, wrapped_b = module.bootstrap_wrap(content_a, content_b)
        assert len(module.parse_shared_regions(wrapped_a)) <= 1
        assert len(module.parse_shared_regions(wrapped_b)) <= 1

    render_version_matches_installed()
    managed_surfaces_end_with_one_newline()
    staleness_matches_numeric_order()
    reconcile_makes_regions_identical()
    identical_region_reconcile_is_idempotent()
    bootstrap_wraps_at_most_one_region()
    return True


def read_canonical_template() -> str:
    """Read the canonical template both instruction files render from."""
    return CANONICAL_TEMPLATE_PATH.read_text(encoding="utf-8")


def canonical_read_entire_file_directive() -> str:
    """Return the canonical router paragraph that directs whole-file reading."""
    _, heading_and_body = read_canonical_template().split(
        "# Spec Tree Instructions\n", maxsplit=1
    )
    preamble, _ = heading_and_body.split("\n---\n", maxsplit=1)
    paragraphs = tuple(
        paragraph.strip() for paragraph in preamble.split("\n\n") if paragraph.strip()
    )
    if not paragraphs:
        raise RuntimeError("Canonical template has no router preamble")
    return paragraphs[-1]


def extract_markdown_section(document: str, heading: str) -> str:
    """Return a markdown section by exact heading line, including the heading."""
    lines = document.splitlines()
    try:
        start = lines.index(heading)
    except ValueError as exc:
        raise RuntimeError(f"Heading not found: {heading}") from exc
    heading_level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index, line in enumerate(lines[start + 1 :], start=start + 1):
        if line.startswith("#") and len(line) - len(line.lstrip("#")) <= heading_level:
            end = index
            break
    return "\n".join(lines[start:end])


def canonical_template_language_blocks() -> dict[str, tuple[str, ...]]:
    """Return every language block body defined by the canonical template."""
    blocks: dict[str, list[str]] = {}
    active_language: str | None = None
    active_lines: list[str] = []
    for line in read_canonical_template().splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("<!-- lang:") and stripped.endswith(" -->"):
            if active_language is not None:
                raise RuntimeError(
                    f"Nested language block before closing {active_language}"
                )
            active_language = stripped.removeprefix("<!-- lang:").removesuffix(" -->")
            active_lines = []
            continue
        if (
            active_language is not None
            and stripped == f"<!-- /lang:{active_language} -->"
        ):
            blocks.setdefault(active_language, []).append("".join(active_lines).strip())
            active_language = None
            active_lines = []
            continue
        if active_language is not None:
            active_lines.append(line)
    if active_language is not None:
        raise RuntimeError(f"Unclosed language block: {active_language}")
    if not blocks:
        raise RuntimeError("Canonical template defines no language blocks")
    return {language: tuple(bodies) for language, bodies in blocks.items()}


def build_template(version: str, *, extra_section: bool = False) -> str:
    """Return a whole-template fixture rewritten to the requested dotted version."""
    template = (
        _EXTENDED_SYNTHETIC_TEMPLATE_TEXT if extra_section else _SYNTHETIC_TEMPLATE_TEXT
    )
    current_version = _template_version(template)
    return template.replace(
        f'template_version: "{current_version}"',
        f'template_version: "{version}"',
        1,
    )


def write_spx_tree_with_tests(
    spx_dir: pathlib.Path, extensions: tuple[str, ...]
) -> pathlib.Path:
    """Create an ``spx/`` tree carrying one node whose ``tests/`` holds the given extensions.

    Lets language-detection tests drive the CLI edge against a real on-disk tree: the
    detector globs ``spx/**/tests/`` and maps each test-file extension to its language.
    """
    tests_dir = spx_dir / "21-node.enabler" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    for extension in extensions:
        (tests_dir / f"test_subject.scenario.l1.{extension}").write_text(
            "", encoding="utf-8"
        )
    return spx_dir


def write_template(
    directory: pathlib.Path, version: str, *, extra_section: bool = False
) -> pathlib.Path:
    """Write ``build_template(...)`` into ``directory`` and return the file path.

    Lets CLI-edge tests drive ``main([...])`` against a real template file under a
    pytest ``tmp_path``; the harness owns the on-disk setup.
    """
    path = directory / "instruction-block.md"
    path.write_text(
        build_template(version, extra_section=extra_section), encoding="utf-8"
    )
    return path


def run_generator_write(
    module: ModuleType,
    repo_root: pathlib.Path,
    template_path: pathlib.Path,
    *,
    languages: str,
) -> int:
    """Run the generator CLI's ``--write`` over ``repo_root`` and return its exit code.

    Centralizes the CLI-invocation setup the render-model tests share, since harness code —
    not test bodies — owns shared execution scaffolding. The dynamically loaded module types
    ``main`` as ``Any``; the CLI contract returns an exit code, so the result is cast to ``int``.
    """
    return cast(
        int,
        module.main(
            [
                "--template",
                str(template_path),
                "--repo-root",
                str(repo_root),
                "--languages",
                languages,
                "--write",
            ]
        ),
    )


def run_generator_write_primary(
    repo_root: pathlib.Path, template_path: pathlib.Path
) -> int:
    """Run the generator ``--write`` over ``repo_root`` with the harness's primary language.

    The render-model scenario tests share this exact run configuration — the loaded module and the
    single primary language — so it lives in the harness rather than a test-local wrapper.
    """
    return run_generator_write(
        load_instruction_block_module(),
        repo_root,
        template_path,
        languages=LANG_PRIMARY,
    )


def root_document_with_shared_region(
    module: ModuleType,
    harness: str,
    region_body: str,
    *,
    languages: tuple[str, ...],
    version: str,
    name: str = SHARED_REGION_NAME,
) -> str:
    """Return a root document: the harness router block first, then one shared region.

    Mirrors a real post-bootstrap file — the router block on top of a single named shared
    region — so a file this helper produces has the three-content-kind shape a ``--reconcile``
    operates on. This root instruction-file setup policy lives in the harness, not a test body.
    """
    template = build_template(version)
    block = module.render(template, languages, version, harness)
    fenced = (
        f"{module.shared_open_marker(name)}\n\n{region_body}\n\n"
        f"{module.shared_close_marker(name)}"
    )
    return cast(str, module.prepend_router_block(block, fenced))


def write_both_root_files_with_shared_region(
    module: ModuleType,
    repo_root: pathlib.Path,
    *,
    languages: tuple[str, ...],
    version: str,
    claude_region: str = SHARED_REGION_BODY,
    agents_region: str = SHARED_REGION_BODY,
    name: str = SHARED_REGION_NAME,
) -> None:
    """Write root CLAUDE.md and AGENTS.md, each a router block over one named shared region.

    The two region bodies are equal by default; passing different ``claude_region`` and
    ``agents_region`` seeds a diverged shared region for a recency-reconcile test.
    """
    bodies = {
        module.AGENT_HARNESS_INSTRUCTION_FILENAMES["claude"]: (claude_region, "claude"),
        module.AGENT_HARNESS_INSTRUCTION_FILENAMES["codex"]: (agents_region, "codex"),
    }
    for filename, (region_body, harness) in bodies.items():
        (repo_root / filename).write_text(
            root_document_with_shared_region(
                module,
                harness,
                region_body,
                languages=languages,
                version=version,
                name=name,
            ),
            encoding="utf-8",
        )


def assert_extension_to_language_mapping() -> None:
    """Assert every source-owned test extension maps with or without a leading dot."""
    module = load_instruction_block_module()
    for extension, language in sorted(module.LANGUAGE_BY_EXTENSION.items()):
        assert module.language_for_extension(extension) == language
        assert module.language_for_extension(f".{extension}") == language


def assert_detected_language_set_mapping() -> None:
    """Assert tree extension detection yields the source-owned language set."""
    module = load_instruction_block_module()
    with TemporaryDirectory() as directory:
        spx_dir = pathlib.Path(directory) / module.OBSOLETE_SPX_DIR_NAME
        tests_dir = spx_dir / "10-node.enabler" / "tests"
        tests_dir.mkdir(parents=True)
        for extension in module.LANGUAGE_BY_EXTENSION:
            (tests_dir / f"test_subject.mapping.l1.{extension}").touch()

        assert module.detect_languages_from_tree(spx_dir) == module.normalize_languages(
            module.LANGUAGE_BY_EXTENSION.values()
        )


def assert_language_block_filter_mapping() -> None:
    """Assert every canonical template language block appears exactly when enabled."""
    module = load_instruction_block_module()
    template = read_canonical_template()
    blocks = canonical_template_language_blocks()
    for language, bodies in blocks.items():
        enabled = module.render(template, (language,), NEW_VERSION, HARNESS_CLAUDE)
        disabled = module.render(
            template,
            tuple(name for name in blocks if name != language),
            NEW_VERSION,
            HARNESS_CLAUDE,
        )
        for body in bodies:
            assert body in enabled
            assert body not in disabled


def _run_generator_check(
    module: ModuleType,
    repo_root: pathlib.Path,
    template_path: pathlib.Path,
    *,
    languages: str,
) -> tuple[int, str]:
    """Run the generator CLI's ``--check`` branch and capture its status report."""
    stdout = io.StringIO()
    with redirect_stdout(stdout):
        code = module.main(
            [
                "--template",
                str(template_path),
                "--repo-root",
                str(repo_root),
                "--languages",
                languages,
                "--check",
            ]
        )
    return cast(int, code), stdout.getvalue().strip()


def observe_router_check_mapping() -> CliCheckMappingObservation:
    """Observe the CLI report for current, stale, and absent router states."""
    module = load_instruction_block_module()
    with TemporaryDirectory() as directory:
        root = pathlib.Path(directory)
        repo = root / "repo"
        repo.mkdir()
        template = write_template(root, NEW_VERSION)
        run_generator_write_primary(repo, template)
        claude = repo / INSTRUCTION_CLAUDE

        current = _run_generator_check(module, repo, template, languages=LANG_PRIMARY)
        stale_language = _run_generator_check(
            module, repo, template, languages=LANG_SECONDARY
        )

        claude.unlink()
        absent = _run_generator_check(module, repo, template, languages=LANG_PRIMARY)

        stale_block = module.render(
            build_template(OLD_VERSION),
            (LANG_PRIMARY,),
            OLD_VERSION,
            HARNESS_CLAUDE,
        )
        claude.write_text(
            module.prepend_router_block(stale_block, ""), encoding="utf-8"
        )
        stale_version = _run_generator_check(
            module, repo, template, languages=LANG_PRIMARY
        )

        return CliCheckMappingObservation(
            actual=(current, stale_language, absent, stale_version),
            expected=(
                (0, module.InstructionStatus.CURRENT.value),
                (0, module.InstructionStatus.STALE.value),
                (0, module.InstructionStatus.ABSENT.value),
                (0, module.InstructionStatus.STALE.value),
            ),
        )


def observe_shared_region_check_mapping() -> CliCheckMappingObservation:
    """Observe the CLI report for identical, diverged, and one-sided shared regions."""
    module = load_instruction_block_module()
    with TemporaryDirectory() as directory:
        root = pathlib.Path(directory).resolve()
        repo = root / "repo"
        repo.mkdir()
        template = write_template(root, NEW_VERSION)

        write_both_root_files_with_shared_region(
            module, repo, languages=(LANG_PRIMARY,), version=NEW_VERSION
        )
        current = _run_generator_check(module, repo, template, languages=LANG_PRIMARY)

        write_both_root_files_with_shared_region(
            module,
            repo,
            languages=(LANG_PRIMARY,),
            version=NEW_VERSION,
            claude_region=SHARED_REGION_BODY,
            agents_region=SHARED_REGION_BODY_ALT,
        )
        stale_diverged = _run_generator_check(
            module, repo, template, languages=LANG_PRIMARY
        )

        codex_block = module.render(
            build_template(NEW_VERSION),
            (LANG_PRIMARY,),
            NEW_VERSION,
            HARNESS_CODEX,
        )
        (repo / INSTRUCTION_AGENTS).write_text(
            module.prepend_router_block(codex_block, ROOT_AGENTS_BODY),
            encoding="utf-8",
        )
        stale_one_sided = _run_generator_check(
            module, repo, template, languages=LANG_PRIMARY
        )

        return CliCheckMappingObservation(
            actual=(current, stale_diverged, stale_one_sided),
            expected=(
                (0, module.InstructionStatus.CURRENT.value),
                (0, module.InstructionStatus.STALE.value),
                (0, module.InstructionStatus.STALE.value),
            ),
        )


def assert_bootstrap_topology_mapping() -> None:
    """Assert every source-owned initial topology maps to its bootstrap outcome."""
    module = load_instruction_block_module()
    template_source = build_template(NEW_VERSION)
    blocks = {
        harness: module.render(template_source, (LANG_PRIMARY,), NEW_VERSION, harness)
        for harness in TEMPLATE_HARNESSES
    }
    for topology in (
        root_instruction_topology_only_claude(),
        root_instruction_topology_only_agents(),
        root_instruction_topology_separate(),
        root_instruction_topology_claude_symlink(),
        root_instruction_topology_agents_symlink(),
    ):
        with TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            repo = root / "repo"
            seeds = materialize_root_instruction_topology(repo, topology)
            template_path = write_template(root, NEW_VERSION)
            run_generator_write_primary(repo, template_path)

            claude_path = repo / INSTRUCTION_CLAUDE
            agents_path = repo / INSTRUCTION_AGENTS
            claude = claude_path.read_text(encoding="utf-8")
            agents = agents_path.read_text(encoding="utf-8")
            seeds_identical = seeds[INSTRUCTION_CLAUDE] == seeds[INSTRUCTION_AGENTS]

            assert bool(module.parse_shared_regions(claude)) == seeds_identical
            if seeds_identical:
                assert set(module.parse_shared_regions(claude)) == set(
                    module.parse_shared_regions(agents)
                )
            assert claude.startswith(module.ROUTER_MARKER_PREFIX)
            assert agents.startswith(module.ROUTER_MARKER_PREFIX)
            assert claude_path.is_file() and not claude_path.is_symlink()
            assert agents_path.is_file() and not agents_path.is_symlink()

    identical_documents = module.build_root_instruction_documents(
        {HARNESS_CLAUDE: ROOT_SHARED_BODY, HARNESS_CODEX: ROOT_SHARED_BODY},
        blocks,
    )
    for document in identical_documents.values():
        assert module.parse_shared_regions(document) == {
            module.BOOTSTRAP_SHARED_REGION_NAME: ROOT_SHARED_BODY.strip("\n")
        }

    retired_open, retired_close = module.LEGACY_MANAGED_BLOCK_MARKERS[0]
    retired_block = (
        f"{retired_open}\n"
        f"{module.MANAGED_TEMPLATE_VERSION_PREFIX} {OLD_VERSION} -->\n"
        f"{retired_close}"
    )
    retired_seed = f"{retired_block}\n\n{ROOT_SHARED_BODY}"
    retired_documents = module.build_root_instruction_documents(
        {HARNESS_CLAUDE: retired_seed, HARNESS_CODEX: retired_seed},
        blocks,
    )
    for document in retired_documents.values():
        assert retired_open not in document
        assert retired_close not in document
        assert module.parse_shared_regions(document) == {
            module.BOOTSTRAP_SHARED_REGION_NAME: ROOT_SHARED_BODY.strip("\n")
        }

    above_threshold_documents = module.build_root_instruction_documents(
        {
            HARNESS_CLAUDE: ROOT_NEAR_IDENTICAL_CLAUDE,
            HARNESS_CODEX: ROOT_NEAR_IDENTICAL_CODEX,
        },
        blocks,
    )
    expected_shared_body = _biggest_identical_whole_line_span(
        ROOT_NEAR_IDENTICAL_CLAUDE,
        ROOT_NEAR_IDENTICAL_CODEX,
    ).strip("\n")
    for document in above_threshold_documents.values():
        assert module.parse_shared_regions(document) == {
            module.BOOTSTRAP_SHARED_REGION_NAME: expected_shared_body
        }
    assert "CLAUDE specific tail" in above_threshold_documents[HARNESS_CLAUDE]
    assert "CODEX specific tail" in above_threshold_documents[HARNESS_CODEX]

    below_threshold_documents = module.build_root_instruction_documents(
        {HARNESS_CLAUDE: ROOT_CLAUDE_BODY, HARNESS_CODEX: ROOT_AGENTS_BODY},
        blocks,
    )
    for document in below_threshold_documents.values():
        assert module.parse_shared_regions(document) == {}


def assert_span_ratio_wrap_mapping() -> None:
    """Assert fixture-corpus spans and ratios map to wrapping decisions."""
    module = load_instruction_block_module()
    wrap_decisions: set[bool] = set()
    for pair in root_content_pairs():
        expected_span = _biggest_identical_whole_line_span(pair.claude, pair.agents)
        span, ratio = module.biggest_identical_span(pair.claude, pair.agents)
        expected_ratio = len(expected_span) / max(len(pair.claude), len(pair.agents))
        should_wrap = bool(expected_span.strip()) and (
            expected_ratio > module.BOOTSTRAP_SHARED_THRESHOLD
        )
        wrapped_claude, wrapped_agents = module.bootstrap_wrap(pair.claude, pair.agents)
        claude_regions = module.parse_shared_regions(wrapped_claude)
        agents_regions = module.parse_shared_regions(wrapped_agents)

        assert span == expected_span, pair.name
        assert ratio == expected_ratio, pair.name
        assert bool(claude_regions) is should_wrap, pair.name
        assert bool(agents_regions) is should_wrap, pair.name
        if should_wrap:
            assert claude_regions == agents_regions
            assert next(iter(claude_regions.values())) == expected_span.strip("\n")
        else:
            assert wrapped_claude == pair.claude
            assert wrapped_agents == pair.agents
        wrap_decisions.add(should_wrap)

    assert wrap_decisions == {False, True}


def _biggest_identical_whole_line_span(text_a: str, text_b: str) -> str:
    """Return the longest common contiguous whole-line span by exhaustive comparison."""
    lines_a = text_a.splitlines(keepends=True)
    lines_b = text_b.splitlines(keepends=True)
    best = ""
    for start_a in range(len(lines_a)):
        for start_b in range(len(lines_b)):
            offset = 0
            while (
                start_a + offset < len(lines_a)
                and start_b + offset < len(lines_b)
                and lines_a[start_a + offset] == lines_b[start_b + offset]
            ):
                offset += 1
                candidate = "".join(lines_a[start_a : start_a + offset])
                if len(candidate) > len(best):
                    best = candidate
    return best


def git_command(
    repo_root: pathlib.Path, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run a git command in ``repo_root`` for tests that need real git state.

    Centralizes the git subprocess setup the drift-gate tests share, since harness code —
    not test bodies — owns shared execution scaffolding.
    """
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, check=True, text=True
    )


def init_git_identity(repo_root: pathlib.Path) -> None:
    """Initialize a git repository with a committed-safe identity for drift-gate tests.

    ``commit.gpgsign`` is forced off in local config so a committer whose global config enables GPG
    signing — the norm this repository's git-safety protocol protects — does not fail the throwaway
    ``Test User`` commits these tests make; the local setting overrides the ambient global one.
    """
    git_command(repo_root, "init")
    git_command(repo_root, "config", "user.name", "Test User")
    git_command(repo_root, "config", "user.email", "test@example.com")
    git_command(repo_root, "config", "commit.gpgsign", "false")


def git_commit_at(
    repo_root: pathlib.Path,
    timestamp: int,
    *paths: str,
    message: str = "commit",
) -> None:
    """Stage ``paths`` and commit them at a fixed epoch ``timestamp``.

    A recency-reconcile test needs two commits whose committer dates differ deterministically;
    fixing ``GIT_AUTHOR_DATE`` and ``GIT_COMMITTER_DATE`` to an explicit epoch makes the newer
    side unambiguous without depending on wall-clock time. Committing setup is harness-owned.
    """
    for path in paths:
        git_command(repo_root, "add", path)
    date = f"@{timestamp} +0000"
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = date
    env["GIT_COMMITTER_DATE"] = date
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_root,
        capture_output=True,
        check=True,
        text=True,
        env=env,
    )


def workflow_run_block(step_name: str) -> str:
    """Return the run-command block of one refresh-workflow step, dedented for assertions.

    Reads ``.github/workflows/refresh-instruction-blocks.yml`` and extracts the ``run: |`` block
    of the named step. Workflow parsing is shared setup, so it lives in the harness rather than a
    test body.
    """
    workflow = REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")
    lines = workflow.splitlines()
    step_line = f"      - name: {step_name}"
    start = lines.index(step_line)
    run_line = lines.index("        run: |", start)
    block: list[str] = []
    for line in lines[run_line + 1 :]:
        if line.startswith("      - name: "):
            break
        if line.startswith("          "):
            block.append(line[10:])
        elif line:
            break
        else:
            block.append("")
    return "\n".join(block) + "\n"


def workflow_step_block(step_name: str) -> str:
    """Return the full YAML block of one refresh-workflow step, for step assertions."""
    workflow = REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")
    lines = workflow.splitlines()
    step_line = f"      - name: {step_name}"
    start = lines.index(step_line)
    block: list[str] = []
    for line in lines[start:]:
        if line.startswith("      - name: ") and block:
            break
        block.append(line)
    return "\n".join(block) + "\n"


def workflow_shell_lines(step_name: str) -> tuple[str, ...]:
    """Return executable shell lines from one workflow run block in source order."""
    return tuple(
        line.strip()
        for line in workflow_run_block(step_name).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def workflow_if_block(step_name: str, condition: str) -> tuple[str, ...]:
    """Return the complete shell ``if`` block for an exact workflow condition."""
    lines = workflow_shell_lines(step_name)
    opener = f"if {condition}; then"
    start = lines.index(opener)
    depth = 0
    for index, line in enumerate(lines[start:], start=start):
        if line.startswith("if ") and line.endswith("; then"):
            depth += 1
        elif line == "fi":
            depth -= 1
            if depth == 0:
                return lines[start : index + 1]
    raise AssertionError(f"workflow if block is unclosed: {condition}")


def workflow_env_value(name: str) -> str:
    """Return the value of one refresh-workflow ``env`` entry, for env assertions."""
    workflow = REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")
    prefix = f"      {name}: "
    for line in workflow.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).split(" #", maxsplit=1)[0].strip('"')
    raise AssertionError(f"workflow env value not found: {name}")


def justfile_recipe_body(justfile: str, recipe: str) -> str:
    """Return the indented body of one justfile recipe, for recipe-binding assertions.

    A recipe header is ``<recipe>:`` at column 0; its body is the following indented lines up to
    the next unindented line. Scoping an invocation to the recipe body, rather than to the whole
    file, is what makes a recipe-body swap falsifiable.
    """
    lines = justfile.splitlines()
    start = lines.index(f"{recipe}:")
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line[0].isspace():
            break
        body.append(line)
    return "\n".join(body)


def justfile_recipe_argv(justfile: str, recipe: str) -> tuple[tuple[str, ...], ...]:
    """Parse executable commands from one exact Justfile recipe body."""
    commands = tuple(
        line.strip()
        for line in justfile_recipe_body(justfile, recipe).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    return tuple(tuple(shlex.split(command)) for command in commands)


def write_gh_stub(bin_dir: pathlib.Path, log_path: pathlib.Path) -> None:
    """Write a fake ``gh`` CLI into ``bin_dir`` that logs its args and accepts pr list/create."""
    stub = bin_dir / "gh"
    stub.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f'printf "%s\\n" "$*" >> {str(log_path)!r}',
                'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "list" ]; then',
                "  exit 0",
                "fi",
                'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "create" ]; then',
                "  exit 0",
                "fi",
                'echo "unexpected gh invocation: $*" >&2',
                "exit 64",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)


def run_refresh_pr_step(repo_root: pathlib.Path, gh_log: pathlib.Path) -> str:
    """Run the refresh workflow's PR-opening step against ``repo_root`` with a stubbed ``gh``.

    Executes the extracted step's bash block with a fake ``gh`` on PATH so the drift-driven
    commit-and-open behavior runs for real without a network call. Subprocess execution setup is
    the harness's responsibility, not a test body's.
    """
    bin_dir = repo_root.parent / f"{repo_root.name}-stub-bin"
    bin_dir.mkdir()
    write_gh_stub(bin_dir, gh_log)
    env = os.environ.copy()
    env["GH_TOKEN"] = "test-token"
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            workflow_run_block("Open instruction-block refresh pull request"),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout
