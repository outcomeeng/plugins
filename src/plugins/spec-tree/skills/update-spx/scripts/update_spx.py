"""Deterministic generator for a product's root Spec Tree guide sections.

One repository is worked by both Claude Code and Codex at once, and each runtime retains
its root instruction file across compaction: ``CLAUDE.md`` for Claude Code and
``AGENTS.md`` for Codex. The Spec Tree guide is therefore a managed section in those root
files, not generated files under ``spx/``. Both sections render from one canonical template:
the body is shared, and the spans that differ by agent runtime are authored once as
``<!-- runtime:NAME -->`` blocks rendered only into that runtime's section, mirroring the
``<!-- lang:NAME -->`` language blocks. The only per-product variation inside the managed
section is the enabled-language list.

Generation is deterministic and needs no agent judgment: the enabled-language list is read
from the product's ``spx/**/tests/`` test-file extensions, staleness is a dotted-version and
language-set comparison, and the render is a pure string transformation. The parse,
version-compare, language-filter, runtime-filter, and render functions take document strings
and return document strings — no filesystem, environment, or subprocess access. The CLI edge
reads the template, globs the test extensions, replaces symlinked root guides with regular
files, removes obsolete ``spx/`` guide files, and writes both root files.
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
MANAGED_SECTION_START = "<!-- BEGIN MANAGED SPEC TREE GUIDE -->"
MANAGED_SECTION_END = "<!-- END MANAGED SPEC TREE GUIDE -->"
MANAGED_TEMPLATE_VERSION_PREFIX = "<!-- spec-tree-template-version:"
MANAGED_TEMPLATE_SOURCE_PREFIX = "<!-- spec-tree-template-source:"
MANAGED_LANGUAGES_PREFIX = "<!-- spec-tree-languages:"

# Each agent runtime reads its own guide filename from the product root.
RUNTIME_GUIDE_FILENAMES = {"claude": "CLAUDE.md", "codex": "AGENTS.md"}
OBSOLETE_SPX_GUIDE_FILENAMES = ("CLAUDE.md", "AGENTS.md")

# Test-file extension -> the language it denotes. The enabled-language set is read from the
# product's own test files, the in-use ground truth, rather than from agent judgment.
LANGUAGE_BY_EXTENSION = {"py": "python", "ts": "typescript", "rs": "rust"}

_LANG_BLOCK = re.compile(
    r"[ \t]*<!-- lang:(?P<lang>[a-z0-9-]+) -->\n(?P<body>.*?)\n[ \t]*<!-- /lang:(?P=lang) -->\n?",
    re.DOTALL,
)
_RUNTIME_BLOCK = re.compile(
    r"[ \t]*<!-- runtime:(?P<runtime>[a-z0-9-]+) -->\n(?P<body>.*?)\n[ \t]*<!-- /runtime:(?P=runtime) -->\n?",
    re.DOTALL,
)
_BLANK_RUN = re.compile(r"\n{3,}")
_MANAGED_SECTION = re.compile(
    rf"{re.escape(MANAGED_SECTION_START)}\n.*?\n{re.escape(MANAGED_SECTION_END)}\n?",
    re.DOTALL,
)


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


def _managed_metadata_value(text: str, prefix: str) -> str | None:
    """Return a metadata comment value from a managed section."""
    for line in text.splitlines():
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


def parse_languages(text: str) -> tuple[str, ...]:
    """Read the recorded enabled-language list from a guide's frontmatter."""
    frontmatter, _ = _split_frontmatter(text)
    return _parse_languages(
        _frontmatter_value(frontmatter, LANGUAGES_KEY)
        or _managed_metadata_value(text, MANAGED_LANGUAGES_PREFIX)
    )


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


def _filter_languages(body: str, languages: tuple[str, ...]) -> str:
    """Keep each ``lang:NAME`` block whose NAME is enabled; drop the rest, markers and all."""

    def replace(match: re.Match[str]) -> str:
        if match.group("lang") in languages:
            return match.group("body") + "\n"
        return ""

    return _LANG_BLOCK.sub(replace, body)


def _filter_runtime(body: str, runtime: str) -> str:
    """Keep each ``runtime:NAME`` block whose NAME is the target runtime; drop the rest."""

    def replace(match: re.Match[str]) -> str:
        if match.group("runtime") == runtime:
            return match.group("body") + "\n"
        return ""

    return _RUNTIME_BLOCK.sub(replace, body)


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
    runtime: str,
) -> str:
    """Render one runtime's managed section from the template and enabled languages.

    Language-conditional blocks render only for enabled languages and runtime-conditional
    blocks only for ``runtime``; nothing else is substituted, so brace-delimited illustration
    tokens pass through unchanged. Metadata comments record the version, source, and language
    list so a later update reads the languages back from any position in a root guide file.
    """
    languages = normalize_languages(languages)
    template_frontmatter, template_body = _split_frontmatter(template_text)
    source = (
        _frontmatter_value(template_frontmatter, TEMPLATE_SOURCE_KEY)
        or DEFAULT_TEMPLATE_SOURCE
    )

    body = _filter_languages(template_body, languages)
    body = _filter_runtime(body, runtime)
    body = _BLANK_RUN.sub("\n\n", body)

    metadata = "\n".join(
        [
            MANAGED_SECTION_START,
            f"{MANAGED_TEMPLATE_VERSION_PREFIX} {installed_version} -->",
            f"{MANAGED_TEMPLATE_SOURCE_PREFIX} {source} -->",
            f"{MANAGED_LANGUAGES_PREFIX} {', '.join(languages)} -->",
            "",
        ]
    )
    rendered = f"{metadata}{body.rstrip()}\n\n{MANAGED_SECTION_END}"
    return rendered.rstrip("\n") + "\n"


