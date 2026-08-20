"""Generated domains for the /issue marketplace resolver's evidence.

Two domains, matching the two shapes the resolver's behavior takes.

The registration-entry domain is finite and source-owned: it is the product
of the resolver's own declared source fields over present, empty, and
absent. Each case's expected outcome is derived from the mapping the node
spec declares in
``spx/21-spec-tree.enabler/76-sessions.enabler/43-issue.enabler/issue.md``
-- the registered source taking precedence over the materialized root, a
Directory source matching its token exactly, and an empty value falling
through wherever an absent one would -- never from the script's branches.
Every combination is emitted twice, once carrying decoy fields the other
runtime owns, because that assertion states a field belonging to the other
runtime leaves the resolved path unchanged; a resolver consulting a decoy
would change an expected outcome.

The selection domain carries, per case, the names the diagnostic must
enumerate, derived from the layout the case declares rather than from the
resolver's own availability helper.

The malformed-payload domain is open: arbitrary JSON, and text that is not
JSON at all, have no finite enumeration, so they are generated rather than
listed.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

from hypothesis import strategies as st

from outcomeeng_testing.harnesses.resolve_marketplace import RESOLVER

_NON_LOCAL_SOURCE_TYPE = "git"
"""A Codex source type outside the local vocabulary the resolver accepts."""

_NON_DIRECTORY_SOURCE = "github"
"""A Claude source outside the Directory vocabulary the resolver accepts."""

_DECOY_PATH = "/decoy/top-level-path"
_DECOY_ROOT = "/decoy/top-level-root"


@dataclass(frozen=True)
class ResolutionCase:
    """One registration payload and the path the declared rule resolves."""

    label: str
    runtime: str
    payload: object
    expected_path: str | None
    """The resolved checkout path, or None when nothing resolves."""


def _codex_entry(
    *,
    source_type: str | None,
    source: str | None,
    root: str | None,
    decoys: bool,
) -> dict[str, object]:
    entry: dict[str, object] = {RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME}
    if source_type is not None or source is not None:
        marketplace_source: dict[str, object] = {}
        if source_type is not None:
            marketplace_source[RESOLVER.SOURCE_TYPE_FIELD] = source_type
        if source is not None:
            marketplace_source[RESOLVER.SOURCE_FIELD] = source
        entry[RESOLVER.MARKETPLACE_SOURCE_FIELD] = marketplace_source
    if root is not None:
        entry[RESOLVER.ROOT_FIELD] = root
    if decoys:
        # Fields no Codex entry carries. The declared rule reads the local
        # source and the materialized root only, so a resolver consulting a
        # top-level path or a top-level source type would resolve a case the
        # rule says resolves nothing.
        entry[RESOLVER.PATH_FIELD] = _DECOY_PATH
        entry[RESOLVER.SOURCE_TYPE_FIELD] = RESOLVER.CODEX_LOCAL_SOURCE_TYPE
    return entry


def _claude_entry(
    *, source: str | None, path: str | None, decoys: bool
) -> dict[str, object]:
    entry: dict[str, object] = {RESOLVER.NAME_FIELD: RESOLVER.DEFAULT_MARKETPLACE_NAME}
    if source is not None:
        entry[RESOLVER.SOURCE_FIELD] = source
    if path is not None:
        entry[RESOLVER.PATH_FIELD] = path
    if decoys:
        # Codex-shaped fields a Claude registration never carries.
        entry[RESOLVER.ROOT_FIELD] = _DECOY_ROOT
        entry[RESOLVER.MARKETPLACE_SOURCE_FIELD] = {
            RESOLVER.SOURCE_TYPE_FIELD: RESOLVER.CODEX_LOCAL_SOURCE_TYPE,
            RESOLVER.SOURCE_FIELD: _DECOY_ROOT,
        }
    return entry


def _codex_cases(base: str) -> Iterator[ResolutionCase]:
    source_types = (
        ("local", RESOLVER.CODEX_LOCAL_SOURCE_TYPE),
        ("nonlocal", _NON_LOCAL_SOURCE_TYPE),
        ("empty-type", ""),
        ("absent-type", None),
    )
    for type_label, source_type in source_types:
        for source_label, source in (
            ("source", f"{base}/codex-source"),
            ("empty-source", ""),
            ("no-source", None),
        ):
            for root_label, root in (
                ("root", f"{base}/codex-root"),
                ("empty-root", ""),
                ("no-root", None),
            ):
                for decoy_label, decoys in (("plain", False), ("decoyed", True)):
                    # The declared rule: a local source type resolves the
                    # registered source, then the materialized root. An
                    # empty source is not a source, so it falls through the
                    # same way an absent one does.
                    if source_type == RESOLVER.CODEX_LOCAL_SOURCE_TYPE:
                        expected = source or root or None
                    else:
                        expected = None
                    yield ResolutionCase(
                        label=(
                            f"codex-{type_label}-{source_label}"
                            f"-{root_label}-{decoy_label}"
                        ),
                        runtime=RESOLVER.RUNTIME_CODEX,
                        payload={
                            RESOLVER.MARKETPLACES_FIELD: [
                                _codex_entry(
                                    source_type=source_type,
                                    source=source,
                                    root=root,
                                    decoys=decoys,
                                )
                            ]
                        },
                        expected_path=expected,
                    )


def _claude_cases(base: str) -> Iterator[ResolutionCase]:
    sources = (
        ("directory", RESOLVER.CLAUDE_DIRECTORY_SOURCE),
        ("directory-titlecase", RESOLVER.CLAUDE_DIRECTORY_SOURCE.title()),
        ("nondirectory", _NON_DIRECTORY_SOURCE),
        ("absent-source", None),
    )
    for source_label, source in sources:
        for path_label, path in (
            ("path", f"{base}/claude-path"),
            ("empty-path", ""),
            ("no-path", None),
        ):
            for decoy_label, decoys in (("plain", False), ("decoyed", True)):
                # The declared rule: a Directory source resolves its path.
                # An empty path is not a path, and this runtime declares no
                # second field to fall through to.
                # The spec declares an exact token match, so a source
                # differing in case is a different source.
                directory = source == RESOLVER.CLAUDE_DIRECTORY_SOURCE
                expected = path if directory and path else None
                yield ResolutionCase(
                    label=(f"claude-{source_label}-{path_label}-{decoy_label}"),
                    runtime=RESOLVER.RUNTIME_CLAUDE,
                    payload=[_claude_entry(source=source, path=path, decoys=decoys)],
                    expected_path=expected,
                )


def registration_field_domain(base: str) -> list[ResolutionCase]:
    """The complete finite domain of the resolver's declared source fields.

    ``base`` prefixes every generated checkout path. The resolver reads no
    filesystem, so the prefix only has to be distinguishable in a failure
    message; it names no directory that has to exist.
    """
    return [*_codex_cases(base), *_claude_cases(base)]


@dataclass(frozen=True)
class SelectionCase:
    """One entry list and the path the requested name selects from it."""

    label: str
    runtime: str
    payload: object
    requested_name: str | None
    """The `--name` value, or None to omit the option entirely."""
    expected_path: str | None
    expected_available: str
    """The names the none-available diagnostic enumerates for this layout."""


_OTHER_MARKETPLACE_NAME = "other-marketplace"


def _selection_entry(name: str, path: str | None, runtime: str) -> dict[str, object]:
    if runtime == RESOLVER.RUNTIME_CODEX:
        entry = _codex_entry(
            source_type=RESOLVER.CODEX_LOCAL_SOURCE_TYPE,
            source=path,
            root=None,
            decoys=False,
        )
    else:
        entry = _claude_entry(
            source=RESOLVER.CLAUDE_DIRECTORY_SOURCE, path=path, decoys=False
        )
    entry[RESOLVER.NAME_FIELD] = name
    return entry


def _as_payload(entries: list[dict[str, object]], runtime: str) -> object:
    if runtime == RESOLVER.RUNTIME_CODEX:
        return {RESOLVER.MARKETPLACES_FIELD: entries}
    return entries


def entry_selection_domain(base: str) -> list[SelectionCase]:
    """The finite domain of which listed entry a requested name selects.

    Each layout is a list of (entry name, resolvable) pairs. The declared
    rule selects the first entry whose name equals the requested name and
    whose declared fields resolve; an omitted `--name` requests the default
    marketplace name.
    """
    default = RESOLVER.DEFAULT_MARKETPLACE_NAME
    layouts: tuple[tuple[str, tuple[tuple[str, bool], ...], str | None], ...] = (
        ("first-of-two-resolves", ((default, True), (default, True)), default),
        ("second-resolves", ((default, False), (default, True)), default),
        ("neither-resolves", ((default, False), (default, False)), default),
        (
            "other-name-precedes",
            ((_OTHER_MARKETPLACE_NAME, True), (default, True)),
            default,
        ),
        ("only-other-name", ((_OTHER_MARKETPLACE_NAME, True),), default),
        ("omitted-name-takes-default", ((default, True),), None),
        ("omitted-name-misses-other", ((_OTHER_MARKETPLACE_NAME, True),), None),
        ("empty-list", (), default),
    )

    cases: list[SelectionCase] = []
    for runtime in (RESOLVER.RUNTIME_CLAUDE, RESOLVER.RUNTIME_CODEX):
        for label, layout, requested in layouts:
            effective = requested if requested is not None else default
            entries: list[dict[str, object]] = []
            expected: str | None = None
            for index, (name, resolvable) in enumerate(layout):
                path = f"{base}/entry-{index}" if resolvable else None
                entries.append(_selection_entry(name, path, runtime))
                if expected is None and name == effective and path:
                    expected = path
            # Derived from the layout this case declares, not from the
            # resolver's availability helper: every entry the layout marks
            # resolvable is a marketplace in the listing that resolves a path.
            resolving = sorted(name for name, resolvable in layout if resolvable)
            cases.append(
                SelectionCase(
                    label=f"{runtime}-{label}",
                    runtime=runtime,
                    payload=_as_payload(entries, runtime),
                    requested_name=requested,
                    expected_path=expected,
                    expected_available=(
                        ", ".join(resolving)
                        if resolving
                        else RESOLVER.NO_LOCAL_MARKETPLACES
                    ),
                )
            )
    return cases


def json_payloads() -> st.SearchStrategy[object]:
    """Arbitrary JSON values — the open domain of well-formed stdin."""
    leaves = (
        st.none()
        | st.booleans()
        | st.integers()
        | st.floats(allow_nan=False, allow_infinity=False)
        | st.text()
    )
    return st.recursive(
        leaves,
        lambda children: (
            st.lists(children, max_size=4)
            | st.dictionaries(st.text(), children, max_size=4)
        ),
        max_leaves=8,
    )


def absent_marketplace_names() -> st.SearchStrategy[str]:
    """Marketplace names to request; collision is excluded by the caller.

    The alphabet excludes exactly what fails in the process layer before
    resolution happens, so no case says something about the process instead
    of the resolver: a NUL byte, which the exec layer rejects, and anything
    UTF-8 cannot encode. A leading ``-`` used to belong to that list and no
    longer does -- the harness attaches the name with ``--name=``, so option
    parsing carries it through -- and the boundary branch below keeps that
    case in every run rather than leaving it to be drawn by chance.
    """
    return st.one_of(
        st.sampled_from(["-", "-x", "--name", "--runtime"]),
        st.text(
            alphabet=st.characters(min_codepoint=1, codec="utf-8"),
            min_size=1,
            max_size=32,
        ),
    )


def non_json_text() -> st.SearchStrategy[str]:
    """Text that is not a JSON document — the open malformed-stdin domain."""

    def parses(candidate: str) -> bool:
        try:
            json.loads(candidate)
        except ValueError:
            return False
        return True

    return st.text(max_size=64).filter(lambda candidate: not parses(candidate))


def runtimes() -> st.SearchStrategy[str]:
    """The runtimes the resolver accepts, from its own vocabulary."""
    return st.sampled_from([RESOLVER.RUNTIME_CLAUDE, RESOLVER.RUNTIME_CODEX])
