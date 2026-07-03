"""Deterministic generator for a product's root Spec Tree instruction block.

One repository is worked by both Claude Code and Codex at once, and each agent harness
retains its root instruction file across compaction: ``CLAUDE.md`` for Claude Code and
``AGENTS.md`` for Codex. The Spec Tree instructions are therefore a managed block in those
root files, not generated files under ``spx/``. Both blocks render from one
canonical template: the body is shared, and the spans that differ by agent harness
are authored once as ``<!-- harness:NAME -->`` blocks rendered only into that
harness's block, mirroring the ``<!-- lang:NAME -->`` language blocks. The only
per-product variation inside the instruction block is the enabled-language list.

Generation is deterministic and needs no agent judgment: the enabled-language list is read
from the product's ``spx/**/tests/`` test-file extensions, staleness is a dotted-version and
language-set comparison, and the render is a pure string transformation. The parse,
version-compare, language-filter, harness-filter, and render functions take document strings
and return document strings — no filesystem, environment, or subprocess access. The CLI edge
reads the template, globs the test extensions, replaces symlinked root instruction files with
regular files, removes obsolete ``spx/`` instruction files, and writes both root files.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections.abc import Iterable
from collections.abc import Mapping

FRONTMATTER_DELIMITER = "---"
TEMPLATE_VERSION_KEY = "template_version"
TEMPLATE_SOURCE_KEY = "template_source"
LANGUAGES_KEY = "languages"
DEFAULT_TEMPLATE_SOURCE = "spec-tree"
MANAGED_BLOCK_START = "<!-- BEGIN MANAGED SPEC TREE INSTRUCTIONS -->"
MANAGED_BLOCK_END = "<!-- END MANAGED SPEC TREE INSTRUCTIONS -->"
# Legacy marker pair from the retired "guide" naming. Recognized so an existing managed
# block is located and replaced in place on upgrade rather than left behind as prose while
# a second block is appended.
LEGACY_MANAGED_BLOCK_MARKERS = (
    (
        "<!-- BEGIN MANAGED SPEC TREE GUIDE -->",
        "<!-- END MANAGED SPEC TREE GUIDE -->",
    ),
)
MANAGED_TEMPLATE_VERSION_PREFIX = "<!-- spec-tree-template-version:"
MANAGED_TEMPLATE_SOURCE_PREFIX = "<!-- spec-tree-template-source:"
MANAGED_LANGUAGES_PREFIX = "<!-- spec-tree-languages:"

# Each agent harness reads its own instruction filename from the product root.
AGENT_HARNESS_INSTRUCTION_FILENAMES = {"claude": "CLAUDE.md", "codex": "AGENTS.md"}
OBSOLETE_SPX_INSTRUCTION_FILENAMES = ("CLAUDE.md", "AGENTS.md")
OBSOLETE_SPX_DIR_NAME = "spx"
RETIRED_GENERATED_INSTRUCTION_HEADINGS = (
    "# Spec Tree Instructions",
    "# Spec Tree Guide",
    "# spx/ Directory Guide (Spec Tree)",
)


class CliInputError(ValueError):
    """Raised when CLI path input would make instruction-block generation unsafe."""


# Test-file extension -> the language it denotes. The enabled-language set is read from the
# product's own test files, the in-use ground truth, rather than from agent judgment.
LANGUAGE_BY_EXTENSION = {"py": "python", "ts": "typescript", "rs": "rust"}

_BLANK_RUN = re.compile(r"\n{3,}")


def _split_frontmatter(text: str) -> tuple[list[str], str]:
    """Split a document into its frontmatter lines and the remaining body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return [], text
    for index in range(1, len(lines)):
        if lines[index].strip() == FRONTMATTER_DELIMITER:
            return lines[1:index], "\n".join(lines[index + 1 :])
    return [], text


