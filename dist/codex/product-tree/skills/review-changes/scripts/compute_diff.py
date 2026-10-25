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
- A renamed file -> listed once under its new path; the manifest's ``renames``
  records its former path and whether its content is unchanged.
- ``spx/local/generated-sources.toml`` read at the scope's base ref -> the
  manifest's ``generated_extents`` lists each changed file that a relation's
  whole-file output pattern matches, grouped by relation; a region-bounded
  output leaves its file ordinary, and a base without the declaration lists no
  extent.
- A changeset that changes ``spx/local/generated-sources.toml`` -> the manifest's
  ``generated_declaration_changed`` is true and every listed relation is flagged
  with the changed declaration as its ``flagged_reason``, so no changed file is
  exempt by declaration.
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
import re
import subprocess
import sys
import tomllib
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
UNCHANGED_SIMILARITY = 100
GENERATED_SOURCES_PATH = pathlib.PurePosixPath("spx/local/generated-sources.toml")

# Keys of the bundle manifest ``write_bundle`` writes.
MANIFEST_SCHEMA_VERSION_KEY = "schema_version"
MANIFEST_BASE_REF = "base_ref"
MANIFEST_HEAD_REF = "head_ref"
MANIFEST_DIFF_PATH = "diff_path"
MANIFEST_DIFF_SHA256 = "diff_sha256"
MANIFEST_DIFF_BYTES = "diff_bytes"
MANIFEST_SECTIONS = "sections"
MANIFEST_SECTION_TITLE = "title"
MANIFEST_SECTION_FILES = "files"
MANIFEST_SECTION_START_LINE = "start_line"
MANIFEST_SECTION_LINE_COUNT = "line_count"
MANIFEST_SECTION_BYTE_START = "byte_start"
MANIFEST_SECTION_BYTE_LENGTH = "byte_length"
MANIFEST_RENAMES = "renames"
MANIFEST_GENERATED_EXTENTS = "generated_extents"
MANIFEST_GENERATED_DECLARATION_CHANGED = "generated_declaration_changed"
# Keys of the summary ``write_bundle`` returns and ``main`` prints.
SUMMARY_DIFF_PATH = "diff_path"
SUMMARY_MANIFEST_PATH = "manifest_path"
SUMMARY_DIFF_BYTES = "diff_bytes"
SUMMARY_SECTION_COUNT = "section_count"


@dataclass(frozen=True)
class ChangedEntry:
    """One changed path; ``former_path`` is set for a rename only."""

    path: str
    former_path: str | None = None
    similarity: int | None = None


@dataclass(frozen=True)
class DiffSection:
    title: str
    text: str
    files: tuple[str, ...]
    renames: tuple[ChangedEntry, ...] = ()


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


def _diff_changed_entries(args: list[str]) -> tuple[ChangedEntry, ...]:
    """Return each changed path once; a rename carries its former path.

    A copy lists only its destination, because the copy source is unchanged.
    """
    command = ["git", "diff", "--name-status", "-z", *DIFF_RENAME_COPY_ARGS, *args]
    records = _git_stdout(command[1:]).split("\0")
    if records and records[-1] == "":
        records.pop()

    entries: dict[str, ChangedEntry] = {}
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
        is_rename = status.startswith(RENAME_STATUS_PREFIX)
        path_count = 2 if is_rename or status.startswith(COPY_STATUS_PREFIX) else 1
        if index + path_count > len(records):
            raise RuntimeError(
                f"`{shlex.join(command)}` emitted a truncated record: status "
                f"{status!r} at record {index} needs {path_count} path field(s) "
                f"but only {len(records) - index} remain of {len(records)} "
                "records. Rerun the command by hand; a truncated stream "
                "means git exited early or its output was cut."
            )
        paths = records[index : index + path_count]
        index += path_count
        entry = ChangedEntry(path=paths[-1])
        if is_rename:
            similarity = status[len(RENAME_STATUS_PREFIX) :]
            entry = ChangedEntry(
                path=paths[1],
                former_path=paths[0],
                similarity=int(similarity) if similarity.isdigit() else None,
            )
        entries.setdefault(entry.path, entry)
    return tuple(entries.values())


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


def _tracked_section(title: str, diff_args: list[str]) -> DiffSection:
    entries = _diff_changed_entries(diff_args)
    return DiffSection(
        title,
        _diff_section(title, _git_diff([*DIFF_RENAME_COPY_ARGS, *diff_args])),
        tuple(entry.path for entry in entries),
        tuple(entry for entry in entries if entry.former_path is not None),
    )


