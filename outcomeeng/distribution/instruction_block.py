"""Actionable Spec Tree root-instruction-block writer and drift reporter for the validation gate.

The ``just build-instructions`` recipe and the ``just instructions-check`` gate run this
module to enforce the render-model ADR's gate: regenerate the managed Spec Tree instruction
blocks in root ``CLAUDE.md`` and ``AGENTS.md`` from the rendered harness templates committed
under ``dist/``, remove retired ``spx/`` instruction files, then fail when any root
instruction file drifts from its committed content. It is the instruction-block analogue of
``dist-diff``: authored templates first become harness-specific plugin output, then the root
instruction blocks render from that output.

A root instruction file absent from the index — a first run, or a worktree where the files
were never committed — registers as drift via ``--intent-to-add``, because a plain
``git diff`` reports only tracked changes and would otherwise pass silently while
leaving the freshly written files uncommitted.
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, cast

from outcomeeng.distribution.contracts import DIST_DIR_NAME

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
GENERATOR_RELATIVE_PATH: Final = Path(
    "src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py"
)
GENERATOR_PATH: Final = REPO_ROOT / GENERATOR_RELATIVE_PATH
AUTHORED_TEMPLATE_RELATIVE_PATH: Final = Path(
    "src/plugins/spec-tree/skills/update-instruction-block/templates/instruction-block.md"
)
AUTHORED_TEMPLATE_PATH: Final = REPO_ROOT / AUTHORED_TEMPLATE_RELATIVE_PATH
DIST_TEMPLATE_RELATIVE_PATH: Final = Path(
    "spec-tree/skills/update-instruction-block/templates/instruction-block.md"
)
HEADER: Final = "root instruction blocks differ from a fresh render."
REMEDIATION: Final = "Run `just build-instructions` and commit the regenerated root CLAUDE.md and AGENTS.md."
SHARED_DRIFT_HEADER: Final = "root instruction blocks carry a shared region that diverges or is present in only one file."
SHARED_DRIFT_REMEDIATION: Final = (
    "Reconcile the shared region with `/update-instruction-block`, which takes the "
    "git-more-recent side, then commit the reconciled root CLAUDE.md and AGENTS.md."
)
UNRESOLVED_BUILD_TEMPLATE_TOKENS: Final = ("{{!", "!}}", "{!%", "%!}", "{!#", "#!}")
FORBIDDEN_ROUTER_TOKENS: Final = (
    "Before archiving a claimed session",
    "`result`",
)
BUILD_INSTRUCTIONS_RECIPE: Final = "build-instructions"
INSTRUCTIONS_CHECK_RECIPE: Final = "instructions-check"
WRITE_FLAG: Final = "--write"
JUSTFILE_NAME: Final = "justfile"
MODULE_INVOCATION: Final = "outcomeeng.distribution.instruction_block"
LEFTHOOK_PATH: Final = Path("lefthook.yml")
REFRESH_WORKFLOW_PATH: Final = Path(".github/workflows/refresh-instruction-blocks.yml")
PRECOMMIT_BUILD_INSTRUCTIONS_COMMAND: Final = "run: just build-instructions"
LEGACY_DIRECT_TEMPLATE_ARGUMENT: Final = "--template src/plugins"
LEGACY_DIRECT_REPO_ROOT_ARGUMENT: Final = "--repo-root ."
WORKFLOW_DISPATCH_TRIGGER: Final = "workflow_dispatch:"
WORKFLOW_REGENERATE_STEP: Final = "Regenerate instruction blocks"
WORKFLOW_OPEN_PR_STEP: Final = "Open instruction-block refresh pull request"
WORKFLOW_CHECKOUT_STEP: Final = "Checkout"
WORKFLOW_INSTALL_JUST_STEP: Final = "Install just"
WORKFLOW_INSTALL_DPRINT_STEP: Final = "Install dprint"
WORKFLOW_JUST_CHECKSUM_ENV: Final = "JUST_SHA256"
WORKFLOW_DPRINT_VERSION_ENV: Final = "DPRINT_VERSION"
WORKFLOW_BUILD_INSTRUCTIONS_COMMAND: Final = "just build-instructions"
WORKFLOW_DRIFT_COMMAND: Final = "git status --porcelain"
DEFAULT_BRANCH: Final = "main"
WORKFLOW_JUST_CHECKSUM_REFERENCE: Final = f"${WORKFLOW_JUST_CHECKSUM_ENV}"
WORKFLOW_DPRINT_INSTALL_COMMAND: Final = (
    f'bun add -g "dprint@${{{WORKFLOW_DPRINT_VERSION_ENV}}}"'
)
WORKFLOW_DPRINT_VERSION_COMMAND: Final = "dprint --version"
FOUNDATION_POLICY_HEADING: Final = "### Before product-content access -> `/understand`"
FOUNDATION_POLICY_REQUIREMENTS: Final = (
    ("live foundation marker", "live `<SPEC_TREE_FOUNDATION>` marker"),
    ("spx path trigger", "anything under `spx/`"),
    ("source and test trigger", "source or test file"),
    ("session exemption", "`spx session` operations"),
    ("session inspection exemption", "inspection"),
    ("session archive exemption", "archive"),
    ("session release exemption", "release"),
    ("worktree-status exemption", "`spx worktree status`"),
    ("diagnose exemption", "`spx diagnose`"),
    ("no-patch Git exemption", "no-patch Git status, history, and topology"),
    ("product-path follow guard", "Never follow paths from their output"),
)


@dataclass(frozen=True)
class RefreshWorkflowContract:
    """Source-owned selectors and commands for instruction-block refresh workflow checks."""

    relative_path: Path
    dispatch_key: str
    checkout_step: str
    default_branch: str
    install_just_step: str
    just_checksum_env: str
    install_dprint_step: str
    dprint_version_env: str
    regenerate_step: str
    build_commands: tuple[str, ...]
    open_pr_step: str
    drift_probe: str
    automation_branch: str
    commit_subject: str

    def path(self, *, repo_root: Path = REPO_ROOT) -> Path:
        """Return the authored workflow path below ``repo_root``."""
        return repo_root / self.relative_path


REFRESH_WORKFLOW: Final = RefreshWorkflowContract(
    relative_path=Path(".github/workflows/refresh-instruction-blocks.yml"),
    dispatch_key="workflow_dispatch:",
    checkout_step="Checkout",
    default_branch="main",
    install_just_step="Install just",
    just_checksum_env="JUST_SHA256",
    install_dprint_step="Install dprint",
    dprint_version_env="DPRINT_VERSION",
    regenerate_step="Regenerate instruction blocks",
    build_commands=("just build-skills", "just build-instructions"),
    open_pr_step="Open instruction-block refresh pull request",
    drift_probe="git status --porcelain",
    automation_branch="automation/refresh-instruction-blocks",
    commit_subject="Refresh root instruction blocks",
)


class InstructionBlockRenderError(RuntimeError):
    """Base error for instruction-block rendering failures."""


class UnresolvedInstructionTemplateError(InstructionBlockRenderError):
    """Raised when a rendered harness template still contains build macros."""


class FoundationAccessPolicyError(InstructionBlockRenderError):
    """Raised when a rendered router omits part of its foundation access policy."""


class InstructionBlockModule(Protocol):
    """Subset of the shipped instruction-block generator reused by the product gate."""

    AGENT_HARNESS_INSTRUCTION_FILENAMES: dict[str, str]
    BOOTSTRAP_SHARED_REGION_NAME: str
    LANGUAGE_BY_EXTENSION: dict[str, str]
    OBSOLETE_SPX_INSTRUCTION_FILENAMES: tuple[str, ...]
    ROUTER_BLOCK_END: str
    ROUTER_MARKER_PREFIX: str
    TEMPLATE_VERSION_KEY: str

    def router_block_bounds(self, text: str) -> tuple[int, int] | None: ...

    def parse_template_version(self, text: str) -> str | None: ...

    def detect_languages_from_tree(self, spx_dir: Path) -> tuple[str, ...]: ...

    def render(
        self,
        template_text: str,
        languages: tuple[str, ...],
        installed_version: str,
        harness: str,
    ) -> str: ...

    def write_root_instruction_files(
        self, repo_root: Path, blocks_by_harness: Mapping[str, str]
    ) -> None: ...

    def parse_shared_regions(self, text: str) -> dict[str, str]: ...

    def remove_obsolete_spx_instruction_files(self, repo_root: Path) -> None: ...

    def shared_region_drift(self, repo_root: Path) -> tuple[str, ...]: ...


def _run(
    args: Sequence[str], *, cwd: Path = REPO_ROOT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, capture_output=True, text=True, check=True
    )


def load_instruction_block_module() -> InstructionBlockModule:
    """Load the shipped instruction-block generator to reuse its pure render contract."""
    cached = sys.modules.get("instruction_block")
    if cached is not None:
        return cast(InstructionBlockModule, cached)
    spec = importlib.util.spec_from_file_location("instruction_block", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load instruction_block from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass type introspection can resolve the module by name.
    sys.modules["instruction_block"] = module
    spec.loader.exec_module(module)
    return cast(InstructionBlockModule, module)


def instruction_paths(module: InstructionBlockModule | None = None) -> tuple[str, ...]:
    """Derive instruction-file paths from the generator's own enumeration."""
    instruction_module = module or load_instruction_block_module()
    return (
        *root_instruction_paths(instruction_module),
        *obsolete_spx_instruction_paths(instruction_module),
    )