def _unquote(value: str) -> str:
    """Strip exactly one matching pair of surrounding quotes."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _frontmatter_value(frontmatter: list[str], key: str) -> str | None:
    """Return the value of ``key`` from frontmatter lines, or None."""
    prefix = f"{key}:"
    for line in frontmatter:
        stripped = line.strip()
        if stripped.startswith(prefix):
            return _unquote(stripped[len(prefix) :].strip())
    return None


def _frontmatter_block(frontmatter: list[str]) -> str:
    return "\n".join([FRONTMATTER_DELIMITER, *frontmatter, FRONTMATTER_DELIMITER])


def _managed_block_bounds(text: str) -> tuple[int, int] | None:
    """Return the instruction block's start and end offsets when present.

    The canonical markers are tried first, then each retired legacy marker pair, so an
    existing block authored under the old naming is replaced in place on upgrade.
    """
    for start_marker, end_marker in (
        (MANAGED_BLOCK_START, MANAGED_BLOCK_END),
        *LEGACY_MANAGED_BLOCK_MARKERS,
    ):
        start = text.find(start_marker)
        if start == -1:
            continue
        end_marker_start = text.find(end_marker, start + len(start_marker))
        if end_marker_start == -1:
            continue
        end = end_marker_start + len(end_marker)
        if text[end : end + 1] == "\n":
            end += 1
        return start, end
    return None


def _managed_block_text(text: str) -> str | None:
    bounds = _managed_block_bounds(text)
    if bounds is None:
        return None
    start, end = bounds
    return text[start:end]


def _managed_metadata_value(text: str, prefix: str) -> str | None:
    """Return a metadata comment value from inside the instruction block."""
    block = _managed_block_text(text)
    if block is None:
        return None
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix) and stripped.endswith("-->"):
            return stripped[len(prefix) : -len("-->")].strip()
    return None


def _parse_languages(value: str | None) -> tuple[str, ...]:
    """Parse a ``languages`` value (``[a, b]`` or ``a, b``) into a tuple."""
    if not value:
        return ()
    inner = value.strip().removeprefix("[").removesuffix("]")
    return normalize_languages(
        item.strip() for item in inner.split(",") if item.strip()
    )


def normalize_languages(languages: Iterable[str]) -> tuple[str, ...]:
    """Return a canonical enabled-language set for rendering and staleness checks."""
    return tuple(sorted(set(languages)))


def parse_template_version(text: str) -> str | None:
    """Return the ``template_version`` value from a document's frontmatter, or None."""
    frontmatter, _ = _split_frontmatter(text)
    return _frontmatter_value(
        frontmatter, TEMPLATE_VERSION_KEY
    ) or _managed_metadata_value(text, MANAGED_TEMPLATE_VERSION_PREFIX)


def parse_instruction_version(text: str) -> str | None:
    """Return an instruction block's ``template_version`` value, or None."""
    return _managed_metadata_value(text, MANAGED_TEMPLATE_VERSION_PREFIX)


def parse_languages(text: str) -> tuple[str, ...]:
    """Read the recorded enabled-language list from an instruction file's frontmatter."""
    frontmatter, _ = _split_frontmatter(text)
    return _parse_languages(
        _frontmatter_value(frontmatter, LANGUAGES_KEY)
        or _managed_metadata_value(text, MANAGED_LANGUAGES_PREFIX)
    )


def parse_instruction_languages(text: str) -> tuple[str, ...]:
    """Return an instruction block's language list."""
    return _parse_languages(_managed_metadata_value(text, MANAGED_LANGUAGES_PREFIX))


def _version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def is_stale(product_version: str, template_version: str) -> bool:
    """Report whether the product version is numerically below the template version.

    A version that is not dotted-numeric is treated as stale rather than crashing — an
    update then normalizes it to the installed version.
    """
    try:
        return _version_tuple(product_version) < _version_tuple(template_version)
    except ValueError:
        return True


def _conditional_marker(line: str, marker: str, *, closing: bool) -> str | None:
    prefix = f"<!-- {'/' if closing else ''}{marker}:"
    stripped = line.strip()
    if not stripped.startswith(prefix) or not stripped.endswith("-->"):
        return None
    return stripped[len(prefix) : -len("-->")].strip()


def _filter_conditional_blocks(body: str, marker: str, allowed: set[str]) -> str:
    lines = body.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    while index < len(lines):
        name = _conditional_marker(lines[index], marker, closing=False)
        if name is None:
            output.append(lines[index])
            index += 1
            continue

        next_index, block, closed = _conditional_block(lines, index, marker, name)
        if not closed:
            output.extend(block)
            break
        if name in allowed:
            output.extend(_with_trailing_newline(block))
        index = next_index

    return "".join(output)


