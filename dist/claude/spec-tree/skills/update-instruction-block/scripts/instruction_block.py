"""Deterministic generator for a product's root Spec Tree instruction surface.

One repository is worked by both Claude Code and Codex at once, and each agent harness
retains its root instruction file across compaction: ``CLAUDE.md`` for Claude Code and
``AGENTS.md`` for Codex. The Spec Tree instructions are therefore a managed surface in those
root files, not generated files under ``spx/``. Each root file's managed surface is three
region kinds:

- A generated **router block**, delimited by a single opening marker
  ``<!-- SPEC-TREE v{version} langs:{list} -->`` and a closing ``<!-- /SPEC-TREE -->``. Both
  router blocks render from one canonical template: the body is shared, and the spans that
  differ by agent harness are authored once as ``<!-- harness:NAME -->`` blocks rendered only
  into that harness's block, mirroring the ``<!-- lang:NAME -->`` language blocks. The only
  per-product variation inside the router is the enabled-language list.
- Named **per-product command slots** over the fixed set ``author``, ``verify``, ``gate``,
  ``merge``, each delimited by ``<!-- SPEC-TREE:{slot} -->`` and ``<!-- /SPEC-TREE:{slot} -->``.
  A slot holds one product's operational command for a spec-tree phase; its body is
  product-owned and preserved verbatim across a re-render. A slot's body is identical in both
  root files, so an empty or placeholder slot in one file is filled from its filled sibling.
- The product's own **out-of-fence prose**, preserved verbatim.

Router generation is deterministic and needs no agent judgment: the enabled-language list is
read from the product's ``spx/**/tests/`` test-file extensions, staleness is a dotted-version
and language-set comparison, and the render is a pure string transformation. Slot handling is
fence recognition plus verbatim carry-through with sibling fill; the one case it does not
resolve — a slot filled with different bodies in the two files — is reported as a conflict for
the update skill's git-recency judgment. The parse, version-compare, language-filter,
harness-filter, router-replacement, slot-preservation, sibling-fill, and render functions take
document strings and return document strings — no filesystem, environment, or subprocess
access. The CLI edge reads the template, globs the test extensions, replaces symlinked root
instruction files with regular files, removes obsolete ``spx/`` instruction files, and writes
both root files.
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

# The router block's compressed marker. The opening marker carries the two fields staleness
# reads — the dotted template version and the recorded enabled-language list — inline, so no
# separate metadata comment lines are written. The template source is always the methodology's
# own, so it is not recorded.
ROUTER_MARKER_PREFIX = "<!-- SPEC-TREE v"
ROUTER_BLOCK_END = "<!-- /SPEC-TREE -->"
ROUTER_LANGS_KEY = "langs:"
_ROUTER_MARKER_RE = re.compile(
    r"<!--\s*SPEC-TREE\s+v(?P<version>\S+)\s+langs:(?P<langs>\S*)\s*-->"
)

# Retired marker pairs. A managed surface delimited by one of these is generated content from a
# superseded naming; it is located and replaced in place on upgrade rather than left behind as
# prose while a new router block is appended. The two prior forms are the four-line
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
# is replaced. The source prefix has no production reader — the compressed marker records no
# source field — and survives only as the vocabulary legacy-format test fixtures build and the
# render's output asserts absent.
MANAGED_TEMPLATE_VERSION_PREFIX = "<!-- spec-tree-template-version:"
MANAGED_TEMPLATE_SOURCE_PREFIX = "<!-- spec-tree-template-source:"
MANAGED_LANGUAGES_PREFIX = "<!-- spec-tree-languages:"

# The fixed, methodology-defined per-product command slots, one per spec-tree phase that runs a
# product command. ``author`` rebuilds or regenerates artifacts after a create/update/delete on
# a spec, test, or implementation file; ``verify`` is the deterministic check over a node and
# the changeset; ``gate`` is the full deterministic bundle; ``merge`` is the transport command.
FIXED_COMMAND_SLOTS = ("author", "verify", "gate", "merge")
# A slot body carrying this mark is unfilled — a scaffolded placeholder, not a product command.
# Sibling-fill and conflict detection treat such a body as empty.
SLOT_PLACEHOLDER_MARK = "<!-- unfilled -->"

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


def _router_marker(version: str, languages: tuple[str, ...]) -> str:
    """Build the router block's opening marker from the version and enabled languages."""
    return (
        f"{ROUTER_MARKER_PREFIX}{version} {ROUTER_LANGS_KEY}{','.join(languages)} -->"
    )


def _router_marker_match(text: str) -> re.Match[str] | None:
    """Return the router block's opening-marker match, or None."""
    return _ROUTER_MARKER_RE.search(text)