def root_instruction_paths(
    module: InstructionBlockModule | None = None,
) -> tuple[str, ...]:
    """Return generated root instruction-file paths."""
    instruction_module = module or load_instruction_block_module()
    return tuple(instruction_module.AGENT_HARNESS_INSTRUCTION_FILENAMES.values())


def obsolete_spx_instruction_paths(
    module: InstructionBlockModule | None = None,
) -> tuple[str, ...]:
    """Return retired spx instruction-file paths that may still be tracked."""
    instruction_module = module or load_instruction_block_module()
    return tuple(
        f"spx/{name}" for name in instruction_module.OBSOLETE_SPX_INSTRUCTION_FILENAMES
    )


def dist_template_path(harness: str, *, repo_root: Path = REPO_ROOT) -> Path:
    """Return the rendered harness template path for one instruction-block harness."""
    return repo_root / DIST_DIR_NAME / harness / DIST_TEMPLATE_RELATIVE_PATH


def load_harness_templates(
    module: InstructionBlockModule | None = None, *, repo_root: Path = REPO_ROOT
) -> dict[str, str]:
    """Read rendered harness templates from ``dist/`` for every instruction-block harness."""
    instruction_module = module or load_instruction_block_module()
    templates: dict[str, str] = {}
    for harness in instruction_module.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        path = dist_template_path(harness, repo_root=repo_root)
        templates[harness] = path.read_text(encoding="utf-8")
    return templates