def _conditional_block(
    lines: list[str], start: int, marker: str, name: str
) -> tuple[int, list[str], bool]:
    """Return the next index, block body, and whether the block closed."""
    block: list[str] = []
    index = start + 1
    while index < len(lines):
        closing_name = _conditional_marker(lines[index], marker, closing=True)
        if closing_name == name:
            return index + 1, block, True
        block.append(lines[index])
        index += 1
    return len(lines), lines[start:], False


def _with_trailing_newline(block: list[str]) -> list[str]:
    """Return a copy of ``block`` that ends with a newline."""
    if block and block[-1].endswith("\n"):
        return block
    return [*block, "\n"]


def _filter_languages(body: str, languages: tuple[str, ...]) -> str:
    """Keep each ``lang:NAME`` block whose NAME is enabled; drop the rest, markers and all."""
    return _filter_conditional_blocks(body, "lang", set(languages))


def _filter_harness(body: str, harness: str) -> str:
    """Keep each ``harness:NAME`` block whose NAME is the target harness; drop the rest."""
    return _filter_conditional_blocks(body, "harness", {harness})


def language_for_extension(extension: str) -> str | None:
    """Map a test-file extension (with or without a leading dot) to its language, or None."""
    return LANGUAGE_BY_EXTENSION.get(extension.lstrip("."))


def detect_languages(extensions: Iterable[str]) -> tuple[str, ...]:
    """Map a set of test-file extensions to the sorted languages they denote.

    Pure: the enabled-language set is the languages the product's own test extensions map
    to, computed without agent judgment or filesystem access. The caller globs the extensions.
    """
    languages = (
        language
        for extension in extensions
        if (language := language_for_extension(extension)) is not None
    )
    return normalize_languages(languages)


def render(
    template_text: str,
    languages: tuple[str, ...],
    installed_version: str,
    harness: str,
) -> str:
    """Render one agent harness's instruction block from the template and enabled languages.

    Language-conditional blocks render only for enabled languages and harness-conditional
    blocks only for ``harness``; nothing else is substituted, so brace-delimited illustration
    tokens pass through unchanged. Metadata comments record the version, source, and language
    list so a later update reads the languages back from any position in a root instruction file.
    """
    languages = normalize_languages(languages)
    template_frontmatter, template_body = _split_frontmatter(template_text)
    source = (
        _frontmatter_value(template_frontmatter, TEMPLATE_SOURCE_KEY)
        or DEFAULT_TEMPLATE_SOURCE
    )

    body = _filter_languages(template_body, languages)
    body = _filter_harness(body, harness)
    body = _BLANK_RUN.sub("\n\n", body)

    metadata = "\n".join(
        [
            MANAGED_BLOCK_START,
            f"{MANAGED_TEMPLATE_VERSION_PREFIX} {installed_version} -->",
            f"{MANAGED_TEMPLATE_SOURCE_PREFIX} {source} -->",
            f"{MANAGED_LANGUAGES_PREFIX} {', '.join(languages)} -->",
            "",
        ]
    )
    rendered = f"{metadata}{body.rstrip()}\n\n{MANAGED_BLOCK_END}"
    return rendered.rstrip("\n") + "\n"


def detect_languages_from_tree(spx_dir: pathlib.Path) -> tuple[str, ...]:
    """CLI-edge helper: glob ``spx/**/tests/`` extensions and map them to languages.

    The filesystem read lives here at the edge, not in the pure render functions.
    """
    extensions = {
        path.suffix.lstrip(".") for path in spx_dir.glob("**/tests/*") if path.is_file()
    }
    return detect_languages(extensions)


def instruction_status(
    instruction_path: pathlib.Path,
    installed_version: str,
    languages: tuple[str, ...],
    containment_root: pathlib.Path | None = None,
) -> str:
    """CLI-edge helper: return ``absent``, ``stale``, or ``current`` for one instruction file.

    The filesystem read lives here at the edge, not in the pure render functions.
    """
    if not instruction_path.is_file():
        return "absent"
    if containment_root is not None:
        _validate_read_target(instruction_path, containment_root)
    text = instruction_path.read_text(encoding="utf-8")
    if _managed_block_text(text) is None:
        return "stale"
    if MANAGED_BLOCK_START not in text:
        # A legacy-marker block is present but not the canonical marker; a re-render
        # migrates it to the current marker.
        return "stale"
    version = parse_instruction_version(text)
    if version is None or is_stale(version, installed_version):
        return "stale"
    if parse_instruction_languages(text) != normalize_languages(languages):
        return "stale"
    return "current"