def _legacy_block_bounds(text: str) -> tuple[int, int] | None:
    """Return a retired marker pair's start and end offsets when present."""
    for start_marker, end_marker in LEGACY_MANAGED_BLOCK_MARKERS:
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


def _router_block_bounds(text: str) -> tuple[int, int] | None:
    """Return the current router block's start and end offsets when present."""
    match = _router_marker_match(text)
    if match is None:
        return None
    start = match.start()
    end_marker_start = text.find(ROUTER_BLOCK_END, match.end())
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
    return _router_block_bounds(text) or _legacy_block_bounds(text)


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
    ) or parse_instruction_version(text)


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
    """Render one agent harness's router block from the template and enabled languages.

    Language-conditional blocks render only for enabled languages and harness-conditional
    blocks only for ``harness``; nothing else is substituted, so brace-delimited illustration
    tokens pass through unchanged. The opening marker records the version and language list
    inline, so a later update reads both back from the marker without separate metadata lines.
    """
    languages = normalize_languages(languages)
    _, template_body = _split_frontmatter(template_text)

    body = _filter_languages(template_body, languages)
    body = _filter_harness(body, harness)
    body = _BLANK_RUN.sub("\n\n", body)

    marker = _router_marker(installed_version, languages)
    rendered = f"{marker}\n{body.rstrip()}\n\n{ROUTER_BLOCK_END}"
    return rendered.rstrip("\n") + "\n"


# --- Command slots -------------------------------------------------------------------------


def _slot_open(slot: str) -> str:
    return f"<!-- SPEC-TREE:{slot} -->"


def _slot_close(slot: str) -> str:
    return f"<!-- /SPEC-TREE:{slot} -->"


def slot_placeholder(slot: str) -> str:
    """Return the scaffolded placeholder body for an unfilled command slot."""
    return f"{SLOT_PLACEHOLDER_MARK} add this product's `{slot}` command"


def _render_slot(slot: str, body: str) -> str:
    # Blank lines around the body keep the fence dprint-compliant: an HTML comment and the
    # Markdown that follows it are separate blocks, so the formatter requires a blank between.
    return f"{_slot_open(slot)}\n\n{body}\n\n{_slot_close(slot)}"


def parse_command_slot(text: str, slot: str) -> str | None:
    """Return a command slot's body, or None when the slot fence is absent."""
    open_marker, close_marker = _slot_open(slot), _slot_close(slot)
    start = text.find(open_marker)
    if start == -1:
        return None
    body_start = start + len(open_marker)
    end = text.find(close_marker, body_start)
    if end == -1:
        return None
    return text[body_start:end].strip("\n")


def is_slot_filled(body: str | None) -> bool:
    """Report whether a slot body is a real product command rather than empty or placeholder."""
    return body is not None and body.strip() != "" and SLOT_PLACEHOLDER_MARK not in body


def set_command_slot(text: str, slot: str, body: str) -> str:
    """Return ``text`` with the command slot's body replaced; unchanged when the fence is absent."""
    open_marker, close_marker = _slot_open(slot), _slot_close(slot)
    start = text.find(open_marker)
    if start == -1:
        return text
    body_start = start + len(open_marker)
    end = text.find(close_marker, body_start)
    if end == -1:
        return text
    # Blank lines around the body match the dprint-compliant fence shape from ``_render_slot``.
    return f"{text[:body_start]}\n\n{body}\n\n{text[end:]}"


def _next_fence_index(text: str, pos: int) -> int:
    """Return the earliest offset at or after ``pos`` of any fence marker, or ``len(text)``.

    Both the router markers (``<!-- SPEC-TREE`` / ``<!-- /SPEC-TREE``) and the slot markers
    share these prefixes, so this bounds a malformed open-only fence's orphaned body at the
    next fence of any kind or the end of the document.
    """
    found = [
        index
        for marker in ("<!-- SPEC-TREE", "<!-- /SPEC-TREE")
        if (index := text.find(marker, pos)) != -1
    ]
    return min(found) if found else len(text)