def assert_no_unresolved_build_macros(text: str, *, path: Path | str) -> None:
    """Reject dist templates that still contain build-time macro delimiters."""
    for token in UNRESOLVED_BUILD_TEMPLATE_TOKENS:
        if token in text:
            raise UnresolvedInstructionTemplateError(
                f"{path} contains unresolved build macro token {token!r}; "
                "run `just build-skills` before regenerating instruction blocks"
            )


def render_instruction_blocks_from_harness_templates(
    module: InstructionBlockModule,
    harness_templates: Mapping[str, str],
    languages: tuple[str, ...],
    *,
    template_paths: Mapping[str, Path | str] | None = None,
) -> dict[str, str]:
    """Render every root instruction block from its harness-specific dist template."""
    versions: dict[str, str] = {}
    for harness, template_text in harness_templates.items():
        path = (
            template_paths[harness]
            if template_paths is not None and harness in template_paths
            else harness
        )
        assert_no_unresolved_build_macros(template_text, path=path)
        version = module.parse_template_version(template_text)
        if version is None:
            raise InstructionBlockRenderError(f"{path} has no template_version")
        versions[harness] = version

    if len(set(versions.values())) != 1:
        details = ", ".join(
            f"{harness}={version}" for harness, version in sorted(versions.items())
        )
        raise InstructionBlockRenderError(
            f"harness instruction-block templates disagree on version: {details}"
        )

    return {
        harness: module.render(
            harness_templates[harness], languages, versions[harness], harness
        )
        for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }


def _markdown_section(document: str, heading: str) -> str:
    """Return the exact Markdown section beginning at ``heading``."""
    lines = document.splitlines()
    try:
        start = lines.index(heading)
    except ValueError as exc:
        raise FoundationAccessPolicyError(f"missing router section: {heading}") from exc
    heading_level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index, line in enumerate(lines[start + 1 :], start=start + 1):
        if line.startswith("#") and len(line) - len(line.lstrip("#")) <= heading_level:
            end = index
            break
    return "\n".join(lines[start:end])


def managed_router_block(document: str) -> str:
    """Extract the managed router block from a complete root instruction document."""
    module = load_instruction_block_module()
    bounds = module.router_block_bounds(document)
    if bounds is None:
        raise FoundationAccessPolicyError("missing complete standalone router block")
    start, end = bounds
    return document[start:end]


