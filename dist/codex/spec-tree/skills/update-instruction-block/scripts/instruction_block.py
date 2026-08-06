"""Deterministic generation and validation of a product's root Spec Tree instruction surface.

One repository is worked by both Claude Code and Codex at once, and each agent harness retains
its root instruction file across compaction: ``CLAUDE.md`` for Claude Code and ``AGENTS.md`` for
Codex. The Spec Tree instructions are therefore a managed surface in those root files, not
generated files under ``spx/``. Each root file is three content kinds:

- A generated **router block**, always first, delimited by a single opening marker
  ``<!-- SPEC-TREE v{version} langs:{list} -->`` and a closing ``<!-- /SPEC-TREE -->``. Both
  router blocks render from one canonical template: the body is shared, and the spans that
  differ by agent harness are authored once as ``<!-- harness:NAME -->`` blocks rendered only
  into that harness's block, mirroring the ``<!-- lang:NAME -->`` language blocks. The router
  carries the product-neutral routing and an instruction to read the whole file, so a product's
  own commands are content the agent reads, not data the router resolves.
- **`shared` regions**, delimited by ``<!-- SPEC-TREE:shared {name} -->`` and
  ``<!-- /SPEC-TREE:shared {name} -->``, present in both root files under the same name and kept
  byte-identical. A diverged region is reconciled by whole-side replacement: the more-recently
  committed file's body is written whole into the other. The reconcile never merges the two
  bodies, so it stays a total function reducible to a hook.
- **Independent content**, everything outside the router block and every shared region, free to
  differ per file and preserved verbatim.

The render, staleness, language-filter, harness-filter, shared-region-parse, biggest-identical-
span, and bootstrap functions take document strings and return document strings — no filesystem,
git, environment, or subprocess access. The CLI edge reads the template, globs the test
extensions, replaces symlinked root instruction files with regular files, removes obsolete
``spx/`` instruction files, reads committed git state for the recency reconcile, and writes both
root files.

Tested with: a stale router below the installed version; a router whose recorded languages differ
from the detected set; a retired marker block and a markerless generated body; an absent surface;
a surface already current; the initial topologies (one file present, a symlinked file, a
delegating file, mutual delegation, two identical files, two near-identical files above and below
the 80% span threshold, two independent files); delegation candidacy on both sides of each fact it
reads (a body naming the other root file within the bound, exactly at it, and one character past
it, and a body naming no other root file); a write that carries no operator answer, one that
carries ``--adopt``, one whose ``--adopt`` names a pointer body and is refused, one whose
``--adopt`` would discard a content-bearing body and is refused, one whose ``--adopt`` arrives
after the bootstrap pass has closed and is refused, and an ``--adopt`` with no ``--write`` to
apply it; a reconcile reporting a pointer body; every section gated on language presence, rendered with no
language enabled and with each non-empty subset of the declared languages; a diverged, one-sided, duplicated, and unclosed shared region; a recency tie
and an operator tie break; a dirty root file; and the CLI rejections (missing or non-directory repo root, missing or directory template, a
template without ``template_version``, a symlink escaping the repository, an unsupported language
token, a duplicate flag). The executable cases live in the governing node's ``tests/`` directory.

"""

from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import subprocess
import sys
from collections.abc import Iterable
from collections.abc import Mapping
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

FRONTMATTER_DELIMITER = "---"
TEMPLATE_VERSION_KEY = "template_version"
# The stable prefix of the missing-version failure; the CLI appends the offending template path
# and the remedy, so a caller matching on the prefix stays coupled to the condition, not the
# advice.
MISSING_TEMPLATE_VERSION_ERROR = "error: template has no template_version"
DUPLICATE_FLAG_ERROR_PREFIX = "error: duplicate flag: "
TEMPLATE_SOURCE_KEY = "template_source"
LANGUAGES_KEY = "languages"
DEFAULT_TEMPLATE_SOURCE = "spec-tree"
READ_ENTIRE_FILE_DIRECTIVE = "**Read this entire file before acting.**"
CLI_OPTION_NAMES = (
    "--template",
    "--repo-root",
    "--check",
    "--write",
    "--reconcile",
    "--from",
    "--adopt",
    "--languages",
)
UNRESOLVED_BUILD_TEMPLATE_TOKENS = (
    "{" + "{!",
    "!" + "}}",
    "{" + "!%",
    "%" + "!}",
    "{" + "!#",
    "#" + "!}",
)

# The router block's compressed marker. The opening marker carries the two fields staleness
# reads — the dotted template version and the recorded enabled-language list — inline, so no
# separate metadata comment lines are written. The template source is always the methodology's
# own, so it is not recorded.
ROUTER_MARKER_PREFIX = "<!-- SPEC-TREE v"
ROUTER_BLOCK_END = "<!-- /SPEC-TREE -->"
ROUTER_LANGS_KEY = "langs:"
ROUTER_BODY_SEPARATOR = "\n\n"
# The conditional marker gating a section that introduces per-language content but carries no
# per-language block itself. Named apart from the per-language `lang` marker so its value is
# never mistaken for a language name by the template's declared-language scan.
LANGUAGE_PRESENCE_MARKER = "langs"
LANGUAGE_PRESENCE_NAME = "present"
# Anchored to a full fence line (``re.MULTILINE``) so an inline marker example in product prose
# never opens the block: the shipped instruction block teaches the literal marker, so a consumer
# may quote it in prose, and an unanchored match would replace from that quote through the real
# closing fence and corrupt the document.
_ROUTER_MARKER_RE = re.compile(
    r"^<!--\s*SPEC-TREE\s+v(?P<version>\S+)\s+langs:(?P<langs>\S*)\s*-->\s*$",
    re.MULTILINE,
)

# Retired marker pairs. A managed surface delimited by one of these is generated content from a
# superseded naming; it is located and replaced in place on upgrade rather than left behind as
# prose while a new router block is inserted. The two prior forms are the four-line
# ``BEGIN/END MANAGED SPEC TREE INSTRUCTIONS`` header and the older ``... GUIDE`` header.
LEGACY_MANAGED_BLOCK_MARKERS = (
    (
        "<!-- BEGIN MANAGED SPEC TREE INSTRUCTIONS -->",
        "<!-- END MANAGED SPEC TREE INSTRUCTIONS -->",
    ),
    (
        "<!-- BEGIN MANAGED SPEC TREE GUIDE -->",
        "<!-- END MANAGED SPEC TREE GUIDE -->",
    ),
)
# Metadata comment lines a retired header records inside its block; the version and languages
# prefixes are recognized so a legacy block's version and language set are read back before it
# is replaced.
MANAGED_TEMPLATE_VERSION_PREFIX = "<!-- spec-tree-template-version:"
MANAGED_TEMPLATE_SOURCE_PREFIX = "<!-- spec-tree-template-source:"
MANAGED_LANGUAGES_PREFIX = "<!-- spec-tree-languages:"

