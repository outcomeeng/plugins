"""CLI: compute the working diff against the resolved base ref.

Resolves ``base_ref`` from the precedence chain (env -> git symbolic-ref),
resolves ``head_ref`` from a parallel precedence chain
(``SPX_VERIFY_HEAD_REF`` env -> literal ``HEAD``), emits the committed
merge-base diff, then appends staged, unstaged, and untracked worktree diffs.

Exit codes:

- ``0`` — the diff was produced (possibly empty).
- non-zero — no ``base_ref`` could be resolved from any source, or git itself
  fails.

Tested with:

- ``SPX_VERIFY_BASE_REF`` -> emits the committed diff.
- Staged, unstaged, and untracked worktree changes -> emits all four sections.
- ``origin/HEAD`` derivation without env -> emits the diff.
- ``SPX_VERIFY_HEAD_REF`` overrides the default ``HEAD`` head ref.
- ``--bundle-dir`` -> writes ``diff.md`` and ``manifest.json`` to the named
  scratch directory and reports the bundle paths.
- Missing base-ref sources -> exits non-zero and names env and git sources.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import shlex
import subprocess
import sys
from dataclasses import dataclass
from types import ModuleType

ENV_BASE_REF = "SPX_VERIFY_BASE_REF"
ENV_HEAD_REF = "SPX_VERIFY_HEAD_REF"
DEFAULT_HEAD_REF = "HEAD"
MANIFEST_SCHEMA_VERSION = 1
BUNDLE_DIFF_FILENAME = "diff.md"
BUNDLE_MANIFEST_FILENAME = "manifest.json"
DIFF_SECTION_COMMITTED = "Committed diff"
DIFF_SECTION_STAGED = "Staged diff"
DIFF_SECTION_UNSTAGED = "Unstaged diff"
DIFF_SECTION_UNTRACKED = "Untracked files"
DIFF_RENAME_COPY_ARGS = ("--find-renames", "--find-copies")
RENAME_STATUS_PREFIX = "R"
COPY_STATUS_PREFIX = "C"


@dataclass(frozen=True)
class DiffSection:
    title: str
    text: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class SectionManifest:
    title: str
    files: tuple[str, ...]
    start_line: int
    line_count: int
    byte_start: int
    byte_length: int


def _load_changeset_scope() -> ModuleType:
    """Load the ``changeset_scope`` module via ``importlib``.

    The canonical git-derivation home is the sibling ``scope-changeset``
    skill's bundled module, which surfaces ``detect_base_ref``,
    ``remote_tracking_ref``, and
    ``BaseRefNotConfiguredError``. Loading here keeps authoritative base-ref
    derivation and the remote-tracking composition a single source rather
    than a private duplicate inside this script.
    """
    cached = sys.modules.get("changeset_scope")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "scope-changeset"
        / "scripts"
        / "changeset_scope.py"
    )
    if not path.is_file():
        raise RuntimeError(
            f"cannot load changeset_scope: {path} does not exist. The "
            "scope-changeset skill must be installed beside review-changes "
            "under the same skills directory; reinstall the product-tree "
            "plugin so both skills are present."
        )
    spec = importlib.util.spec_from_file_location("changeset_scope", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"cannot load changeset_scope from {path}: Python found no import "
            "loader for the file. Confirm the file is a readable .py module "
            "and reinstall the product-tree plugin if it is damaged."
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["changeset_scope"] = module
    spec.loader.exec_module(module)
    return module


def resolve_head_ref() -> str:
    """Resolve head_ref via env -> literal ``HEAD``.

    Symmetric with ``resolve_base_ref`` but with a literal default so
    the common "diff against current HEAD" case requires no
    configuration.
    """
    env_value = os.environ.get(ENV_HEAD_REF, "").strip()
    if env_value:
        return env_value
    return DEFAULT_HEAD_REF


def resolve_base_ref() -> str:
    """Resolve base_ref via env -> git, aborting when no source yields one.

    The error message names every source so the operator knows which to
    populate. No fallback to a literal default — silent fallbacks would
    let a diff compute against the wrong ref without surfacing it. The
    git derivation delegates to ``changeset_scope.detect_base_ref()``
    so the symbolic-ref read lives in one source, then composes the
    remote-tracking ref via ``changeset_scope.remote_tracking_ref`` so a
    stale local branch ref cannot widen the diff. Env values are used verbatim
    because the operator owns explicit override refs.
    """
    env_value = os.environ.get(ENV_BASE_REF, "").strip()
    if env_value:
        return env_value
    changeset_scope = _load_changeset_scope()
    try:
        bare_base = changeset_scope.detect_base_ref(pathlib.Path.cwd())
    except changeset_scope.BaseRefNotConfiguredError as exc:
        raise RuntimeError(
            "cannot resolve base_ref from any source; tried: "
            f"{ENV_BASE_REF} env (unset or empty), git symbolic-ref "
            f"refs/remotes/origin/HEAD ({str(exc) or 'no detail reported'}) in "
            f"{pathlib.Path.cwd()}. Set {ENV_BASE_REF} to the base ref, for "
            "example origin/main, or run `git remote set-head origin --auto` "
            "so origin/HEAD resolves."
        ) from exc
    except FileNotFoundError as exc:
        raise RuntimeError(
            "cannot resolve base_ref from any source; tried: "
            f"{ENV_BASE_REF} env (unset or empty), git symbolic-ref "
            "refs/remotes/origin/HEAD (the `git` executable was not found on "
            f"PATH: {str(exc) or 'no detail reported'}). Install git or add "
            f"it to PATH, or set {ENV_BASE_REF} and rerun."
        ) from exc
    return str(changeset_scope.remote_tracking_ref(bare_base))


def _run_git(
    args: list[str], *, accepted_codes: tuple[int, ...] = (0,)
) -> subprocess.CompletedProcess[str]:
    """Run ``git`` with ``args``, raising a located, actionable error on failure.

    The error names the full command, the working directory, the exit code
    against the accepted codes, and git's stderr (or states that stderr was
    empty), then says what to check.
    """
    command = ["git", *args]
    try:
        completed = subprocess.run(  # noqa: S603 — refs derived from validated sources
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise RuntimeError(
            f"cannot run `{shlex.join(command)}` in {pathlib.Path.cwd()}: "
            f"{str(exc) or type(exc).__name__}. Install git or add it to "
            "PATH, then rerun."
        ) from exc
    if completed.returncode not in accepted_codes:
        stderr = (completed.stderr or "").strip()
        accepted = " or ".join(str(code) for code in accepted_codes)
        raise RuntimeError(
            f"`{shlex.join(command)}` exited {completed.returncode} (expected "
            f"{accepted}) in {pathlib.Path.cwd()}: "
            f"{stderr or 'git wrote nothing to stderr'}. Run the command by "
            "hand to reproduce it; confirm the working directory is inside a "
            f"git worktree and that every ref it names exists (base ref from "
            f"{ENV_BASE_REF} or origin/HEAD, head ref from {ENV_HEAD_REF} or "
            f"{DEFAULT_HEAD_REF}), fetching the remote if a ref is missing."
        )
    return completed


def _git_diff(args: list[str]) -> str:
    return _run_git(["diff", *args]).stdout


def _git_stdout(args: list[str]) -> str:
    return _run_git(args).stdout


def _diff_section(title: str, diff: str) -> str:
    if not diff:
        return ""
    return f"### {title}\n\n{diff}"


def _dedupe_paths(paths: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    unique: list[str] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return tuple(unique)


def _diff_changed_paths(args: list[str]) -> tuple[str, ...]:
    command = ["git", "diff", "--name-status", "-z", *DIFF_RENAME_COPY_ARGS, *args]
    records = _git_stdout(command[1:]).split("\0")
    if records and records[-1] == "":
        records.pop()

    paths: list[str] = []
    index = 0
    while index < len(records):
        status = records[index]
        index += 1
        if not status:
            raise RuntimeError(
                f"`{shlex.join(command)}` emitted an empty status field at "
                f"record {index} of {len(records)}. The output is not the "
                "NUL-separated name-status format this script parses; rerun "
                "the command by hand and check that git is not wrapped by a "
                "pager or alias that rewrites its output."
            )
        path_count = (
            2 if status.startswith((RENAME_STATUS_PREFIX, COPY_STATUS_PREFIX)) else 1
        )
        if index + path_count > len(records):
            raise RuntimeError(
                f"`{shlex.join(command)}` emitted a truncated record: status "
                f"{status!r} at record {index} needs {path_count} path field(s) "
                f"but only {len(records) - index} remain of {len(records)} "
                "records. Rerun the command by hand; a truncated stream "
                "means git exited early or its output was cut."
            )
        paths.extend(records[index : index + path_count])
        index += path_count
    return _dedupe_paths(paths)


def _untracked_paths() -> tuple[str, ...]:
    return tuple(
        line
        for line in _git_stdout(
            ["ls-files", "--others", "--exclude-standard", "-z"]
        ).split("\0")
        if line
    )


def _untracked_diff(paths: tuple[str, ...]) -> str:
    sections: list[str] = []
    for path in paths:
        completed = _run_git(
            ["diff", "--no-index", "--", os.devnull, path], accepted_codes=(0, 1)
        )
        sections.append(completed.stdout)
    return "\n".join(sections)


def diff_sections(base_ref: str, head_ref: str) -> tuple[DiffSection, ...]:
    """Return non-empty review-input sections with changed file names."""
    untracked_paths = _untracked_paths()
    candidates = (
        DiffSection(
            DIFF_SECTION_COMMITTED,
            _diff_section(
                DIFF_SECTION_COMMITTED,
                _git_diff([*DIFF_RENAME_COPY_ARGS, f"{base_ref}...{head_ref}"]),
            ),
            _diff_changed_paths([f"{base_ref}...{head_ref}"]),
        ),
        DiffSection(
            DIFF_SECTION_STAGED,
            _diff_section(
                DIFF_SECTION_STAGED,
                _git_diff([*DIFF_RENAME_COPY_ARGS, "--cached"]),
            ),
            _diff_changed_paths(["--cached"]),
        ),
        DiffSection(
            DIFF_SECTION_UNSTAGED,
            _diff_section(
                DIFF_SECTION_UNSTAGED,
                _git_diff([*DIFF_RENAME_COPY_ARGS]),
            ),
            _diff_changed_paths([]),
        ),
        DiffSection(
            DIFF_SECTION_UNTRACKED,
            _diff_section(DIFF_SECTION_UNTRACKED, _untracked_diff(untracked_paths)),
            untracked_paths,
        ),
    )
    return tuple(section for section in candidates if section.text)


def combined_diff(base_ref: str, head_ref: str) -> str:
    """Return committed, staged, unstaged, and untracked diffs as one review input."""
    return "\n".join(section.text for section in diff_sections(base_ref, head_ref))


def _section_manifests(
    sections: tuple[DiffSection, ...],
) -> tuple[SectionManifest, ...]:
    manifests: list[SectionManifest] = []
    byte_cursor = 0
    line_cursor = 1
    for index, section in enumerate(sections):
        if index:
            byte_cursor += len("\n".encode("utf-8"))
            line_cursor += 1
        section_bytes = section.text.encode("utf-8")
        line_count = len(section.text.splitlines())
        manifests.append(
            SectionManifest(
                title=section.title,
                files=section.files,
                start_line=line_cursor,
                line_count=line_count,
                byte_start=byte_cursor,
                byte_length=len(section_bytes),
            )
        )
        byte_cursor += len(section_bytes)
        line_cursor += section.text.count("\n")
    return tuple(manifests)


def _manifest_dict(
    *,
    base_ref: str,
    head_ref: str,
    diff_text: str,
    sections: tuple[DiffSection, ...],
) -> dict[str, object]:
    diff_bytes = diff_text.encode("utf-8")
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "diff_path": BUNDLE_DIFF_FILENAME,
        "diff_sha256": hashlib.sha256(diff_bytes).hexdigest(),
        "diff_bytes": len(diff_bytes),
        "sections": [
            {
                "title": section.title,
                "files": list(section.files),
                "start_line": section.start_line,
                "line_count": section.line_count,
                "byte_start": section.byte_start,
                "byte_length": section.byte_length,
            }
            for section in _section_manifests(sections)
        ],
    }


def _resolve_bundle_dir(bundle_dir: pathlib.Path) -> pathlib.Path:
    """Return a normalized bundle directory path."""
    resolved = bundle_dir.expanduser().resolve(strict=False)
    if resolved == resolved.parent:
        raise RuntimeError(
            f"--bundle-dir must not be the filesystem root; got {bundle_dir} "
            f"which resolves to {resolved}. Pass a dedicated scratch "
            "directory outside the git worktree."
        )
    if resolved.exists() and not resolved.is_dir():
        raise RuntimeError(
            f"--bundle-dir exists and is not a directory: {resolved}. Pass a "
            "directory path, or a path that does not exist yet."
        )
    worktree_root = pathlib.Path(
        _git_stdout(["rev-parse", "--show-toplevel"]).strip()
    ).resolve(strict=True)
    if resolved == worktree_root or resolved.is_relative_to(worktree_root):
        raise RuntimeError(
            f"--bundle-dir must be outside the git worktree; {resolved} is "
            f"inside the worktree rooted at {worktree_root}. Pass a scratch "
            "directory elsewhere, for example one created with `mktemp -d`."
        )
    return resolved


def _bundle_file_path(bundle_dir: pathlib.Path, filename: str) -> pathlib.Path:
    """Return a bundle file path guaranteed to stay inside ``bundle_dir``."""
    path = (bundle_dir / filename).resolve(strict=False)
    if not path.is_relative_to(bundle_dir):
        raise RuntimeError(
            f"bundle file escapes --bundle-dir: {filename!r} resolves to "
            f"{path}, outside {bundle_dir}. Bundle filenames are fixed "
            f"({BUNDLE_DIFF_FILENAME}, {BUNDLE_MANIFEST_FILENAME}); a symlink "
            "inside the bundle directory points elsewhere, so remove it or "
            "choose another --bundle-dir."
        )
    return path


def write_bundle(
    *, base_ref: str, head_ref: str, bundle_dir: pathlib.Path
) -> dict[str, object]:
    """Write a scratch diff bundle and return a small summary."""
    safe_bundle_dir = _resolve_bundle_dir(bundle_dir)
    sections = diff_sections(base_ref, head_ref)
    diff_text = "\n".join(section.text for section in sections)
    manifest = _manifest_dict(
        base_ref=base_ref,
        head_ref=head_ref,
        diff_text=diff_text,
        sections=sections,
    )
    safe_bundle_dir.mkdir(parents=True, exist_ok=True)
    diff_path = _bundle_file_path(safe_bundle_dir, BUNDLE_DIFF_FILENAME)
    manifest_path = _bundle_file_path(safe_bundle_dir, BUNDLE_MANIFEST_FILENAME)
    diff_path.write_text(diff_text, encoding="utf-8")
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "diff_path": str(diff_path),
        "manifest_path": str(manifest_path),
        "diff_bytes": manifest["diff_bytes"],
        "section_count": len(sections),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute git diff against the resolved base ref."
    )
    parser.add_argument(
        "--bundle-dir",
        type=pathlib.Path,
        default=None,
        help=(
            "write diff.md and manifest.json into this scratch "
            "directory instead of writing the full diff to stdout"
        ),
    )
    args = parser.parse_args(argv)

    try:
        base_ref = resolve_base_ref()
    except RuntimeError as exc:
        sys.stderr.write(
            f"{str(exc) or 'compute_diff.py could not resolve base_ref'}\n"
        )
        return 1

    head_ref = resolve_head_ref()

    try:
        if args.bundle_dir is not None:
            summary = write_bundle(
                base_ref=base_ref, head_ref=head_ref, bundle_dir=args.bundle_dir
            )
            sys.stdout.write(json.dumps(summary, sort_keys=True) + "\n")
            return 0
        diff = combined_diff(base_ref, head_ref)
    except RuntimeError as exc:
        sys.stderr.write(
            f"{str(exc) or 'compute_diff.py failed with an empty RuntimeError'}\n"
        )
        return 1
    sys.stdout.write(diff)
    return 0


if __name__ == "__main__":
    sys.exit(main())
