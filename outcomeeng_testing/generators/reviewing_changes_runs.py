"""Bounded case domains for review-run changeset evidence.

Covers the changesets ``review_run.py`` meets beyond a plain edit: files a
generated-source declaration marks as generated extents, region-bounded outputs the
declaration does not mark as extents, renamed files, and unread sets too large for
one argument per path. Every path, pattern, and command is derived from a case label
so no test body carries a literal for them.
"""

from __future__ import annotations

import enum
from collections.abc import Iterator
from dataclasses import dataclass

UNREAD_SET_SIZE = 12


@dataclass(frozen=True)
class ExtentRelation:
    """One declared relation whose whole-file output pattern marks generated extents."""

    output_pattern: str
    sources: tuple[str, ...]
    generator: tuple[str, ...]
    regenerate: str


@dataclass(frozen=True)
class RegionRelation:
    """One declared relation whose output is a marker-bounded region of a file."""

    file: str
    begin: str
    end: str
    sources: tuple[str, ...]
    generator: tuple[str, ...]
    regenerate: str


@dataclass(frozen=True)
class ExtentMappingCase:
    """A declaration plus the changed paths it marks as extents and the ones it leaves ordinary."""

    label: str
    relations: tuple[ExtentRelation, ...]
    extents: tuple[tuple[str, int], ...]
    ordinary: tuple[str, ...]


def _relation(label: str, output_pattern: str) -> ExtentRelation:
    return ExtentRelation(
        output_pattern=output_pattern,
        sources=(f"{label}-src/**",),
        generator=(f"{label}-gen/**",),
        regenerate=f"just regenerate-{label}",
    )


def extent_mapping_cases() -> Iterator[ExtentMappingCase]:
    """Yield one case per whole-file output pattern form, and one with two relations.

    The forms are the ones ``spx/local/generated-sources.toml`` uses for whole-file
    outputs: a recursive tree pattern, a single-directory suffix pattern, and a literal
    path. The suffix and literal cases each carry a decoy beside the matched path that
    the pattern does not match.
    """
    tree = _relation("tree", "tree-out/**")
    suffix = _relation("suffix", "suffix-out/*.gen")
    literal = _relation("literal", "literal-out/fixed.lock")
    tree_extents = ("tree-out/a.txt", "tree-out/deep/b.txt")
    suffix_extents = ("suffix-out/a.gen",)
    literal_extents = ("literal-out/fixed.lock",)
    yield ExtentMappingCase(
        "tree",
        (tree,),
        tuple((path, 0) for path in tree_extents),
        ("tree-docs/note.txt",),
    )
    yield ExtentMappingCase(
        "suffix",
        (suffix,),
        tuple((path, 0) for path in suffix_extents),
        ("suffix-out/a.txt",),
    )
    yield ExtentMappingCase(
        "literal",
        (literal,),
        tuple((path, 0) for path in literal_extents),
        ("literal-out/other.lock",),
    )
    yield ExtentMappingCase(
        "pair",
        (tree, suffix),
        tuple((path, 0) for path in tree_extents)
        + tuple((path, 1) for path in suffix_extents),
        ("pair-docs/note.txt",),
    )


def single_relation_case() -> ExtentMappingCase:
    """Return the case whose one relation marks two changed files as extents."""
    return next(iter(extent_mapping_cases()))


class InputKind(enum.Enum):
    """Which declared input of a relation a changeset also changes."""

    SOURCE = "source"
    GENERATOR = "generator"


@dataclass(frozen=True)
class FlaggedRelationCase:
    """A relation whose extent changes together with one of its declared inputs."""

    input_kind: InputKind
    relation: ExtentRelation
    extent_path: str
    input_path: str


def flagged_relation_cases() -> Iterator[FlaggedRelationCase]:
    """Yield one case per declared input kind a changeset can change beside an extent."""
    relation = _relation("flag", "flag-out/**")
    yield FlaggedRelationCase(
        InputKind.SOURCE, relation, "flag-out/built.txt", "flag-src/input.txt"
    )
    yield FlaggedRelationCase(
        InputKind.GENERATOR, relation, "flag-out/built.txt", "flag-gen/builder.txt"
    )


class EditSite(enum.Enum):
    """Where a declaration differing from the base commit's declaration lives."""

    HEAD = "head"
    WORKING_TREE = "working-tree"


@dataclass(frozen=True)
class DeclarationEditCase:
    """A base declaration and a differing declaration at one edit site.

    The base declaration marks ``base_extent`` as a generated extent; the edited
    declaration replaces that relation with one that marks ``edited_extent`` instead.
    """

    site: EditSite
    base_relation: ExtentRelation
    edited_relation: ExtentRelation
    base_extent: str
    edited_extent: str


def declaration_edit_cases() -> Iterator[DeclarationEditCase]:
    """Yield one case per site at which a declaration can differ from the base commit's."""
    base_relation = _relation("declared-base", "declared-base-out/**")
    edited_relation = _relation("declared-edit", "declared-edit-out/**")
    for site in EditSite:
        yield DeclarationEditCase(
            site,
            base_relation,
            edited_relation,
            "declared-base-out/built.txt",
            "declared-edit-out/built.txt",
        )


@dataclass(frozen=True)
class RegionOutputCase:
    """A region-bounded output beside a whole-file relation that proves the declaration is read."""

    label: str
    region: RegionRelation
    region_path: str
    control: ExtentRelation
    control_extent: str


def region_output_cases() -> Iterator[RegionOutputCase]:
    """Yield a region-bounded output at the repository root and one in a subdirectory."""
    for label, region_path in (
        ("root", "region-root.md"),
        ("nested", "region-docs/nested.md"),
    ):
        yield RegionOutputCase(
            label=label,
            region=RegionRelation(
                file=region_path,
                begin=f"<!-- BEGIN {label} -->",
                end=f"<!-- END {label} -->",
                sources=(f"region-{label}-src/**",),
                generator=(f"region-{label}-gen/**",),
                regenerate=f"just regenerate-region-{label}",
            ),
            region_path=region_path,
            control=_relation(f"control-{label}", f"control-{label}-out/**"),
            control_extent=f"control-{label}-out/built.txt",
        )


@dataclass(frozen=True)
class RenameCase:
    """A tracked file renamed on the branch, with or without a content change."""

    label: str
    old_path: str
    new_path: str
    content_changed: bool
    companion_path: str


def pure_rename_case() -> RenameCase:
    """Return the case that renames a file and leaves its content unchanged."""
    return RenameCase(
        "pure", "moved/old-name.txt", "moved/new-name.txt", False, "moved/companion.txt"
    )


def modified_rename_case() -> RenameCase:
    """Return the case that renames a file and changes its content."""
    return RenameCase(
        "modified",
        "moved/old-name.txt",
        "moved/new-name.txt",
        True,
        "moved/companion.txt",
    )


@dataclass(frozen=True)
class UnreadSetCase:
    """Changed files the review leaves unread, and the one it reads."""

    unread: tuple[str, ...]
    read: str


def unread_set_case() -> UnreadSetCase:
    """Return a case whose unread set is too large to type as separate arguments by hand."""
    return UnreadSetCase(
        unread=tuple(f"batch/file-{index:02d}.txt" for index in range(UNREAD_SET_SIZE)),
        read="batch/read.txt",
    )