# The `shared` region marker namespace. A shared region is present in both root files under the
# same name with byte-identical bodies; the reconcile keeps them identical by whole-side
# replacement. A `<!-- SPEC-TREE:shared {name} -->` fence on its own line opens a region; a quote
# of the marker inside prose does not, because matching is anchored to a standalone fence line.
SHARED_MARKER_NAME = "SPEC-TREE:shared"
_SHARED_OPEN_RE = re.compile(
    r"^<!--\s*SPEC-TREE:shared\s+(?P<name>\S+)\s*-->\s*$",
    re.MULTILINE,
)
# The default region name the bootstrap pass assigns to its single wrapped span.
BOOTSTRAP_SHARED_REGION_NAME = "root"
# The bootstrap pass wraps one shared region only when the biggest contiguous identical span
# covers more than this fraction of the larger file.
BOOTSTRAP_SHARED_THRESHOLD = 0.8
# A root instruction file that only points at the other one is absolutely small — a title and a
# sentence or two — however large the file it points at. The bound is therefore a character count,
# not a ratio: measured against the other file, a 400-line body would read as a stub whenever the
# body opposite it ran to 4000 lines. The bound only decides when to ask the operator, never what
# the answer is, so it is set well above a real stub rather than tuned to exclude borderline
# bodies; a body that clears it costs one question, never its content.
DELEGATION_STUB_MAX_CHARACTERS = 500

# Each agent harness reads its own instruction filename from the product root.
AGENT_HARNESS_INSTRUCTION_FILENAMES = {"claude": "CLAUDE.md", "codex": "AGENTS.md"}
OBSOLETE_SPX_INSTRUCTION_FILENAMES = ("CLAUDE.md", "AGENTS.md")
OBSOLETE_SPX_DIR_NAME = "spx"
RETIRED_GENERATED_INSTRUCTION_HEADINGS = (
    "# Spec Tree Instructions",
    "# Spec Tree Guide",
    "# spx/ Directory Guide (Spec Tree)",
)


class InstructionStatus(StrEnum):
    """Status reported for a product's managed instruction surface."""

    ABSENT = "absent"
    STALE = "stale"
    CURRENT = "current"


INSTRUCTION_STATUS_PRECEDENCE = (
    InstructionStatus.ABSENT,
    InstructionStatus.STALE,
    InstructionStatus.CURRENT,
)


class CliInputError(ValueError):
    """Raised when CLI path input would make instruction-block generation unsafe."""


class UnresolvedInstructionTemplateError(ValueError):
    """Raised when instruction generation receives an authored build template."""


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


def router_marker(version: str, languages: tuple[str, ...]) -> str:
    """Build the router block's opening marker from the version and enabled languages.

    The single source of the ``<!-- SPEC-TREE v{version} langs:{list} -->`` marker format, so a
    consumer or test references it here rather than copying the literal.
    """
    return (
        f"{ROUTER_MARKER_PREFIX}{version} {ROUTER_LANGS_KEY}{','.join(languages)} -->"
    )


def _router_marker_match(text: str) -> re.Match[str] | None:
    """Return the router block's opening-marker match, or None."""
    return _ROUTER_MARKER_RE.search(text)


def _legacy_block_bounds(text: str) -> tuple[int, int] | None:
    """Return a retired marker pair's start and end offsets when present.

    Both markers are matched only where they stand alone on their own line, so a marker quoted
    inline in product prose is never taken for a real fence — the same standalone-line rule the
    router and shared-region fences use.
    """
    for start_marker, end_marker in LEGACY_MANAGED_BLOCK_MARKERS:
        start = _find_fence_line(text, start_marker)
        if start == -1:
            continue
        end_marker_start = _find_fence_line(text, end_marker, start + len(start_marker))
        if end_marker_start == -1:
            continue
        end = end_marker_start + len(end_marker)
        if text[end : end + 1] == "\n":
            end += 1
        return start, end
    return None


def router_block_bounds(text: str) -> tuple[int, int] | None:
    """Return the current router block's start and end offsets when present.

    The closing marker is matched only where it stands alone on its own line, matching the
    line-anchored opening marker: a `<!-- /SPEC-TREE -->` quoted inline in the router body or the
    product prose after it is never taken for the real closing fence.
    """
    match = _router_marker_match(text)
    if match is None:
        return None
    start = match.start()
    end_marker_start = _find_fence_line(text, ROUTER_BLOCK_END, match.end())
    if end_marker_start == -1:
        return None
    end = end_marker_start + len(ROUTER_BLOCK_END)
    if text[end : end + 1] == "\n":
        end += 1
    return start, end


def _managed_block_bounds(text: str) -> tuple[int, int] | None:
    """Return the managed router block's start and end offsets when present.

    The current compressed marker is tried first, then each retired marker pair, so an existing
    block authored under a superseded naming is replaced in place on upgrade.
    """
    return router_block_bounds(text) or _legacy_block_bounds(text)


def _managed_block_text(text: str) -> str | None:
    bounds = _managed_block_bounds(text)
    if bounds is None:
        return None
    start, end = bounds
    return text[start:end]


def _managed_metadata_value(text: str, prefix: str) -> str | None:
    """Return a metadata comment value from inside a retired managed block."""
    block = _managed_block_text(text)
    if block is None:
        return None
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix) and stripped.endswith("-->"):
            return stripped[len(prefix) : -len("-->")].strip()
    return None


def _parse_languages(value: str | None) -> tuple[str, ...]:
    """Parse a ``languages`` value (``[a, b]``, ``a, b``, or ``a,b``) into a tuple."""
    if not value:
        return ()
    stripped = value.strip()
    inner = (
        stripped[1:-1]
        if stripped.startswith("[") and stripped.endswith("]")
        else stripped
    )
    return normalize_languages(
        item.strip() for item in inner.split(",") if item.strip()
    )


def normalize_languages(languages: Iterable[str]) -> tuple[str, ...]:
    """Return a canonical enabled-language set for rendering and staleness checks."""
    return tuple(sorted(set(languages)))


def duplicate_cli_option(argv: Iterable[str]) -> str | None:
    """Return the first repeated supported option in raw argv, or None."""
    seen: set[str] = set()
    for token in argv:
        option = token.split("=", maxsplit=1)[0]
        if option not in CLI_OPTION_NAMES:
            continue
        if option in seen:
            return option
        seen.add(option)
    return None


