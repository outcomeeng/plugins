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
from pathlib import Path
from typing import Final, Protocol, cast

from outcomeeng.distribution.contracts import DIST_DIR_NAME

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
_GENERATOR: Final = (
    REPO_ROOT
    / "src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py"
)
DIST_TEMPLATE_RELATIVE_PATH: Final = Path(
    "spec-tree/skills/understand/templates/instruction-block.md"
)
HEADER: Final = "root instruction blocks differ from a fresh render."
REMEDIATION: Final = "Run `just build-instructions` and commit the regenerated root CLAUDE.md and AGENTS.md."
SLOT_CONFLICT_HEADER: Final = (
    "root instruction blocks carry a command slot filled differently in each file."
)
SLOT_CONFLICT_REMEDIATION: Final = (
    "Reconcile the conflicting slot with `/update-instruction-block`, which picks the "
    "git-more-recent body, then commit the reconciled root CLAUDE.md and AGENTS.md."
)
UNRESOLVED_BUILD_TEMPLATE_TOKENS: Final = ("{{!", "!}}", "{!%", "%!}", "{!#", "#!}")
BUILD_INSTRUCTIONS_RECIPE: Final = "build-instructions"
INSTRUCTIONS_CHECK_RECIPE: Final = "instructions-check"
WRITE_FLAG: Final = "--write"
JUSTFILE_NAME: Final = "justfile"


class InstructionBlockRenderError(RuntimeError):
    """Base error for instruction-block rendering failures."""


class UnresolvedInstructionTemplateError(InstructionBlockRenderError):
    """Raised when a rendered harness template still contains build macros."""


class InstructionBlockModule(Protocol):
    """Subset of the shipped instruction-block generator reused by the product gate."""

    AGENT_HARNESS_INSTRUCTION_FILENAMES: dict[str, str]
    OBSOLETE_SPX_INSTRUCTION_FILENAMES: tuple[str, ...]

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

    def remove_obsolete_spx_instruction_files(self, repo_root: Path) -> None: ...

    def conflicting_command_slots(self, repo_root: Path) -> tuple[str, ...]: ...

    def slot_reference(self, slot: str) -> str: ...


def _run(
    args: Sequence[str], *, cwd: Path = REPO_ROOT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, capture_output=True, text=True, check=True
    )


def load_instruction_block_module() -> InstructionBlockModule:
    """Load the shipped instruction-block generator to reuse its pure render contract."""
    spec = importlib.util.spec_from_file_location("instruction_block", _GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load instruction_block from {_GENERATOR}")
    module = importlib.util.module_from_spec(spec)
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


def regenerate_instruction_blocks() -> None:
    """Render both root instruction files in place from committed harness dist templates."""
    module = load_instruction_block_module()
    spx_dir = REPO_ROOT / "spx"
    templates = load_harness_templates(module)
    paths = {
        harness: dist_template_path(harness)
        for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    rendered = render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.detect_languages_from_tree(spx_dir),
        template_paths=paths,
    )
    module.write_root_instruction_files(REPO_ROOT, rendered)
    module.remove_obsolete_spx_instruction_files(REPO_ROOT)


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


def conflicting_command_slots(
    *, repo_root: Path = REPO_ROOT, module: InstructionBlockModule | None = None
) -> tuple[str, ...]:
    """Return fixed command slots filled with different bodies across the root files.

    Sibling-fill makes an empty-and-filled slot pair identical on regenerate, so a difference
    that survives is a genuine two-sided conflict the deterministic writer leaves unresolved for
    the update skill's git-recency judgment. Reporting it keeps the gate from passing over a
    slot that names one command for Claude Code and a different one for Codex.
    """
    instruction_module = module or load_instruction_block_module()
    return instruction_module.conflicting_command_slots(repo_root)


def render_report(
    drift: Sequence[str],
    conflicts: Sequence[str] = (),
    *,
    module: InstructionBlockModule | None = None,
) -> str:
    """Render the actionable drift report from drifting paths and conflicting command slots.

    A conflicting slot is named through the generator's source-owned ``slot_reference``, so the
    report and the fence markers share one ``SPEC-TREE:{slot}`` vocabulary rather than a copy.
    """
    sections: list[str] = []
    if drift:
        sections += [HEADER, "", *(f"  {path}" for path in drift), "", REMEDIATION]
    if conflicts:
        instruction_module = module or load_instruction_block_module()
        if sections:
            sections.append("")
        sections += [
            SLOT_CONFLICT_HEADER,
            "",
            *(f"  {instruction_module.slot_reference(slot)}" for slot in conflicts),
            "",
            SLOT_CONFLICT_REMEDIATION,
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
        conflicts = conflicting_command_slots()
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
    if not drift and not conflicts:
        return 0
    print(render_report(drift, conflicts))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