def validate_foundation_access_policy(
    blocks_by_harness: Mapping[str, str],
) -> None:
    """Reject a rendered harness router that weakens the product-content gate."""
    for harness, document in blocks_by_harness.items():
        router = managed_router_block(document)
        section = _markdown_section(router, FOUNDATION_POLICY_HEADING)
        missing = [
            name
            for name, required_text in FOUNDATION_POLICY_REQUIREMENTS
            if required_text not in section
        ]
        if missing:
            details = ", ".join(missing)
            raise FoundationAccessPolicyError(
                f"{harness} router foundation policy is incomplete: {details}"
            )
        forbidden = [token for token in FORBIDDEN_ROUTER_TOKENS if token in router]
        if forbidden:
            details = ", ".join(repr(token) for token in forbidden)
            raise FoundationAccessPolicyError(
                f"{harness} router contains forbidden session-result tokens: {details}"
            )


def regenerate_instruction_blocks(*, repo_root: Path = REPO_ROOT) -> None:
    """Render both root instruction files in place from committed harness dist templates."""
    module = load_instruction_block_module()
    spx_dir = repo_root / "spx"
    templates = load_harness_templates(module, repo_root=repo_root)
    paths = {
        harness: dist_template_path(harness, repo_root=repo_root)
        for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    rendered = render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.detect_languages_from_tree(spx_dir),
        template_paths=paths,
    )
    validate_foundation_access_policy(rendered)
    module.write_root_instruction_files(repo_root, rendered)
    module.remove_obsolete_spx_instruction_files(repo_root)


def intent_to_add_paths(
    paths: Sequence[str], *, repo_root: Path = REPO_ROOT
) -> tuple[str, ...]:
    """Return generated instruction-file paths that exist and can be marked intent-to-add."""
    return tuple(path for path in paths if (repo_root / path).exists())


def drifting_instruction_files(
    *, repo_root: Path = REPO_ROOT, module: InstructionBlockModule | None = None
) -> list[str]:
    """Return the root instruction files that drift from their committed content.

    ``--intent-to-add`` makes an absent-from-index file register as drift; a plain
    ``git diff`` reports only tracked changes and would pass silently on a first run.
    Missing root instruction files are drift directly; missing obsolete spx instruction
    files are skipped because only tracked deletion drift matters for retired paths.
    """
    instruction_module = module or load_instruction_block_module()
    root_paths = root_instruction_paths(instruction_module)
    paths = (*root_paths, *obsolete_spx_instruction_paths(instruction_module))
    missing_root_paths = [
        path for path in root_paths if not (repo_root / path).exists()
    ]
    existing_paths = intent_to_add_paths(paths, repo_root=repo_root)
    if existing_paths:
        _run(["git", "add", "--intent-to-add", *existing_paths], cwd=repo_root)
    result = _run(["git", "diff", "--name-only", "--", *paths], cwd=repo_root)
    drift = [line for line in result.stdout.splitlines() if line.strip()]
    return sorted({*missing_root_paths, *drift})


def drifting_shared_regions(
    *, repo_root: Path = REPO_ROOT, module: InstructionBlockModule | None = None
) -> tuple[str, ...]:
    """Return the shared regions that diverge or are present in only one root file.

    A shared region is kept byte-identical across the two files; a body that differs between them,
    or a region present in only one, is drift the deterministic writer leaves unresolved for the
    update skill's git-recency reconcile. Reporting it keeps the gate from passing over a region
    that carries one body for Claude Code and a different one — or none — for Codex.
    """
    instruction_module = module or load_instruction_block_module()
    return instruction_module.shared_region_drift(repo_root)


def render_report(
    drift: Sequence[str],
    shared_drift: Sequence[str] = (),
) -> str:
    """Render the actionable drift report from drifting paths and drifting shared regions."""
    sections: list[str] = []
    if drift:
        sections += [HEADER, "", *(f"  {path}" for path in drift), "", REMEDIATION]
    if shared_drift:
        if sections:
            sections.append("")
        sections += [
            SHARED_DRIFT_HEADER,
            "",
            *(f"  {name}" for name in shared_drift),
            "",
            SHARED_DRIFT_REMEDIATION,
        ]
    return "\n".join(sections)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate root instruction blocks from rendered dist templates."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write instruction blocks without checking git drift.",
    )
    args = parser.parse_args(argv)
    try:
        regenerate_instruction_blocks()
        if args.write:
            return 0
        drift = drifting_instruction_files()
        shared_drift = drifting_shared_regions()
    except InstructionBlockRenderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        # Surface the failed command's own diagnostic; captured output is otherwise
        # swallowed by the default traceback, leaving the reporter unactionable.
        sys.stderr.write(exc.stderr or "")
        print(
            f"{HEADER}\n  the root instruction-block gate failed; see the error above."
        )
        return 1
    if not drift and not shared_drift:
        return 0
    print(render_report(drift, shared_drift))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
