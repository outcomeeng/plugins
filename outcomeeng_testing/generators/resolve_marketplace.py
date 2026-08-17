"""Generated domains for the /issue marketplace resolver's evidence.

Two domains, matching the two shapes the resolver's behavior takes.

The registration-entry domain is finite and source-owned: it is the product
of the resolver's own declared source fields over present, empty, and
absent, and each case's expected outcome is derived from the resolution rule
the decision states — a Codex local marketplace resolves ``source`` first
and then ``root``; a Claude Directory source resolves ``path``; an empty
value is not a value, so it falls through wherever an absent one would —
never by reading the script's branches. Every combination is emitted twice, once carrying decoy
fields the other runtime owns, because the declared rule says the resolver
reads no field outside the ones its runtime names; a resolver that consulted
a decoy would change an expected outcome.

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
                ("no-root", None),
            ):
                for decoy_label, decoys in (("plain", False), ("decoyed", True)):
                    # The declared rule: a local source type resolves the
                    # registered source, then the materialized root. An
                    # empty source is not a source, so it falls through the
                    # same way an absent one does.
                    if source_type == RESOLVER.CODEX_LOCAL_SOURCE_TYPE:
                        expected = source or root
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
                directory = (
                    source is not None
                    and source.lower() == RESOLVER.CLAUDE_DIRECTORY_SOURCE
                )
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

    The alphabet is what argv can carry: encodable as UTF-8, and no NUL.
    Either one fails in the process layer before resolution happens, so a
    case built from one says nothing about the resolver.
    """
    return st.text(
        alphabet=st.characters(min_codepoint=1, codec="utf-8"),
        min_size=1,
        max_size=32,
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