def upsert_managed_block(document: str, block: str) -> str:
    """Return ``document`` with exactly one managed Spec Tree instruction block."""
    block = block.rstrip("\n") + "\n"
    bounds = _managed_block_bounds(document)
    if bounds is not None:
        start, end = bounds
        updated = f"{document[:start]}{block}{document[end:]}"
        return updated.rstrip("\n") + "\n"
    base = document.rstrip("\n")
    if not base:
        return block
    return f"{base}\n\n{block}"


def _is_markerless_generated_instructions(document: str) -> bool:
    """Report whether ``document`` is the retired generated full-file instruction shape."""
    if _managed_block_text(document) is not None:
        return False
    frontmatter, body = _split_frontmatter(document)
    stripped_body = body.lstrip()
    return (
        _frontmatter_value(frontmatter, TEMPLATE_SOURCE_KEY) == DEFAULT_TEMPLATE_SOURCE
        and _frontmatter_value(frontmatter, TEMPLATE_VERSION_KEY) is not None
        and stripped_body.startswith(RETIRED_GENERATED_INSTRUCTION_HEADINGS)
    )


def _product_owned_root_document(document: str) -> str:
    """Return product-owned root instruction prose, excluding retired generated bodies."""
    if _is_markerless_generated_instructions(document):
        return ""
    return document


def _validated_repo_root(raw_repo_root: str | None) -> pathlib.Path | None:
    """Return a resolved repository root, rejecting missing or non-directory input."""
    if raw_repo_root is None:
        return None
    try:
        repo_root = pathlib.Path(raw_repo_root).expanduser().resolve(strict=True)
    except OSError as exc:
        raise CliInputError(f"--repo-root does not exist: {raw_repo_root}") from exc
    if not repo_root.is_dir():
        raise CliInputError(f"--repo-root is not a directory: {raw_repo_root}")
    return repo_root


def _validated_template_path(raw_template: str) -> pathlib.Path:
    """Return a resolved template path, rejecting a symlink, missing, or non-file input.

    ``--template`` is read from a CLI argument, so the path is validated before the read:
    a faulty or hostile argument that points at a symlink or a non-regular file is rejected
    rather than read, keeping the read from escaping into an unintended file.
    """
    if pathlib.Path(raw_template).is_symlink():
        raise CliInputError(f"--template is a symlink: {raw_template}")
    try:
        template = pathlib.Path(raw_template).expanduser().resolve(strict=True)
    except OSError as exc:
        raise CliInputError(f"--template does not exist: {raw_template}") from exc
    if not template.is_file():
        raise CliInputError(f"--template is not a regular file: {raw_template}")
    return template


def _repo_child(repo_root: pathlib.Path, relative_path: str) -> pathlib.Path:
    """Return a repo child path after validating its parent stays inside root."""
    if pathlib.PurePath(relative_path).is_absolute():
        raise CliInputError(f"repository-relative path is absolute: {relative_path}")
    path = repo_root / relative_path
    try:
        path.parent.resolve(strict=True).relative_to(repo_root)
    except (OSError, ValueError) as exc:
        raise CliInputError(f"path escapes --repo-root: {relative_path}") from exc
    return path


def _validate_read_target(path: pathlib.Path, repo_root: pathlib.Path) -> None:
    """Reject symlink reads that resolve outside the repository root."""
    if not path.is_symlink():
        return
    try:
        path.resolve(strict=True).relative_to(repo_root)
    except (OSError, ValueError) as exc:
        raise CliInputError(f"symlink target escapes --repo-root: {path}") from exc


def _spx_dir(repo_root: pathlib.Path) -> pathlib.Path:
    """Return the repository's spx directory after rejecting unsafe shapes."""
    spx_dir = _repo_child(repo_root, OBSOLETE_SPX_DIR_NAME)
    if spx_dir.is_symlink():
        raise CliInputError(f"spx directory is a symlink: {spx_dir}")
    if spx_dir.exists() and not spx_dir.is_dir():
        raise CliInputError(f"spx path is not a directory: {spx_dir}")
    return spx_dir


def _read_text_if_present(path: pathlib.Path, repo_root: pathlib.Path) -> str | None:
    """Read ``path`` when it exists or is a symlink; otherwise return None."""
    if path.exists() or path.is_symlink():
        _validate_read_target(path, repo_root)
        return path.read_text(encoding="utf-8")
    return None