def ensure_slot_fences(text: str) -> str:
    """Return ``text`` with every fixed command-slot fence present and well-formed.

    A slot with no parseable fence is repaired. Presence uses the same full open-and-close
    contract as :func:`parse_command_slot`, so a malformed open-only fence — an open marker
    with no matching close, from a truncated write or a partial edit — is not mistaken for a
    valid one. Repair preserves the slot's product-owned body: an open-only fence's orphaned
    body (from after the open marker to the next fence or end of document) is recovered and
    re-rendered inside a well-formed fence, never discarded, so the generator does not overwrite
    a real command. A slot with no recoverable body — truly absent, or an open marker with an
    empty body — is scaffolded with a placeholder.
    """
    additions = []
    for slot in FIXED_COMMAND_SLOTS:
        if parse_command_slot(text, slot) is not None:
            continue
        body = slot_placeholder(slot)
        start = text.find(_slot_open(slot))
        if start != -1:
            body_start = start + len(_slot_open(slot))
            end = _next_fence_index(text, body_start)
            recovered = text[body_start:end].strip("\n")
            if recovered:
                body = recovered
            text = f"{text[:start]}{text[end:]}"
        # Drop any stray close marker (a close-only fragment carries no recoverable body).
        text = text.replace(_slot_close(slot), "")
        additions.append(_render_slot(slot, body))
    if not additions:
        return text
    base = _BLANK_RUN.sub("\n\n", text).rstrip("\n")
    joined = "\n\n".join(additions)
    return f"{base}\n\n{joined}\n" if base else f"{joined}\n"


def command_slot_conflicts(text_a: str, text_b: str) -> tuple[str, ...]:
    """Return the fixed slots filled with different bodies in the two texts.

    A conflict is the one case sibling-fill cannot resolve: both files carry a real command for
    the slot and the commands differ, so choosing which is current needs git-recency judgment
    the deterministic generator does not supply.
    """
    conflicts = []
    for slot in FIXED_COMMAND_SLOTS:
        body_a = parse_command_slot(text_a, slot)
        body_b = parse_command_slot(text_b, slot)
        if (
            body_a is not None
            and body_b is not None
            and is_slot_filled(body_a)
            and is_slot_filled(body_b)
            and body_a.strip() != body_b.strip()
        ):
            conflicts.append(slot)
    return tuple(conflicts)


def command_slots_pending_sibling_fill(text_a: str, text_b: str) -> tuple[str, ...]:
    """Return the fixed slots filled in one text but empty or placeholder in the other.

    These are the slots sibling-fill would change on the next ``--write``: the two files' slot
    bodies are not yet identical, so the surface is drift until a write propagates the filled
    body to its sibling.
    """
    pending = []
    for slot in FIXED_COMMAND_SLOTS:
        filled_a = is_slot_filled(parse_command_slot(text_a, slot))
        filled_b = is_slot_filled(parse_command_slot(text_b, slot))
        if filled_a != filled_b:
            pending.append(slot)
    return tuple(pending)


def reconcile_command_slots(text_a: str, text_b: str) -> tuple[str, str]:
    """Return the two texts with each slot's body made identical by sibling-fill.

    A slot filled in one file and empty or placeholder in the other is filled from the filled
    side. A slot filled differently in both files is a conflict and is left unchanged.
    """
    for slot in FIXED_COMMAND_SLOTS:
        body_a = parse_command_slot(text_a, slot)
        body_b = parse_command_slot(text_b, slot)
        if body_a is None or body_b is None:
            continue
        a_filled, b_filled = is_slot_filled(body_a), is_slot_filled(body_b)
        if a_filled and not b_filled:
            text_b = set_command_slot(text_b, slot, body_a)
        elif b_filled and not a_filled:
            text_a = set_command_slot(text_a, slot, body_b)
    return text_a, text_b


def missing_command_slots(text: str) -> tuple[str, ...]:
    """Return the fixed command slots whose fence is absent from ``text``.

    A fixed slot must always carry its fence — filled or placeholder — so the router's by-name
    references never dangle; an absent fence is drift a re-render restores by re-scaffolding it.
    """
    return tuple(
        slot for slot in FIXED_COMMAND_SLOTS if parse_command_slot(text, slot) is None
    )


# --- CLI edge ------------------------------------------------------------------------------


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
    if _router_marker_match(text) is None:
        # A retired-marker block is present but not the current compressed marker; a re-render
        # migrates it.
        return "stale"
    version = parse_instruction_version(text)
    if version is None or is_stale(version, installed_version):
        return "stale"
    if parse_instruction_languages(text) != normalize_languages(languages):
        return "stale"
    if missing_command_slots(text):
        # A fixed command slot's fence is absent — a re-render restores it, so the surface is
        # stale until it does. The shipped --check verb enforces this without the git-diff gate.
        return "stale"
    return "current"


def upsert_managed_block(document: str, block: str) -> str:
    """Return ``document`` with exactly one managed Spec Tree router block."""
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