def detect_languages_from_tree(spx_dir: pathlib.Path) -> tuple[str, ...]:
    """CLI-edge helper: glob ``spx/**/tests/`` extensions and map them to languages.

    The filesystem read lives here at the edge, not in the pure render functions.
    """
    extensions = {
        path.suffix.lstrip(".") for path in spx_dir.glob("**/tests/*") if path.is_file()
    }
    return detect_languages(extensions)


def guide_status(
    guide_path: pathlib.Path, installed_version: str, languages: tuple[str, ...]
) -> str:
    """CLI-edge helper: return ``absent``, ``stale``, or ``current`` for one guide file.

    The filesystem read lives here at the edge, not in the pure render functions.
    """
    if not guide_path.is_file():
        return "absent"
    text = guide_path.read_text(encoding="utf-8")
    version = parse_template_version(text)
    if version is None or is_stale(version, installed_version):
        return "stale"
    if parse_languages(text) != normalize_languages(languages):
        return "stale"
    return "current"


def upsert_managed_section(document: str, section: str) -> str:
    """Return ``document`` with exactly one managed Spec Tree guide section."""
    section = section.rstrip("\n") + "\n"
    if _MANAGED_SECTION.search(document):
        updated = _MANAGED_SECTION.sub(section, document, count=1)
        return updated.rstrip("\n") + "\n"
    base = document.rstrip("\n")
    if not base:
        return section
    return f"{base}\n\n{section}"


def _read_text_if_present(path: pathlib.Path) -> str | None:
    """Read ``path`` when it exists or is a symlink; otherwise return None."""
    if path.exists() or path.is_symlink():
        return path.read_text(encoding="utf-8")
    return None


def _replace_path_with_text(path: pathlib.Path, text: str) -> None:
    """Write ``text`` as a regular file, replacing any file or symlink."""
    if path.exists() or path.is_symlink():
        path.unlink()
    path.write_text(text, encoding="utf-8")


def _root_seed_documents(repo_root: pathlib.Path) -> dict[str, str]:
    """Return root guide seed text for each runtime, copying a sole existing guide."""
    values = {
        runtime: _read_text_if_present(repo_root / filename)
        for runtime, filename in RUNTIME_GUIDE_FILENAMES.items()
    }
    fallback = next((text for text in values.values() if text is not None), "")
    return {
        runtime: text if text is not None else fallback
        for runtime, text in values.items()
    }


def write_root_guides(
    repo_root: pathlib.Path, sections_by_runtime: Mapping[str, str]
) -> None:
    """Insert managed sections into root guides, replacing symlinks with files."""
    seeds = _root_seed_documents(repo_root)
    for runtime, filename in RUNTIME_GUIDE_FILENAMES.items():
        output = upsert_managed_section(seeds[runtime], sections_by_runtime[runtime])
        _replace_path_with_text(repo_root / filename, output)


def remove_obsolete_spx_guides(repo_root: pathlib.Path) -> None:
    """Remove retired ``spx/`` guide files when present."""
    spx_dir = repo_root / "spx"
    for filename in OBSOLETE_SPX_GUIDE_FILENAMES:
        path = spx_dir / filename
        if path.exists() or path.is_symlink():
            path.unlink()


def main(argv: list[str] | None = None) -> int:
    """Thin CLI edge: read the template, detect languages, render and write both guides."""
    parser = argparse.ArgumentParser(
        description="Generate managed Spec Tree sections in root CLAUDE.md and AGENTS.md."
    )
    parser.add_argument(
        "--template", required=True, help="Path to the canonical template."
    )
    parser.add_argument(
        "--repo-root",
        help="Path to the product repository root holding root guide files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print staleness status only; emit no content.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write both root guide files under --repo-root instead of stdout.",
    )
    parser.add_argument(
        "--languages",
        help="Comma-separated enabled languages; detected from spx/**/tests/ extensions when omitted.",
    )
    args = parser.parse_args(argv)

    template_text = pathlib.Path(args.template).read_text(encoding="utf-8")
    installed = parse_template_version(template_text)
    if installed is None:
        print("error: template has no template_version", file=sys.stderr)
        return 2

    repo_root = pathlib.Path(args.repo_root) if args.repo_root else None

    if args.languages is not None:
        languages = _parse_languages(args.languages)
    elif repo_root is not None:
        languages = detect_languages_from_tree(repo_root / "spx")
    else:
        languages = ()

    if args.check:
        if repo_root is None:
            print("error: --check requires --repo-root", file=sys.stderr)
            return 2
        statuses = {
            guide_status(repo_root / filename, installed, languages)
            for filename in RUNTIME_GUIDE_FILENAMES.values()
        }
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
        runtime: render(template_text, languages, installed, runtime)
        for runtime in RUNTIME_GUIDE_FILENAMES
    }

    if args.write and repo_root is not None:
        write_root_guides(repo_root, rendered)
        remove_obsolete_spx_guides(repo_root)
    else:
        for runtime, content in rendered.items():
            sys.stdout.write(f"=== {RUNTIME_GUIDE_FILENAMES[runtime]} ===\n{content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