def _replace_path_with_text(path: pathlib.Path, text: str) -> None:
    """Write ``text`` as a regular file, replacing any file or symlink."""
    if path.exists() or path.is_symlink():
        path.unlink()
    path.write_text(text, encoding="utf-8")


def _root_seed_documents(repo_root: pathlib.Path) -> dict[str, str]:
    """Return root instruction seed text per harness, copying a sole existing file."""
    values = {
        harness: _read_text_if_present(_repo_child(repo_root, filename), repo_root)
        for harness, filename in AGENT_HARNESS_INSTRUCTION_FILENAMES.items()
    }
    fallback = next((text for text in values.values() if text is not None), "")
    return {
        harness: text if text is not None else fallback
        for harness, text in values.items()
    }


def write_root_instruction_files(
    repo_root: pathlib.Path, blocks_by_harness: Mapping[str, str]
) -> None:
    """Insert instruction blocks into root files, replacing symlinks with files."""
    seeds = _root_seed_documents(repo_root)
    for harness, filename in AGENT_HARNESS_INSTRUCTION_FILENAMES.items():
        output = upsert_managed_block(
            _product_owned_root_document(seeds[harness]),
            blocks_by_harness[harness],
        )
        _replace_path_with_text(_repo_child(repo_root, filename), output)


def remove_obsolete_spx_instruction_files(repo_root: pathlib.Path) -> None:
    """Remove retired ``spx/`` instruction files when present."""
    spx_dir = _spx_dir(repo_root)
    if not spx_dir.exists():
        return
    for filename in OBSOLETE_SPX_INSTRUCTION_FILENAMES:
        path = spx_dir / filename
        if path.exists() or path.is_symlink():
            path.unlink()


def main(argv: list[str] | None = None) -> int:
    """Thin CLI edge: read the template, detect languages, render and write both files."""
    parser = argparse.ArgumentParser(
        description="Generate managed Spec Tree instruction blocks in root CLAUDE.md and AGENTS.md."
    )
    parser.add_argument(
        "--template", required=True, help="Path to the canonical template."
    )
    parser.add_argument(
        "--repo-root",
        help="Path to the product repository root holding root instruction files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print staleness status only; emit no content.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write both root instruction files under --repo-root instead of stdout.",
    )
    parser.add_argument(
        "--languages",
        help="Comma-separated enabled languages; detected from spx/**/tests/ extensions when omitted.",
    )
    args = parser.parse_args(argv)

    try:
        template_path = _validated_template_path(args.template)
    except CliInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    template_text = template_path.read_text(encoding="utf-8")
    installed = parse_template_version(template_text)
    if installed is None:
        print("error: template has no template_version", file=sys.stderr)
        return 2

    try:
        repo_root = _validated_repo_root(args.repo_root)
    except CliInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.languages is not None:
        languages = _parse_languages(args.languages)
    elif repo_root is not None:
        try:
            languages = detect_languages_from_tree(_spx_dir(repo_root))
        except CliInputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        languages = ()

    if args.check:
        if repo_root is None:
            print("error: --check requires --repo-root", file=sys.stderr)
            return 2
        try:
            statuses = {
                instruction_status(
                    _repo_child(repo_root, filename),
                    installed,
                    languages,
                    repo_root,
                )
                for filename in AGENT_HARNESS_INSTRUCTION_FILENAMES.values()
            }
        except CliInputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        # Absent dominates stale dominates current: report the worst across both files.
        for verdict in ("absent", "stale", "current"):
            if verdict in statuses:
                print(verdict)
                break
        return 0

    if args.write and repo_root is None:
        print("error: --write requires --repo-root", file=sys.stderr)
        return 2

    rendered = {
        harness: render(template_text, languages, installed, harness)
        for harness in AGENT_HARNESS_INSTRUCTION_FILENAMES
    }

    if args.write and repo_root is not None:
        try:
            write_root_instruction_files(repo_root, rendered)
            remove_obsolete_spx_instruction_files(repo_root)
        except CliInputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        for harness, content in rendered.items():
            sys.stdout.write(
                f"=== {AGENT_HARNESS_INSTRUCTION_FILENAMES[harness]} ===\n{content}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