def build_root_instruction_documents(
    seeds: Mapping[str, str], blocks_by_harness: Mapping[str, str]
) -> dict[str, str]:
    """Compose each harness's root document: router block, slot fences, and sibling-fill.

    Pure over the seed and block strings: upsert the router block into product-owned prose,
    scaffold every missing command-slot fence with a placeholder, then reconcile the two
    harnesses' slots so each slot's body is identical across them.
    """
    documents = {
        harness: ensure_slot_fences(
            upsert_managed_block(
                _product_owned_root_document(seeds[harness]),
                blocks_by_harness[harness],
            )
        )
        for harness in AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    claude, codex = build_root_instruction_documents_reconciled(documents)
    return {"claude": claude, "codex": codex}


def build_root_instruction_documents_reconciled(
    documents: Mapping[str, str],
) -> tuple[str, str]:
    """Reconcile the two harnesses' command slots by sibling-fill; return (claude, codex)."""
    claude, codex = reconcile_command_slots(documents["claude"], documents["codex"])
    return claude, codex


def write_root_instruction_files(
    repo_root: pathlib.Path, blocks_by_harness: Mapping[str, str]
) -> None:
    """Insert router blocks and command slots into root files, replacing symlinks with files."""
    seeds = _root_seed_documents(repo_root)
    documents = build_root_instruction_documents(seeds, blocks_by_harness)
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


def conflicting_command_slots(repo_root: pathlib.Path) -> tuple[str, ...]:
    """CLI-edge helper: return fixed slots filled with different bodies across the root files.

    The filesystem read lives here at the edge; the comparison is the pure
    :func:`command_slot_conflicts`.
    """
    texts = _read_both_root_texts(repo_root)
    if texts is None:
        return ()
    return command_slot_conflicts(texts[0], texts[1])


def sibling_fill_pending_command_slots(repo_root: pathlib.Path) -> tuple[str, ...]:
    """CLI-edge helper: return fixed slots filled in one root file but not the other.

    The filesystem read lives here at the edge; the comparison is the pure
    :func:`command_slots_pending_sibling_fill`.
    """
    texts = _read_both_root_texts(repo_root)
    if texts is None:
        return ()
    return command_slots_pending_sibling_fill(texts[0], texts[1])


def fill_command_slot_from(
    repo_root: pathlib.Path, slot: str, source_harness: str
) -> None:
    """Set one command slot in both root files to the ``source_harness`` file's body.

    The write is deterministic; choosing the source harness is the update skill's git-recency
    judgment, which the deterministic generator does not make. Used to reconcile a slot filled
    with different bodies in the two files after that judgment picks the more recent side.
    Every read is validated against ``repo_root`` so a symlinked root file escaping the
    repository is rejected rather than followed.
    """
    source_path = _repo_child(
        repo_root, AGENT_HARNESS_INSTRUCTION_FILENAMES[source_harness]
    )
    source_text = _read_text_if_present(source_path, repo_root)
    if source_text is None:
        raise CliInputError(
            f"source harness {source_harness} instruction file is absent"
        )
    body = parse_command_slot(source_text, slot)
    if body is None:
        raise CliInputError(
            f"source harness {source_harness} has no {slot} command slot"
        )
    for filename in AGENT_HARNESS_INSTRUCTION_FILENAMES.values():
        path = _repo_child(repo_root, filename)
        text = _read_text_if_present(path, repo_root)
        if text is None:
            # Reconciling a slot across both files is meaningless when one is absent; fail
            # loudly rather than leave a partial fill, symmetric with the source-file case.
            raise CliInputError(f"root instruction file is absent: {filename}")
        _replace_path_with_text(
            path, set_command_slot(ensure_slot_fences(text), slot, body)
        )


def main(argv: list[str] | None = None) -> int:
    """Thin CLI edge: read the template, detect languages, render and write both files."""
    parser = argparse.ArgumentParser(
        description="Generate the managed Spec Tree instruction surface in root CLAUDE.md and AGENTS.md."
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
    parser.add_argument(
        "--fill-slot",
        choices=FIXED_COMMAND_SLOTS,
        help="Reconcile one command slot across both root files from the --from harness.",
    )
    parser.add_argument(
        "--from",
        dest="from_harness",
        choices=tuple(AGENT_HARNESS_INSTRUCTION_FILENAMES),
        help="Source harness whose slot body fills both files under --fill-slot.",
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

    if args.fill_slot is not None:
        if repo_root is None:
            print("error: --fill-slot requires --repo-root", file=sys.stderr)
            return 2
        if args.from_harness is None:
            print("error: --fill-slot requires --from", file=sys.stderr)
            return 2
        try:
            fill_command_slot_from(repo_root, args.fill_slot, args.from_harness)
        except CliInputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        return 0

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
            if conflicting_command_slots(repo_root):
                # A command slot filled differently in the two files is drift the update skill
                # reconciles; report it as stale so the gate does not pass over it.
                statuses.add("stale")
            if sibling_fill_pending_command_slots(repo_root):
                # A slot filled in one file but not the other is drift the next --write resolves
                # by sibling-fill; the two bodies are not yet identical, so report it stale.
                statuses.add("stale")
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
