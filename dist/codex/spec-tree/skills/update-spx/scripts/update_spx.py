"""Deterministic generator for a product's two spx-level guide files.

One repository is worked by both Claude Code and Codex at once, and each reads its own
filename from the same ``spx/`` directory, so the guide is two generated files —
``CLAUDE.md`` for Claude Code and ``AGENTS.md`` for Codex. Both render from one canonical
template: the body is shared, and the spans that differ by agent runtime are authored once
as ``<!-- runtime:NAME -->`` blocks rendered only into that runtime's file, mirroring the
``<!-- lang:NAME -->`` language blocks. The only per-product variation is the
enabled-language list (see the node's Guide Render Model ADR).

Generation is deterministic and needs no agent judgment: the enabled-language list is read
from the product's ``spx/**/tests/`` test-file extensions, staleness is a dotted-version and
language-set comparison, and the render is a pure string transformation. The parse,
version-compare, language-filter, runtime-filter, and render functions take document strings
and return document strings — no filesystem, environment, or subprocess access. The CLI edge
reads the template, globs the test extensions, and writes both files.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from collections.abc import Iterable

FRONTMATTER_DELIMITER = "---"
TEMPLATE_VERSION_KEY = "template_version"
TEMPLATE_SOURCE_KEY = "template_source"
LANGUAGES_KEY = "languages"
DEFAULT_TEMPLATE_SOURCE = "spec-tree"

# Each agent runtime reads its own guide filename from the product's spx/ directory.
RUNTIME_GUIDE_FILENAMES = {"claude": "CLAUDE.md", "codex": "AGENTS.md"}

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


def _parse_languages(value: str | None) -> tuple[str, ...]:
    """Parse a ``languages`` value (``[a, b]`` or ``a, b``) into a tuple."""
    if not value:
        return ()
    inner = value.strip().removeprefix("[").removesuffix("]")
    return tuple(item.strip() for item in inner.split(",") if item.strip())


def parse_template_version(text: str) -> str | None:
    """Return the ``template_version`` value from a document's frontmatter, or None."""
    frontmatter, _ = _split_frontmatter(text)
    return _frontmatter_value(frontmatter, TEMPLATE_VERSION_KEY)


def parse_languages(text: str) -> tuple[str, ...]:
    """Read the recorded enabled-language list from a guide's frontmatter."""
    frontmatter, _ = _split_frontmatter(text)
    return _parse_languages(_frontmatter_value(frontmatter, LANGUAGES_KEY))


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
    languages = {
        language
        for extension in extensions
        if (language := language_for_extension(extension)) is not None
    }
    return tuple(sorted(languages))


def render(
    template_text: str,
    languages: tuple[str, ...],
    installed_version: str,
    runtime: str,
) -> str:
    """Render one runtime's guide from the template and the enabled-language list.

    Language-conditional blocks render only for enabled languages and runtime-conditional
    blocks only for ``runtime``; nothing else is substituted, so brace-delimited illustration
    tokens pass through unchanged. The output frontmatter records the version, source, and
    language list so a later update reads the languages back.
    """
    template_frontmatter, template_body = _split_frontmatter(template_text)
    source = (
        _frontmatter_value(template_frontmatter, TEMPLATE_SOURCE_KEY)
        or DEFAULT_TEMPLATE_SOURCE
    )

    body = _filter_languages(template_body, languages)
    body = _filter_runtime(body, runtime)
    body = _BLANK_RUN.sub("\n\n", body)

    out_frontmatter = [
        f'{TEMPLATE_VERSION_KEY}: "{installed_version}"',
        f"{TEMPLATE_SOURCE_KEY}: {source}",
        f"{LANGUAGES_KEY}: [{', '.join(languages)}]",
    ]
    # `_split_frontmatter` uses `str.splitlines()`, which drops the template's trailing
    # newline; normalize so the output always ends with exactly one.
    rendered = f"{_frontmatter_block(out_frontmatter)}\n{body}"
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
    if parse_languages(text) != languages:
        return "stale"
    return "current"


def main(argv: list[str] | None = None) -> int:
    """Thin CLI edge: read the template, detect languages, render and write both guide files."""
    parser = argparse.ArgumentParser(
        description="Generate a product's spx/CLAUDE.md and spx/AGENTS.md from the template."
    )
    parser.add_argument(
        "--template", required=True, help="Path to the canonical template."
    )
    parser.add_argument(
        "--spx-dir",
        help="Path to the product's spx/ directory holding both guide files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print staleness status only; emit no content.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write both guide files under --spx-dir instead of stdout.",
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

    spx_dir = pathlib.Path(args.spx_dir) if args.spx_dir else None

    if args.languages is not None:
        languages = _parse_languages(args.languages)
    elif spx_dir is not None:
        languages = detect_languages_from_tree(spx_dir)
    else:
        languages = ()

    if args.check:
        if spx_dir is None:
            print("error: --check requires --spx-dir", file=sys.stderr)
            return 2
        statuses = {
            guide_status(spx_dir / filename, installed, languages)
            for filename in RUNTIME_GUIDE_FILENAMES.values()
        }
        # Absent dominates stale dominates current: report the worst across both files.
        for verdict in ("absent", "stale", "current"):
            if verdict in statuses:
                print(verdict)
                break
        return 0

    if args.write and spx_dir is None:
        print("error: --write requires --spx-dir", file=sys.stderr)
        return 2

    rendered = {
        filename: render(template_text, languages, installed, runtime)
        for runtime, filename in RUNTIME_GUIDE_FILENAMES.items()
    }

    if args.write and spx_dir is not None:
        for filename, content in rendered.items():
            (spx_dir / filename).write_text(content, encoding="utf-8")
    else:
        for filename, content in rendered.items():
            sys.stdout.write(f"=== {filename} ===\n{content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