def diff_sections(base_ref: str, head_ref: str) -> tuple[DiffSection, ...]:
    """Return non-empty review-input sections with changed file names."""
    untracked_paths = _untracked_paths()
    candidates = (
        _tracked_section(DIFF_SECTION_COMMITTED, [f"{base_ref}...{head_ref}"]),
        _tracked_section(DIFF_SECTION_STAGED, ["--cached"]),
        _tracked_section(DIFF_SECTION_UNSTAGED, []),
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
    renames: list[dict[str, object]],
    generated_extents: list[dict[str, object]],
    generated_declaration_changed: bool,
) -> dict[str, object]:
    diff_bytes = diff_text.encode("utf-8")
    return {
        MANIFEST_SCHEMA_VERSION_KEY: MANIFEST_SCHEMA_VERSION,
        MANIFEST_BASE_REF: base_ref,
        MANIFEST_HEAD_REF: head_ref,
        MANIFEST_DIFF_PATH: BUNDLE_DIFF_FILENAME,
        MANIFEST_DIFF_SHA256: hashlib.sha256(diff_bytes).hexdigest(),
        MANIFEST_DIFF_BYTES: len(diff_bytes),
        MANIFEST_SECTIONS: [
            {
                MANIFEST_SECTION_TITLE: section.title,
                MANIFEST_SECTION_FILES: list(section.files),
                MANIFEST_SECTION_START_LINE: section.start_line,
                MANIFEST_SECTION_LINE_COUNT: section.line_count,
                MANIFEST_SECTION_BYTE_START: section.byte_start,
                MANIFEST_SECTION_BYTE_LENGTH: section.byte_length,
            }
            for section in _section_manifests(sections)
        ],
        MANIFEST_RENAMES: renames,
        MANIFEST_GENERATED_EXTENTS: generated_extents,
        MANIFEST_GENERATED_DECLARATION_CHANGED: generated_declaration_changed,
    }


def rename_records(sections: tuple[DiffSection, ...]) -> list[dict[str, object]]:
    """List each renamed path once with its former path.

    ``content_unchanged`` holds when every section that lists the path lists it
    as a rename of identical content, so a rename edited afterwards in the
    staged, unstaged, or untracked state is not a pure rename.
    """
    records: dict[str, dict[str, object]] = {}
    plain: set[str] = set()
    for section in sections:
        renamed = {entry.path: entry for entry in section.renames}
        for path in section.files:
            entry = renamed.get(path)
            if entry is None:
                plain.add(path)
                continue
            unchanged = entry.similarity == UNCHANGED_SIMILARITY
            record = records.get(path)
            if record is None:
                records[path] = {
                    "path": path,
                    "former_path": entry.former_path,
                    "content_unchanged": unchanged,
                }
            elif not unchanged:
                record["content_unchanged"] = False
    for path in plain:
        if path in records:
            records[path]["content_unchanged"] = False
    return [records[path] for path in sorted(records)]


def _glob_regex(pattern: str) -> re.Pattern[str]:
    """Compile a declaration path pattern: ``**`` spans directories, ``*`` and
    ``?`` stay inside one path segment."""
    out: list[str] = []
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            out.append("(?:.*/)?")
            index += 3
        elif pattern.startswith("**", index):
            out.append(".*")
            index += 2
        elif pattern[index] == "*":
            out.append("[^/]*")
            index += 1
        elif pattern[index] == "?":
            out.append("[^/]")
            index += 1
        else:
            out.append(re.escape(pattern[index]))
            index += 1
    return re.compile("".join(out))


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(_glob_regex(pattern).fullmatch(path) for pattern in patterns)


def _pattern_list(
    relation: dict[str, object], key: str, *, ordinal: int, source: str
) -> list[str]:
    value = relation.get(key, [])
    if not isinstance(value, list):
        raise RuntimeError(
            f"{source} relation {ordinal}: key {key!r} must be an array, got "
            f"{type(value).__name__}. Fix the declaration and rerun."
        )
    return [item for item in value if isinstance(item, str)]


def _declaration_at_base(base_ref: str) -> tuple[str, str] | None:
    """Return the declaration text committed at ``base_ref`` with its label.

    The label names the committed blob, ``<base_ref>:<path>``. A base without
    the declaration yields ``None``.
    """
    path = str(GENERATED_SOURCES_PATH)
    if not _git_stdout(["ls-tree", "--name-only", base_ref, "--", path]).strip():
        return None
    label = f"{base_ref}:{path}"
    return _git_stdout(["show", label]), label