def parse_template_frontmatter_version(text: str) -> str | None:
    """Return the ``template_version`` value from frontmatter only, or None."""
    frontmatter, _ = _split_frontmatter(text)
    return _frontmatter_value(frontmatter, TEMPLATE_VERSION_KEY)


def parse_template_version(text: str) -> str | None:
    """Return a template or rendered instruction document's version, or None."""
    return parse_template_frontmatter_version(text) or parse_instruction_version(text)


def parse_instruction_version(text: str) -> str | None:
    """Return a managed block's ``template_version``, from the router marker or legacy metadata."""
    match = _router_marker_match(text)
    if match is not None:
        return match.group("version")
    return _managed_metadata_value(text, MANAGED_TEMPLATE_VERSION_PREFIX)


def parse_languages(text: str) -> tuple[str, ...]:
    """Read the recorded enabled-language list from an instruction file's frontmatter or block."""
    frontmatter, _ = _split_frontmatter(text)
    frontmatter_value = _frontmatter_value(frontmatter, LANGUAGES_KEY)
    if frontmatter_value is not None:
        return _parse_languages(frontmatter_value)
    return parse_instruction_languages(text)


def parse_instruction_languages(text: str) -> tuple[str, ...]:
    """Return a managed block's language list, from the router marker or legacy metadata."""
    match = _router_marker_match(text)
    if match is not None:
        return _parse_languages(match.group("langs"))
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


def _filter_language_presence(body: str, languages: tuple[str, ...]) -> str:
    """Keep each ``langs:present`` block when any language is enabled; drop it when none is.

    A section that introduces per-language content carries no per-language block of its own, so
    with no language enabled it would render as a heading and a preamble promising tables that
    the same render just dropped. Wrapping that surrounding text in ``langs:present`` removes
    the whole section instead of leaving it dangling. The marker is ``langs``, distinct from the
    per-language ``lang`` marker, so it never reads as a language name.
    """
    return _filter_conditional_blocks(
        body,
        LANGUAGE_PRESENCE_MARKER,
        {LANGUAGE_PRESENCE_NAME} if languages else set(),
    )


def template_languages(template_text: str) -> tuple[str, ...]:
    """Return the languages declared by opening ``lang:NAME`` template markers."""
    _, body = _split_frontmatter(template_text)
    return normalize_languages(
        name
        for line in body.splitlines()
        if (name := _conditional_marker(line, "lang", closing=False)) is not None
    )


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


def assert_no_unresolved_build_macros(template_text: str) -> None:
    """Reject a template that still contains build-time macro delimiters."""
    for token in UNRESOLVED_BUILD_TEMPLATE_TOKENS:
        if token in template_text:
            raise UnresolvedInstructionTemplateError(
                f"template contains unresolved build macro token {token!r}; "
                "pass the rendered, delimiter-free template bundled with the installed plugin"
            )


def render(
    template_text: str,
    languages: tuple[str, ...],
    installed_version: str,
    harness: str,
) -> str:
    """Render one agent harness's router block from the template and enabled languages.

    Language-conditional blocks render only for enabled languages and harness-conditional
    blocks only for ``harness``; a ``langs:present`` block, wrapping text that introduces
    per-language content while carrying none of its own, is dropped whole when no language is
    enabled. Nothing else is substituted, so brace-delimited illustration
    tokens pass through unchanged. The opening marker records the version and language list
    inline, so a later update reads both back from the marker without separate metadata lines.
    """
    assert_no_unresolved_build_macros(template_text)
    languages = normalize_languages(languages)
    _, template_body = _split_frontmatter(template_text)

    body = _filter_language_presence(template_body, languages)
    body = _filter_languages(body, languages)
    body = _filter_harness(body, harness)
    body = _BLANK_RUN.sub("\n\n", body)
    body = body.lstrip("\n")

    marker = router_marker(installed_version, languages)
    rendered = (
        f"{marker}{ROUTER_BODY_SEPARATOR}{body.rstrip()}"
        f"{ROUTER_BODY_SEPARATOR}{ROUTER_BLOCK_END}"
    )
    return rendered.rstrip("\n") + "\n"


# --- Shared regions ------------------------------------------------------------------------


def shared_open_marker(name: str) -> str:
    """The opening fence marker delimiting a shared region's body."""
    return f"<!-- {SHARED_MARKER_NAME} {name} -->"


def shared_close_marker(name: str) -> str:
    """The closing fence marker delimiting a shared region's body."""
    return f"<!-- /{SHARED_MARKER_NAME} {name} -->"


def _find_fence_line(text: str, marker: str, start: int = 0) -> int:
    """Return the offset of ``marker`` where it stands alone on its own line, or -1.

    A fence marker in the managed surface occupies a whole line; a copy of the marker quoted
    inside product prose does not. Matching only a standalone-line occurrence keeps such a quoted
    marker from being taken for a real fence.
    """
    index = text.find(marker, start)
    while index != -1:
        at_line_start = index == 0 or text[index - 1] == "\n"
        line_end = index + len(marker)
        at_line_end = line_end == len(text) or text[line_end] == "\n"
        if at_line_start and at_line_end:
            return index
        index = text.find(marker, index + 1)
    return -1


def parse_shared_regions(text: str) -> dict[str, str]:
    """Return each shared region's body keyed by name.

    Only a ``<!-- SPEC-TREE:shared {name} -->`` open fence standing alone on its line, closed by
    the matching ``<!-- /SPEC-TREE:shared {name} -->`` fence, is a region; an open fence with no
    matching close is skipped rather than treated as an open-ended region — a malformed fence is
    an ambiguous case the update skill reconciles, not one the generator repairs.
    """
    regions: dict[str, str] = {}
    for match in _SHARED_OPEN_RE.finditer(text):
        name = match.group("name")
        body_start = match.end()
        close = _find_fence_line(text, shared_close_marker(name), body_start)
        if close == -1:
            continue
        regions[name] = text[body_start:close].strip("\n")
    return regions


def malformed_shared_regions(text: str) -> tuple[str, ...]:
    """Return the names of malformed shared open fences.

    A fence is malformed when its open marker has no matching standalone-line closing fence, or
    when the same name is opened more than once. ``parse_shared_regions`` skips an unclosed open
    fence and lets a duplicated name silently overwrite the earlier body — either way a region is
    lost or collapsed — so this reports those names so the drift gate and ``--check`` surface the
    malformed fence as an ambiguous case for the update skill rather than leaving it silently in
    the instruction surface.
    """
    malformed: list[str] = []
    seen: set[str] = set()
    for match in _SHARED_OPEN_RE.finditer(text):
        name = match.group("name")
        if name in seen:
            malformed.append(
                name
            )  # a second open fence for one name collapses in the parse
            continue
        seen.add(name)
        if _find_fence_line(text, shared_close_marker(name), match.end()) == -1:
            malformed.append(name)
    return tuple(sorted(set(malformed)))


