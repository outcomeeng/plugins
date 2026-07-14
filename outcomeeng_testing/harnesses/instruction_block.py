"""Test harness for the instruction-block render module.

Exposes:

- An importlib loader for ``instruction_block.py``. The module ships under a
  generated plugin skill directory and is not importable by package
  name; tests load it through ``importlib`` instead.
- ``build_template``. Constructs a synthetic instruction-block.md-shaped template for
  focused render scenarios. Canonical language-block mapping evidence reads the real
  template instead, so the governed domain follows every language the template defines.
- Root-instruction topology and root-content-pair fixture loaders. These read inert
  whole-payload fixtures and materialize temporary repositories for filesystem behavior.

The render and parse functions take document strings. Filesystem-facing scenarios use
fixture files and temporary directories owned and cleaned up by this harness.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import sys
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final, cast

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parents[2]
# Coupled to the update-instruction-block skill directory name; a rename there must update
# this path or load_instruction_block_module raises RuntimeError at import time.
INSTRUCTION_BLOCK_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "update-instruction-block"
    / "scripts"
    / "instruction_block.py"
)
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

INSTRUCTION_CLAUDE: Final = "CLAUDE.md"
INSTRUCTION_AGENTS: Final = "AGENTS.md"
ROOT_TOPOLOGY_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "instruction_block"
)
ROOT_CONTENT_PAIR_FIXTURES_DIR: Final = (
    ROOT_TOPOLOGY_FIXTURES_DIR / "root-content-pairs"
)
TOPOLOGY_ONLY_CLAUDE: Final = "only-claude.json"
TOPOLOGY_ONLY_AGENTS: Final = "only-agents.json"
TOPOLOGY_SEPARATE: Final = "separate.json"
TOPOLOGY_CLAUDE_SYMLINK: Final = "claude-symlink.json"
TOPOLOGY_AGENTS_SYMLINK: Final = "agents-symlink.json"

SHARED_REGION_NAME: Final = "root"
ROOT_CONTENT_CASE_ABOVE_THRESHOLD: Final = "above-threshold"
ROOT_CONTENT_CASE_BELOW_THRESHOLD: Final = "below-threshold"
ROOT_CONTENT_CASE_IDENTICAL: Final = "identical"
ROOT_CONTENT_CASE_MIDLINE_BOUNDARY: Final = "midline-boundary"
ROOT_CONTENT_CASE_STRADDLING: Final = "straddling"

# The retired session-result tokens the shipped instruction block must never teach. No
# production module owns a removed token, so the regression guard declares the forbidden
# strings here and asserts they are absent from the real rendered output.
SESSION_MANAGEMENT_HEADING = "## Session Management"
SESSION_ARCHIVE_RESULT_INSTRUCTION = "Before archiving a claimed session"
SESSION_RESULT_FRONTMATTER_FIELD = "`result`"

# The required read-the-whole-file directive the router must carry so a reading agent reaches the
# product's own commands below the router. Declared here as the required-content vocabulary the
# compliance guard asserts is present in the rendered router.
READ_ENTIRE_FILE_INSTRUCTION = "Read this entire file"

# Invented scenario payload owned by the harness.
LANG_PRIMARY = "python"
LANG_SECONDARY = "typescript"
TEMPLATE_LANGUAGES = (LANG_PRIMARY, LANG_SECONDARY)
BASE_SECTION = "Test Naming"
NEW_SECTION = "Process Hygiene"
# Invented scenario version payload owned by the harness: NEW_VERSION is the installed (current)
# template version, OLD_VERSION a version numerically below it. The values carry no domain
# meaning; the dotted-numeric ordering NEW_VERSION > OLD_VERSION is what the staleness and
# upgrade scenarios rely on.
OLD_VERSION: Final = "0.17.0"
NEW_VERSION: Final = "0.18.0"
# A brace-delimited illustration token the render must pass through unchanged.
ILLUSTRATION_TOKEN = "{product-slug}"
BUILD_MACRO_CAPABILITY = "ask_user"
BUILD_MACRO_HARNESS = "codex"

# Harness payload: the template carries a per-harness block for each agent harness,
# rendered only into that harness's instruction file. The marker syntax mirrors the module's
# ``<!-- harness:NAME -->`` conditional-block contract (parsed by ``_filter_harness``); a
# synthetic template that drifts from it fails to render.
HARNESS_CLAUDE = "claude"
HARNESS_CODEX = "codex"
TEMPLATE_HARNESSES = (HARNESS_CLAUDE, HARNESS_CODEX)


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


ROOT_CLAUDE_BODY: Final = root_instruction_topology_only_claude().files[
    INSTRUCTION_CLAUDE
]
ROOT_AGENTS_BODY: Final = root_instruction_topology_only_agents().files[
    INSTRUCTION_AGENTS
]
ROOT_SHARED_BODY: Final = root_instruction_topology_claude_symlink().files[
    INSTRUCTION_AGENTS
]
SHARED_REGION_BODY: Final = root_content_pair(ROOT_CONTENT_CASE_IDENTICAL).claude.strip(
    "\n"
)
SHARED_REGION_BODY_ALT: Final = root_content_pair(
    ROOT_CONTENT_CASE_BELOW_THRESHOLD
).claude.strip("\n")
ROOT_NEAR_IDENTICAL_CLAUDE: Final = root_content_pair(
    ROOT_CONTENT_CASE_ABOVE_THRESHOLD
).claude
ROOT_NEAR_IDENTICAL_CODEX: Final = root_content_pair(
    ROOT_CONTENT_CASE_ABOVE_THRESHOLD
).agents
ROOT_STRADDLING_CLAUDE: Final = root_content_pair(ROOT_CONTENT_CASE_STRADDLING).claude
ROOT_STRADDLING_CODEX: Final = root_content_pair(ROOT_CONTENT_CASE_STRADDLING).agents
ROOT_MIDLINE_CLAUDE: Final = root_content_pair(
    ROOT_CONTENT_CASE_MIDLINE_BOUNDARY
).claude
ROOT_MIDLINE_CODEX: Final = root_content_pair(ROOT_CONTENT_CASE_MIDLINE_BOUNDARY).agents


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


def harness_line(harness: str) -> str:
    """The body the harness emits inside a harness block — what render keeps or drops."""
    return f"{harness.upper()} runs the audit as a subagent."


def render_build_macro() -> str:
    """Build an unresolved macro-shaped token owned by the render harness."""
    return f"\n{{{{! tool('{BUILD_MACRO_CAPABILITY}', '{BUILD_MACRO_HARNESS}') !}}}}\n"


def load_instruction_block_module() -> ModuleType:
    """Load the ``instruction_block`` module via importlib and cache it."""
    cached = sys.modules.get("instruction_block")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "instruction_block", INSTRUCTION_BLOCK_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load instruction_block from {INSTRUCTION_BLOCK_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["instruction_block"] = module
    spec.loader.exec_module(module)
    return module


def read_canonical_template() -> str:
    """Read the canonical template both instruction files render from."""
    return CANONICAL_TEMPLATE_PATH.read_text(encoding="utf-8")


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


def _language_heading(language: str) -> str:
    """The H3 heading the harness emits inside a language block — what render keeps or drops."""
    return f"### {language.capitalize()}"


def build_template(version: str, *, extra_section: bool = False) -> str:
    """Build a synthetic template at ``version`` with a block per template language.

    With ``extra_section`` the template also carries ``NEW_SECTION`` — a section a
    newer template introduces, absent from an older one.
    """
    module = load_instruction_block_module()
    delimiter = module.FRONTMATTER_DELIMITER
    frontmatter = (
        f"{delimiter}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{version}"\n'
        f"{module.TEMPLATE_SOURCE_KEY}: {module.DEFAULT_TEMPLATE_SOURCE}\n"
        f"{delimiter}\n"
    )
    parts = [
        "",
        "# Spec Tree Instructions",
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
    for harness in TEMPLATE_HARNESSES:
        parts += [
            f"<!-- harness:{harness} -->",
            "",
            harness_line(harness),
            "",
            f"<!-- /harness:{harness} -->",
        ]
    if extra_section:
        parts += ["", f"## {NEW_SECTION}", "", "new methodology guidance"]
    return frontmatter + "\n".join(parts) + "\n"


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


def assert_router_status_mapping() -> None:
    """Assert current, absent, and behind-version router states map to reports."""
    module = load_instruction_block_module()
    with TemporaryDirectory() as directory:
        root = pathlib.Path(directory)
        repo = root / "repo"
        repo.mkdir()
        template = write_template(root, NEW_VERSION)
        run_generator_write_primary(repo, template)
        claude = repo / INSTRUCTION_CLAUDE

        assert (
            module.instruction_status(claude, NEW_VERSION, (LANG_PRIMARY,), repo)
            is module.InstructionStatus.CURRENT
        )
        assert (
            module.instruction_status(claude, NEW_VERSION, (LANG_SECONDARY,), repo)
            is module.InstructionStatus.STALE
        )

        claude.unlink()
        assert (
            module.instruction_status(claude, NEW_VERSION, (LANG_PRIMARY,), repo)
            is module.InstructionStatus.ABSENT
        )

        stale_block = module.render(
            build_template(OLD_VERSION),
            (LANG_PRIMARY,),
            OLD_VERSION,
            HARNESS_CLAUDE,
        )
        claude.write_text(
            module.prepend_router_block(stale_block, ""), encoding="utf-8"
        )
        assert (
            module.instruction_status(claude, NEW_VERSION, (LANG_PRIMARY,), repo)
            is module.InstructionStatus.STALE
        )


def assert_shared_region_status_mapping() -> None:
    """Assert identical, diverged, and one-sided shared regions map to drift reports."""
    module = load_instruction_block_module()
    with TemporaryDirectory() as directory:
        repo = pathlib.Path(directory).resolve() / "repo"
        repo.mkdir()

        write_both_root_files_with_shared_region(
            module, repo, languages=(LANG_PRIMARY,), version=NEW_VERSION
        )
        assert module.shared_region_drift(repo) == ()

        write_both_root_files_with_shared_region(
            module,
            repo,
            languages=(LANG_PRIMARY,),
            version=NEW_VERSION,
            claude_region=SHARED_REGION_BODY,
            agents_region=SHARED_REGION_BODY_ALT,
        )
        assert SHARED_REGION_NAME in module.shared_region_drift(repo)

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
        assert SHARED_REGION_NAME in module.shared_region_drift(repo)


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
