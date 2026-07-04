"""Test harness for the instruction-block render module.

Exposes:

- An importlib loader for ``instruction_block.py``. The module ships under a
  generated plugin skill directory and is not importable by package
  name; tests load it through ``importlib`` instead.
- ``build_template``. Constructs a synthetic instruction-block.md-shaped template with a
  brace-delimited illustration token, a language-conditional block per language in
  ``TEMPLATE_LANGUAGES``, and (optionally) a section that exists only in a newer
  template — for exercising new-section propagation on update. The lang-block
  marker syntax mirrors the module's ``<!-- lang:NAME -->`` conditional-block contract
  (parsed by ``_filter_languages``); a synthetic template that drifts from it fails to
  render, which is the intended input-fixture coupling.

The render and parse functions take document strings, so the harness builds
documents as strings; no filesystem is involved.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
from dataclasses import dataclass
import sys
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
ROOT_CLAUDE_BODY: Final = "# Claude Root\n\nClaude repository instructions.\n"
ROOT_AGENTS_BODY: Final = "# Agents Root\n\nCodex repository instructions.\n"
ROOT_SHARED_BODY: Final = "# Shared Root\n\nShared repository instructions.\n"

# Invented product-command payloads the harness owns, for command-slot preservation,
# sibling-fill, and conflict tests. Their identity across a re-render is what the tests
# assert; the strings carry no domain vocabulary.
SAMPLE_COMMAND_BODY: Final = "Build: `product build --all`"
SAMPLE_COMMAND_BODY_ALT: Final = "Build: `product build --changed`"

# Source-template content probes for the rendered-output session-result check.
SESSION_MANAGEMENT_HEADING = "## Session Management"
SESSION_ARCHIVE_RESULT_INSTRUCTION = "Before archiving a claimed session"
SESSION_RESULT_FRONTMATTER_FIELD = "`result`"

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


def root_instruction_topology_only_claude() -> RootInstructionTopology:
    """Return a root topology with only the Claude harness instruction file present."""
    return RootInstructionTopology(
        files={INSTRUCTION_CLAUDE: ROOT_CLAUDE_BODY}, symlinks={}
    )


def root_instruction_topology_only_agents() -> RootInstructionTopology:
    """Return a root topology with only the Codex harness instruction file present."""
    return RootInstructionTopology(
        files={INSTRUCTION_AGENTS: ROOT_AGENTS_BODY}, symlinks={}
    )


def root_instruction_topology_separate() -> RootInstructionTopology:
    """Return a root topology with two independent harness instruction files."""
    return RootInstructionTopology(
        files={
            INSTRUCTION_CLAUDE: ROOT_CLAUDE_BODY,
            INSTRUCTION_AGENTS: ROOT_AGENTS_BODY,
        },
        symlinks={},
    )


def root_instruction_topology_symlinked() -> RootInstructionTopology:
    """Return a root topology matching a shared instruction file with a harness symlink."""
    return RootInstructionTopology(
        files={INSTRUCTION_AGENTS: ROOT_SHARED_BODY},
        symlinks={INSTRUCTION_CLAUDE: INSTRUCTION_AGENTS},
    )


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


def write_both_instruction_files(
    module: ModuleType,
    repo_root: pathlib.Path,
    languages: tuple[str, ...],
    version: str,
) -> None:
    """Render and write root CLAUDE.md and AGENTS.md with router blocks and scaffolded slots.

    Mirrors the writer's own shape — the router block plus every fixed command-slot fence — so a
    file this helper produces is fence-complete like a real ``--write`` output. This root
    instruction-file setup policy lives in the harness rather than a test body.
    """
    template = build_template(version)
    for harness, filename in module.AGENT_HARNESS_INSTRUCTION_FILENAMES.items():
        block = module.render(template, languages, version, harness)
        (repo_root / filename).write_text(
            module.ensure_slot_fences(module.upsert_managed_block("", block)),
            encoding="utf-8",
        )


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
    """Initialize a git repository with a committed-safe identity for drift-gate tests."""
    git_command(repo_root, "init")
    git_command(repo_root, "config", "user.name", "Test User")
    git_command(repo_root, "config", "user.email", "test@example.com")


def remove_command_slot_fence(text: str, slot: str) -> str:
    """Return ``text`` with one command slot's fence and body removed, for missing-fence tests.

    The fence markers come from the generator's source-owned ``slot_open_marker`` /
    ``slot_close_marker`` accessors, so this setup helper never re-spells the module's fence
    format.
    """
    module = load_instruction_block_module()
    open_marker = module.slot_open_marker(slot)
    close_marker = module.slot_close_marker(slot)
    start = text.find(open_marker)
    if start == -1:
        return text
    end = text.find(close_marker, start)
    if end == -1:
        return text
    prefix = text[:start].rstrip("\n")
    suffix = text[end + len(close_marker) :].lstrip("\n")
    joiner = "\n\n" if prefix and suffix else ""
    return f"{prefix}{joiner}{suffix}"