def set_shared_region(text: str, name: str, body: str) -> str:
    """Return ``text`` with the named shared region's body replaced; unchanged when absent."""
    open_marker, close_marker = shared_open_marker(name), shared_close_marker(name)
    start = _find_fence_line(text, open_marker)
    if start == -1:
        return text
    body_start = start + len(open_marker)
    end = _find_fence_line(text, close_marker, body_start)
    if end == -1:
        return text
    # Blank lines around the body keep the fence dprint-compliant: an HTML comment and the
    # Markdown that follows it are separate blocks, so the formatter requires a blank between.
    return f"{text[:body_start]}\n\n{body}\n\n{text[end:]}"


def diverged_shared_regions(text_a: str, text_b: str) -> tuple[str, ...]:
    """Return the shared regions present in both texts whose bodies differ, byte for byte."""
    regions_a = parse_shared_regions(text_a)
    regions_b = parse_shared_regions(text_b)
    return tuple(
        name
        for name in sorted(regions_a.keys() & regions_b.keys())
        if regions_a[name] != regions_b[name]
    )


def one_sided_shared_regions(text_a: str, text_b: str) -> tuple[str, ...]:
    """Return the shared-region names present in exactly one of the two texts."""
    regions_a = set(parse_shared_regions(text_a))
    regions_b = set(parse_shared_regions(text_b))
    return tuple(sorted(regions_a ^ regions_b))


def reconcile_shared_regions(
    text_a: str, text_b: str, winner: str | None
) -> tuple[str, str]:
    """Return the two texts with each diverged shared region set to the winner's body.

    ``winner`` is ``"a"`` or ``"b"``; ``None`` is a recency tie, an ambiguous case left for the
    update skill, so the texts are returned unchanged. A one-sided region is also left unchanged —
    reconciliation replaces a diverged body wholesale, never invents a region in the file that
    lacks it.
    """
    if winner is None:
        return text_a, text_b
    diverged = diverged_shared_regions(text_a, text_b)
    if not diverged:
        return text_a, text_b
    source_regions = parse_shared_regions(text_a if winner == "a" else text_b)
    for name in diverged:
        body = source_regions[name]
        if winner == "a":
            text_b = set_shared_region(text_b, name, body)
        else:
            text_a = set_shared_region(text_a, name, body)
    return text_a, text_b


# --- Biggest-identical-span bootstrap ------------------------------------------------------


def _is_line_boundary(text: str, pos: int) -> bool:
    """Report whether ``pos`` sits at a line boundary — file start, file end, or after a newline."""
    return pos == 0 or pos == len(text) or text[pos - 1] == "\n"


def _snap_match_to_both_lines(
    text_a: str, text_b: str, a0: int, b0: int, size: int
) -> tuple[int, int, int, int] | None:
    """Snap a common match to the sub-span that is whole lines in *both* texts, or None.

    The match content is identical in both texts, so its internal newlines sit at the same
    relative offsets in each; only the two edges can be mid-line, and independently per file — one
    text may carry a harness-specific prefix on the shared line, so an edge that is a line boundary
    in one is mid-line in the other. The start advances past the first internal newline unless both
    edges already fall on a line boundary, and the end retreats to the last internal newline unless
    both edges already do, so the wrapped region never splits a line in either file.
    """
    content = text_a[a0 : a0 + size]
    start_rel = 0
    if not (_is_line_boundary(text_a, a0) and _is_line_boundary(text_b, b0)):
        newline = content.find("\n")
        if newline == -1:
            return None
        start_rel = newline + 1
    end_rel = size
    if not (
        _is_line_boundary(text_a, a0 + size) and _is_line_boundary(text_b, b0 + size)
    ):
        newline = content.rfind("\n", start_rel)
        if newline == -1:
            return None
        end_rel = newline + 1
    if end_rel <= start_rel:
        return None
    return (a0 + start_rel, a0 + end_rel, b0 + start_rel, b0 + end_rel)


def _longest_identical_line_span(text_a: str, text_b: str) -> tuple[int, int, int, int]:
    """Return whole-line offsets of the biggest span identical to both texts.

    ``(a_start, a_end, b_start, b_end)`` bound the same content in each text, snapped inward to
    line boundaries in *both* texts so a wrap never splits a line: a ``difflib`` match is a
    byte-level common substring that can begin or end mid-line — independently in each file, since
    one file may carry a harness-specific prefix on the shared line — and wrapping there would
    break a word across the shared-region boundary and alter the independent content the model
    preserves. Every matching block is snapped and the largest post-snap span wins, not just the
    single byte-longest match, which can be a very long near-duplicate line that snaps away to
    nothing while a shorter but whole-line-aligned block elsewhere is the real biggest shared span.
    An empty span (no whole line in common) returns all zeros.
    """
    matcher = difflib.SequenceMatcher(None, text_a, text_b, autojunk=False)
    best: tuple[int, int, int, int] = (0, 0, 0, 0)
    best_length = 0
    for match in matcher.get_matching_blocks():
        if match.size == 0:
            continue
        snapped = _snap_match_to_both_lines(
            text_a, text_b, match.a, match.b, match.size
        )
        if snapped is None:
            continue
        length = snapped[1] - snapped[0]
        if length > best_length:
            best = snapped
            best_length = length
    return best


def biggest_identical_span(text_a: str, text_b: str) -> tuple[str, float]:
    """Return the biggest whole-line span identical to both texts and its ratio.

    The ratio is the snapped span's length over the larger text's length, so a one-sided addition
    cannot inflate it. Pure: the span is snapped to line boundaries, so it never splits a line.
    """
    a_start, a_end, _, _ = _longest_identical_line_span(text_a, text_b)
    span = text_a[a_start:a_end]
    larger = max(len(text_a), len(text_b))
    ratio = (a_end - a_start) / larger if larger else 0.0
    return span, ratio


def _wrap_shared_at(text: str, start: int, end: int, name: str) -> str:
    """Wrap the whole-line span ``text[start:end]`` as a named shared region.

    ``start`` and ``end`` are line boundaries, so the divergent independent content before and
    after the span keeps its own whole lines — no line is split across the fence. The three
    segments rejoin with the blank-line separators the formatter keeps.
    """
    open_marker, close_marker = shared_open_marker(name), shared_close_marker(name)
    before = text[:start].strip("\n")
    body = text[start:end].strip("\n")
    after = text[end:].strip("\n")
    fenced = f"{open_marker}\n\n{body}\n\n{close_marker}"
    return "\n\n".join(part for part in (before, fenced, after) if part) + "\n"