def load_generated_relations(base_ref: str) -> list[dict[str, object]]:
    """Read the generated-source declaration committed at ``base_ref``.

    The declaration comes from ``git show <base_ref>:spx/local/generated-sources.toml``,
    never from the working tree, so a changeset cannot widen its own exemption
    and a reviewed head that is not the checked-out tree reads the same
    declaration. Each returned relation carries its 1-based ``relation`` ordinal
    and the whole-file ``outputs`` patterns only: a region-bounded output (an
    inline table naming ``file``, ``begin``, and ``end``) bounds no whole-file
    extent. A base without the declaration yields no relation.
    """
    declaration = _declaration_at_base(base_ref)
    if declaration is None:
        return []
    text, source = declaration
    try:
        document = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise RuntimeError(
            f"cannot read the generated-source declaration {source}: "
            f"{str(exc) or type(exc).__name__}. Fix the declaration and rerun."
        ) from exc
    declared = document.get("relation", [])
    if not isinstance(declared, list):
        raise RuntimeError(
            f"{source} key 'relation' must be an array of tables, got "
            f"{type(declared).__name__}. Fix the declaration and rerun."
        )
    relations: list[dict[str, object]] = []
    for ordinal, relation in enumerate(declared, start=1):
        if not isinstance(relation, dict):
            raise RuntimeError(
                f"{source} relation {ordinal} must be a table, got "
                f"{type(relation).__name__}. Fix the declaration and rerun."
            )
        regenerate = relation.get("regenerate", "")
        relations.append(
            {
                "relation": ordinal,
                "outputs": _pattern_list(
                    relation, "outputs", ordinal=ordinal, source=source
                ),
                "sources": _pattern_list(
                    relation, "sources", ordinal=ordinal, source=source
                ),
                "generator": _pattern_list(
                    relation, "generator", ordinal=ordinal, source=source
                ),
                "regenerate": regenerate if isinstance(regenerate, str) else "",
            }
        )
    return relations


def generated_declaration_changed(
    changed_files: list[str], renames: list[dict[str, object]]
) -> bool:
    """Report whether the changeset changes the generated-source declaration.

    A rename's former path counts as changed.
    """
    declaration = str(GENERATED_SOURCES_PATH)
    return declaration in changed_files or any(
        record.get("former_path") == declaration for record in renames
    )


def generated_extents(
    relations: list[dict[str, object]],
    changed_files: list[str],
    renames: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Group the changed files that whole-file output patterns match by relation.

    A changeset that changes the declaration itself exempts nothing: every
    listed relation is flagged and carries the changed declaration as its
    ``flagged_reason``, so the runner treats every changed file as ordinary.

    A relation is flagged when the changeset also changes one of its declared
    sources or generator paths (a rename's former path counts as changed), so
    the extents are evidence the reviewer may read. A relation's own extents
    never count as its changed inputs.
    """
    declaration_changed = generated_declaration_changed(changed_files, renames)
    touched = set(changed_files)
    touched.update(
        str(record["former_path"])
        for record in renames
        if isinstance(record.get("former_path"), str)
    )
    extents: list[dict[str, object]] = []
    for relation in relations:
        outputs = relation["outputs"]
        sources = relation["sources"]
        generator = relation["generator"]
        assert isinstance(outputs, list)
        assert isinstance(sources, list)
        assert isinstance(generator, list)
        files = [path for path in changed_files if _matches_any(path, outputs)]
        if not files:
            continue
        inputs = sorted(touched - set(files))
        changed_sources = [path for path in inputs if _matches_any(path, sources)]
        changed_generator = [path for path in inputs if _matches_any(path, generator)]
        extents.append(
            {
                "relation": relation["relation"],
                "sources": sources,
                "generator": generator,
                "regenerate": relation["regenerate"],
                "files": files,
                "flagged": declaration_changed
                or bool(changed_sources or changed_generator),
                "flagged_reason": str(GENERATED_SOURCES_PATH)
                if declaration_changed
                else "",
                "changed_sources": changed_sources,
                "changed_generator": changed_generator,
            }
        )
    return extents


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
    changed_files = list(
        dict.fromkeys(path for section in sections for path in section.files)
    )
    renames = rename_records(sections)
    manifest = _manifest_dict(
        base_ref=base_ref,
        head_ref=head_ref,
        diff_text=diff_text,
        sections=sections,
        renames=renames,
        generated_extents=generated_extents(
            load_generated_relations(base_ref), changed_files, renames
        ),
        generated_declaration_changed=generated_declaration_changed(
            changed_files, renames
        ),
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
        SUMMARY_DIFF_PATH: str(diff_path),
        SUMMARY_MANIFEST_PATH: str(manifest_path),
        SUMMARY_DIFF_BYTES: manifest[MANIFEST_DIFF_BYTES],
        SUMMARY_SECTION_COUNT: len(sections),
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