def is_delegation_candidate(body: str, other_filename: str) -> bool:
    """Report whether ``body`` is small enough to be nothing but a pointer at ``other_filename``.

    Two facts about the file decide this, and neither is a reading of its prose: the body names
    the other root instruction file, and its text stays under
    :data:`DELEGATION_STUB_MAX_CHARACTERS`. Whether a sentence naming the other file *also*
    carries an instruction of its own is a question about English, not about the file, and no
    pattern over the text answers it — "see the other file for commands and run the migration
    first" and "see the other file for commands, packages, and conventions" differ by meaning
    alone. Adoption replaces the whole body, so guessing wrong costs the file its instructions.
    This therefore reports a *candidate* the operator resolves, never a verdict.
    Pure: two strings in, a bool out.
    """
    # Naming the other file already implies a non-empty body, so the size bound is the only
    # further condition.
    return (
        other_filename in body and len(body.strip()) <= DELEGATION_STUB_MAX_CHARACTERS
    )


def delegation_candidates(bodies_by_harness: Mapping[str, str]) -> tuple[str, ...]:
    """Return the harnesses whose body may be a pointer at the other root instruction file.

    Both sides can qualify: two stubs naming each other carry no content for either to adopt, and
    the operator resolves that standoff by writing a body rather than choosing a side. Pure: a
    mapping of bodies in, harness names out.
    """
    candidates = []
    for harness, body in sorted(bodies_by_harness.items()):
        others = [name for name in bodies_by_harness if name != harness]
        if any(
            is_delegation_candidate(body, AGENT_HARNESS_INSTRUCTION_FILENAMES[other])
            for other in others
        ):
            candidates.append(harness)
    return tuple(candidates)


def is_first_encounter(body_claude: str, body_codex: str) -> bool:
    """Report whether the bootstrap pass may still arrange these two bodies.

    A surface is a first encounter while neither body carries a valid shared region and neither
    carries a malformed fence. A malformed fence (an open marker with no matching close, or a
    duplicated name) makes ``parse_shared_regions`` read the body as region-free, so a bootstrap
    would wrap the dangling marker verbatim into a new region and bury it in a permanently stuck
    stale state; an ambiguous seed is refused rather than guessed at, and ``--check`` and the drift
    gate surface it as stale instead.

    Every step that only a first encounter may take reads this one function, so the reported
    remedy and the write that applies it can never disagree about whether the pass is open.
    Pure: two strings in, a bool out.
    """
    return not any(
        malformed_shared_regions(body) or parse_shared_regions(body)
        for body in (body_claude, body_codex)
    )


def adopt_delegated_body(
    bodies_by_harness: Mapping[str, str], adopt_harness: str
) -> dict[str, str]:
    """Give every harness the body of ``adopt_harness``, the side the operator kept.

    An answer is only meaningful where a body was reported as a pointer, so both sides are
    checked. The named side must not be a pointer, or adoption installs a body sending the
    reader to a file carrying that same pointer. Every other side must *be* one, because
    adoption discards it: overwriting a body that states something of its own destroys
    instructions no report ever offered up. Pure: bodies and a harness name in, bodies out.
    """
    kept = bodies_by_harness[adopt_harness]
    others = [name for name in bodies_by_harness if name != adopt_harness]
    if any(
        is_delegation_candidate(kept, AGENT_HARNESS_INSTRUCTION_FILENAMES[other])
        for other in others
    ):
        raise CliInputError(
            f"--adopt {adopt_harness} names a body that only points at the other root "
            "instruction file; no side carries content to adopt, so write the intended "
            "instructions into one file first"
        )
    kept_filename = AGENT_HARNESS_INSTRUCTION_FILENAMES[adopt_harness]
    discarded = [
        AGENT_HARNESS_INSTRUCTION_FILENAMES[other]
        for other in others
        if not is_delegation_candidate(bodies_by_harness[other], kept_filename)
    ]
    if discarded:
        raise CliInputError(
            f"--adopt {adopt_harness} would discard the body of "
            f"{', '.join(sorted(discarded))}, which carries content of its own rather than a "
            "pointer at another root instruction file; adoption replaces a whole body, so no "
            "answer authorizes it"
        )
    return {harness: kept for harness in bodies_by_harness}


def bootstrap_wrap(
    text_a: str,
    text_b: str,
    name: str = BOOTSTRAP_SHARED_REGION_NAME,
    threshold: float = BOOTSTRAP_SHARED_THRESHOLD,
) -> tuple[str, str]:
    """Wrap the biggest whole-line identical span as one shared region in each text.

    The single assumption the tool makes on first encounter: at most one shared region, wrapped
    only when the biggest whole-line identical span covers more than ``threshold`` of the larger
    file. The span is snapped to line boundaries and wrapped at each text's own offsets, so the
    divergent independent content around it keeps its lines intact. Below the threshold, nothing
    is wrapped. After this pass the operator owns sharing granularity.
    """
    a_start, a_end, b_start, b_end = _longest_identical_line_span(text_a, text_b)
    larger = max(len(text_a), len(text_b))
    size = a_end - a_start
    if larger == 0 or size / larger <= threshold or not text_a[a_start:a_end].strip():
        return text_a, text_b
    return (
        _wrap_shared_at(text_a, a_start, a_end, name),
        _wrap_shared_at(text_b, b_start, b_end, name),
    )


# --- Managed block placement ---------------------------------------------------------------


def _strip_managed_block(text: str) -> str:
    """Return ``text`` with any managed or retired router block removed."""
    bounds = _managed_block_bounds(text)
    if bounds is None:
        return text
    start, end = bounds
    remainder = text[:start].rstrip("\n") + "\n" + text[end:].lstrip("\n")
    return remainder.strip("\n")


def prepend_router_block(block: str, body: str) -> str:
    """Return a document whose router block is first, followed by the product content.

    The router is always the first content of the file, so the reading agent reaches its
    read-the-whole-file instruction before anything else. Exactly one trailing newline.
    """
    router = block.strip("\n")
    content = body.strip("\n")
    if not content:
        return f"{router}\n"
    return f"{router}\n\n{content}\n"


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


def build_root_instruction_documents(
    seeds: Mapping[str, str],
    blocks_by_harness: Mapping[str, str],
    adopt_harness: str | None = None,
) -> dict[str, str]:
    """Compose each harness's root document: router block first, then product content.

    Pure over the seed and block strings. Each seed's product content is taken (retired generated
    bodies excluded, any existing managed block removed). On first encounter — neither file
    carries a shared region — the biggest contiguous identical span is wrapped as one shared
    region per :func:`bootstrap_wrap`; once a shared region exists, the bodies are left as the
    operator arranged them. The per-harness router block is then prepended to each.

    ``adopt_harness`` carries an operator decision and defaults to none. A body that merely looks
    like a pointer at the other root instruction file is never adopted here: the reconcile reports
    it as an ambiguity, and only the operator's answer arrives as ``adopt_harness``. Composing a
    document never destroys a body on its own reading of that body.

    Adoption belongs to the bootstrap pass, so an answer that arrives after that pass has closed
    is refused rather than dropped. Passing over it would write both files, exit zero, and leave
    the operator reading a success that answered nothing.
    """
    body_claude = _strip_managed_block(_product_owned_root_document(seeds["claude"]))
    body_codex = _strip_managed_block(_product_owned_root_document(seeds["codex"]))

    if is_first_encounter(body_claude, body_codex):
        if adopt_harness is not None:
            adopted = adopt_delegated_body(
                {"claude": body_claude, "codex": body_codex}, adopt_harness
            )
            body_claude, body_codex = adopted["claude"], adopted["codex"]
        body_claude, body_codex = bootstrap_wrap(body_claude, body_codex)
    elif adopt_harness is not None:
        raise CliInputError(
            f"--adopt {adopt_harness} applies only to a first encounter, and a root instruction "
            "file already carries a shared region or a malformed shared fence; no delegation is "
            "open for this answer to resolve"
        )

    return {
        "claude": prepend_router_block(blocks_by_harness["claude"], body_claude),
        "codex": prepend_router_block(blocks_by_harness["codex"], body_codex),
    }


# --- CLI edge: path validation -------------------------------------------------------------


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
    template = pathlib.Path(raw_template).expanduser()
    if template.is_symlink():
        raise CliInputError(f"--template is a symlink: {raw_template}")
    try:
        template = template.resolve(strict=True)
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
    """Write ``text`` as a regular file, replacing any file or symlink.

    Every caller passes a ``_repo_child(repo_root, <fixed filename>)`` path: ``repo_root`` is a
    resolved, existing directory (``_validated_repo_root``), the filename is a constant
    (``CLAUDE.md``/``AGENTS.md``), and ``_repo_child`` rejects a parent that resolves outside
    ``repo_root`` — so the write target is provably inside the operator's own repository, not
    attacker-controlled path data.
    """
    if path.exists() or path.is_symlink():
        path.unlink()  # NOSONAR S2083
    path.write_text(text, encoding="utf-8")  # NOSONAR S2083


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


def _read_both_root_texts(repo_root: pathlib.Path) -> tuple[str, str] | None:
    """Read both root instruction files' text, or None when either is absent."""
    texts = []
    for filename in AGENT_HARNESS_INSTRUCTION_FILENAMES.values():
        path = _repo_child(repo_root, filename)
        text = _read_text_if_present(path, repo_root)
        if text is None:
            return None
        texts.append(text)
    return texts[0], texts[1]


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
) -> InstructionStatus:
    """CLI-edge helper: return ``absent``, ``stale``, or ``current`` for one instruction file.

    The filesystem read lives here at the edge, not in the pure render functions.
    """
    if not instruction_path.is_file():
        return InstructionStatus.ABSENT
    if containment_root is not None:
        _validate_read_target(instruction_path, containment_root)
    text = instruction_path.read_text(encoding="utf-8")
    if _managed_block_text(text) is None:
        return InstructionStatus.STALE
    if _router_marker_match(text) is None:
        # A retired-marker block is present but not the current compressed marker; a re-render
        # migrates it.
        return InstructionStatus.STALE
    bounds = router_block_bounds(text)
    if bounds is None or bounds[0] != 0:
        # The router block must be the first content of the file so a reading agent reaches its
        # read-the-whole-file instruction before any product content; a router preceded by prose
        # is stale, and a re-render moves it back to the top.
        return InstructionStatus.STALE
    if malformed_shared_regions(text):
        # A shared open fence with no matching close is a malformed region — an ambiguous case for
        # the update skill, surfaced as stale rather than left silently in the instruction surface.
        return InstructionStatus.STALE
    version = parse_instruction_version(text)
    if version is None or is_stale(version, installed_version):
        return InstructionStatus.STALE
    if parse_instruction_languages(text) != normalize_languages(languages):
        return InstructionStatus.STALE
    return InstructionStatus.CURRENT


def write_root_instruction_files(
    repo_root: pathlib.Path,
    blocks_by_harness: Mapping[str, str],
    adopt_harness: str | None = None,
) -> None:
    """Insert router blocks and bootstrap shared regions, replacing symlinks with files."""
    seeds = _root_seed_documents(repo_root)
    documents = build_root_instruction_documents(
        seeds, blocks_by_harness, adopt_harness
    )
    for harness, filename in AGENT_HARNESS_INSTRUCTION_FILENAMES.items():
        _replace_path_with_text(_repo_child(repo_root, filename), documents[harness])


def remove_obsolete_spx_instruction_files(repo_root: pathlib.Path) -> None:
    """Remove retired ``spx/`` instruction files when present."""
    spx_dir = _spx_dir(repo_root)
    if not spx_dir.exists():
        return
    for filename in OBSOLETE_SPX_INSTRUCTION_FILENAMES:
        path = spx_dir / filename
        if path.exists() or path.is_symlink():
            path.unlink()


# --- CLI edge: git-recency shared-region reconcile -----------------------------------------


@dataclass(frozen=True)
class ReconcileReport:
    """The outcome of a shared-region reconcile over the two root files."""

    reconciled: tuple[str, ...] = ()
    dirty: tuple[str, ...] = ()
    tie: tuple[str, ...] = ()
    one_sided: tuple[str, ...] = ()
    malformed: tuple[str, ...] = ()
    delegating: tuple[str, ...] = ()

    @property
    def ambiguous(self) -> bool:
        """Whether any region needs the update skill's judgment rather than a deterministic write."""
        return bool(
            self.dirty
            or self.tie
            or self.one_sided
            or self.malformed
            or self.delegating
        )


class Runner(Protocol):
    """Execute one git command through an injectable process boundary."""

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: pathlib.Path,
        capture_output: bool,
        text: bool,
        check: bool,
    ) -> subprocess.CompletedProcess[str]: ...


def _subprocess_runner(
    argv: Sequence[str],
    *,
    cwd: pathlib.Path,
    capture_output: bool,
    text: bool,
    check: bool,
) -> subprocess.CompletedProcess[str]:
    """The default runner: the one place this script reaches a real process."""
    return subprocess.run(  # noqa: S603
        argv,
        cwd=cwd,
        capture_output=capture_output,
        text=text,
        check=check,
    )


def _git(
    repo_root: pathlib.Path, *args: str, runner: Runner = _subprocess_runner
) -> subprocess.CompletedProcess[str]:
    """Run a git command in ``repo_root``, capturing output; never raising on non-zero exit."""
    return runner(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _working_tree_dirty(
    repo_root: pathlib.Path, filename: str, *, runner: Runner = _subprocess_runner
) -> bool:
    """Report whether ``filename`` carries uncommitted working-tree changes."""
    proc = _git(repo_root, "status", "--porcelain", "--", filename, runner=runner)
    return bool(proc.stdout.strip())


def _region_line_range(text: str, name: str) -> tuple[int, int] | None:
    """Return the 1-based inclusive line range of the named region's content body, or None.

    The range covers only the content lines between the fences — the fence lines themselves and
    the blank separators around them are excluded — so a ``git log -L`` over it reflects the
    region's own content history: a commit touching only a fence or a separator line does not read
    as a content change and cannot flip the recency winner.
    """
    open_marker, close_marker = shared_open_marker(name), shared_close_marker(name)
    start = _find_fence_line(text, open_marker)
    if start == -1:
        return None
    body_start = start + len(open_marker)
    end = _find_fence_line(text, close_marker, body_start)
    if end == -1:
        return None
    body = text[body_start:end]
    leading = len(body) - len(body.lstrip("\n"))
    trailing = len(body) - len(body.rstrip("\n"))
    content_start = body_start + leading
    content_end = end - trailing  # one past the last content character
    if content_end <= content_start:
        return None
    first_line = text.count("\n", 0, content_start) + 1
    last_line = text.count("\n", 0, content_end - 1) + 1
    return (first_line, last_line)


def _region_committed_timestamp(
    repo_root: pathlib.Path,
    filename: str,
    text: str,
    name: str,
    *,
    runner: Runner = _subprocess_runner,
) -> int | None:
    """Return the committer timestamp of the last commit that touched the region's lines, or None.

    ``git log -L<start>,<end>:<file>`` scopes recency to the shared region's own line range rather
    than the whole file, so a later commit that edited only a file's independent content does not
    read as a newer region and overwrite the other side's genuinely-more-current body. A missing
    timestamp — an untracked file, a range git cannot resolve — returns None, so the region falls
    to the ambiguous tie path rather than a guessed side.
    """
    line_range = _region_line_range(text, name)
    if line_range is None:
        return None
    start_line, end_line = line_range
    proc = _git(
        repo_root,
        "log",
        "-1",
        "--no-patch",
        "--format=%ct",
        f"-L{start_line},{end_line}:{filename}",
        runner=runner,
    )
    output = proc.stdout.strip()
    if proc.returncode != 0 or not output:
        return None
    try:
        return int(output.splitlines()[0])
    except (ValueError, IndexError):
        return None


def _region_recency_winner(
    repo_root: pathlib.Path,
    name: str,
    text_a: str,
    text_b: str,
    *,
    runner: Runner = _subprocess_runner,
) -> str | None:
    """Return the harness whose shared region was committed more recently, or None.

    ``"a"`` is claude, ``"b"`` codex. None is a tie — equal region timestamps, or a timestamp
    missing for either side — the ambiguous case the update skill resolves, never a side the
    deterministic reconcile guesses.
    """
    claude = _region_committed_timestamp(
        repo_root,
        AGENT_HARNESS_INSTRUCTION_FILENAMES["claude"],
        text_a,
        name,
        runner=runner,
    )
    codex = _region_committed_timestamp(
        repo_root,
        AGENT_HARNESS_INSTRUCTION_FILENAMES["codex"],
        text_b,
        name,
        runner=runner,
    )
    if claude is None or codex is None or claude == codex:
        return None
    return "a" if claude > codex else "b"


def reconcile_root_shared_regions(
    repo_root: pathlib.Path,
    forced_winner: str | None = None,
    *,
    runner: Runner = _subprocess_runner,
) -> ReconcileReport:
    """Reconcile diverged shared regions across the two root files by git recency.

    Operates on the committed state: a root file carrying uncommitted working-tree changes is
    left untouched and reported, so the reconcile never clobbers an in-progress edit. Each
    diverged region is resolved independently by whole-side replacement from the side whose region
    was committed more recently, scoped to that region's own line range so an unrelated later
    commit does not decide it; a region-recency tie and a region present in only one file are
    reported as ambiguous for the update skill, never guessed. ``forced_winner`` (``"a"`` claude,
    ``"b"`` codex) applies the operator's tie break to every diverged region, bypassing the
    recency read.
    """
    dirty = tuple(
        filename
        for filename in AGENT_HARNESS_INSTRUCTION_FILENAMES.values()
        if _working_tree_dirty(repo_root, filename, runner=runner)
    )
    if dirty:
        return ReconcileReport(dirty=dirty)

    texts = _read_both_root_texts(repo_root)
    if texts is None:
        return ReconcileReport()
    original_a, original_b = texts
    text_a, text_b = original_a, original_b

    one_sided = one_sided_shared_regions(text_a, text_b)
    malformed = tuple(
        sorted(
            set(malformed_shared_regions(text_a))
            | set(malformed_shared_regions(text_b))
        )
    )
    # A malformed name (a duplicate that `parse_shared_regions` collapsed to one body) is reported,
    # never reconciled: its parsed body is unreliable, so whole-side replacement from it would
    # write the wrong content. It is surfaced through ``malformed`` for the operator to repair.
    malformed_set = set(malformed)
    diverged = tuple(
        name
        for name in diverged_shared_regions(text_a, text_b)
        if name not in malformed_set
    )
    delegating = unresolved_delegation(repo_root)
    if not diverged:
        return ReconcileReport(
            one_sided=one_sided, malformed=malformed, delegating=delegating
        )

    # Recency and the winning body read the committed originals (line ranges match git history),
    # while the writes accumulate on text_a / text_b; reconciling one region shifts another's line
    # numbers, so a later region must never derive its range from the already-mutated text.
    reconciled: list[str] = []
    tie: list[str] = []
    for name in diverged:
        winner = (
            forced_winner
            if forced_winner is not None
            else _region_recency_winner(
                repo_root, name, original_a, original_b, runner=runner
            )
        )
        if winner is None:
            tie.append(name)
            continue
        source = original_a if winner == "a" else original_b
        body = parse_shared_regions(source)[name]
        if winner == "a":
            text_b = set_shared_region(text_b, name, body)
        else:
            text_a = set_shared_region(text_a, name, body)
        reconciled.append(name)

    if text_a != original_a:
        _replace_path_with_text(
            _repo_child(repo_root, AGENT_HARNESS_INSTRUCTION_FILENAMES["claude"]),
            text_a,
        )
    if text_b != original_b:
        _replace_path_with_text(
            _repo_child(repo_root, AGENT_HARNESS_INSTRUCTION_FILENAMES["codex"]), text_b
        )
    return ReconcileReport(
        reconciled=tuple(reconciled),
        tie=tuple(tie),
        one_sided=one_sided,
        malformed=malformed,
        delegating=delegating,
    )


def unresolved_delegation(repo_root: pathlib.Path) -> tuple[str, ...]:
    """CLI-edge helper: return the root instruction files that may be a pointer at the other.

    Only a first encounter can adopt a body, so a candidate outside that state is not reported —
    reporting one there would name a remedy the write would decline to apply. The state test is
    :func:`is_first_encounter` and the candidate test is :func:`delegation_candidates`.
    """
    texts = _read_both_root_texts(repo_root)
    if texts is None:
        return ()
    bodies = {
        harness: _strip_managed_block(_product_owned_root_document(text))
        for harness, text in zip(("claude", "codex"), texts, strict=True)
    }
    if not is_first_encounter(bodies["claude"], bodies["codex"]):
        return ()
    return tuple(
        AGENT_HARNESS_INSTRUCTION_FILENAMES[harness]
        for harness in delegation_candidates(bodies)
    )


def shared_region_drift(repo_root: pathlib.Path) -> tuple[str, ...]:
    """CLI-edge helper: return the shared regions that diverge, are one-sided, or are malformed.

    Each is drift the surface must resolve before it is current: a diverged or one-sided region,
    or a malformed open fence with no matching close in either file. The pure comparisons are
    :func:`diverged_shared_regions`, :func:`one_sided_shared_regions`, and
    :func:`malformed_shared_regions`.
    """
    texts = _read_both_root_texts(repo_root)
    if texts is None:
        return ()
    text_a, text_b = texts
    return tuple(
        sorted(
            {
                *diverged_shared_regions(text_a, text_b),
                *one_sided_shared_regions(text_a, text_b),
                *malformed_shared_regions(text_a),
                *malformed_shared_regions(text_b),
            }
        )
    )


# --- CLI ------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Thin CLI edge: read the template, detect languages, render/write/check/reconcile."""
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    duplicate = duplicate_cli_option(raw_argv)
    if duplicate is not None:
        print(f"{DUPLICATE_FLAG_ERROR_PREFIX}{duplicate}", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Generate and validate the managed Spec Tree instruction surface in root CLAUDE.md and AGENTS.md."
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
        "--reconcile",
        action="store_true",
        help="Reconcile diverged shared regions across both root files by git recency.",
    )
    parser.add_argument(
        "--from",
        dest="from_harness",
        choices=tuple(AGENT_HARNESS_INSTRUCTION_FILENAMES),
        help="With --reconcile, apply this harness's diverged region bodies (operator tie break) instead of git recency.",
    )
    parser.add_argument(
        "--adopt",
        dest="adopt_harness",
        choices=tuple(AGENT_HARNESS_INSTRUCTION_FILENAMES),
        help="With --write, give both root files this harness's body (operator answer to a reported delegation candidate).",
    )
    parser.add_argument(
        "--languages",
        help="Comma-separated enabled languages; detected from spx/**/tests/ extensions when omitted.",
    )
    args = parser.parse_args(raw_argv)

    if args.adopt_harness is not None and not args.write:
        # Only the write applies an adoption. Rendering to stdout, checking, or reconciling with
        # an answer attached would report success while discarding it.
        print("error: --adopt requires --write", file=sys.stderr)
        return 2

    try:
        template_path = _validated_template_path(args.template)
    except CliInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    template_text = template_path.read_text(encoding="utf-8")
    installed = parse_template_frontmatter_version(template_text)
    if installed is None:
        print(
            f"{MISSING_TEMPLATE_VERSION_ERROR}: add a dotted-numeric "
            f"{TEMPLATE_VERSION_KEY} to the frontmatter of {template_path}",
            file=sys.stderr,
        )
        return 2

    try:
        repo_root = _validated_repo_root(args.repo_root)
    except CliInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.languages is not None:
        languages = _parse_languages(args.languages)
        allowed_languages = template_languages(template_text)
        allowed_language_set = set(allowed_languages)
        unsupported_languages = tuple(
            language for language in languages if language not in allowed_language_set
        )
        if unsupported_languages:
            print(
                "error: unsupported --languages token(s): "
                f"{', '.join(unsupported_languages)}; allowed languages: "
                f"{', '.join(allowed_languages)}",
                file=sys.stderr,
            )
            return 2
    elif repo_root is not None:
        try:
            languages = detect_languages_from_tree(_spx_dir(repo_root))
        except CliInputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        languages = ()

    if args.reconcile:
        if repo_root is None:
            print("error: --reconcile requires --repo-root", file=sys.stderr)
            return 2
        forced_winner = (
            {"claude": "a", "codex": "b"}[args.from_harness]
            if args.from_harness is not None
            else None
        )
        try:
            report = reconcile_root_shared_regions(repo_root, forced_winner)
        except CliInputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        for filename in report.dirty:
            print(f"dirty: {filename}", file=sys.stderr)
        for name in report.tie:
            print(f"ambiguous (recency tie): {name}", file=sys.stderr)
        for name in report.one_sided:
            print(f"ambiguous (one-sided): {name}", file=sys.stderr)
        for name in report.malformed:
            print(f"malformed: {name}", file=sys.stderr)
        for filename in report.delegating:
            print(f"ambiguous (delegating): {filename}", file=sys.stderr)
        for name in report.reconciled:
            print(f"reconciled: {name}")
        return 1 if report.ambiguous else 0

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
            if shared_region_drift(repo_root) or unresolved_delegation(repo_root):
                # A diverged or one-sided shared region is drift the reconcile resolves; report
                # it as stale so the gate does not pass over it. An unresolved delegation
                # candidate is the same: the routers alone can be current while one body still
                # waits on the operator's answer, and reporting current there would strand it.
                statuses.add(InstructionStatus.STALE)
        except CliInputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        # Absent dominates stale dominates current: report the worst across both files.
        for verdict in INSTRUCTION_STATUS_PRECEDENCE:
            if verdict in statuses:
                print(verdict)
                break
        return 0

    if args.write and repo_root is None:
        print("error: --write requires --repo-root", file=sys.stderr)
        return 2

    try:
        rendered = {
            harness: render(template_text, languages, installed, harness)
            for harness in AGENT_HARNESS_INSTRUCTION_FILENAMES
        }
    except UnresolvedInstructionTemplateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.write and repo_root is not None:
        try:
            write_root_instruction_files(repo_root, rendered, args.adopt_harness)
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
