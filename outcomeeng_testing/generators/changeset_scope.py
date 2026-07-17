"""Variable input domains for changeset-scope and merge-classifier evidence."""

from __future__ import annotations

import itertools
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class ChangesetScopeCase:
    """Generated branch and path inputs for one synthetic Git topology."""

    base_branch: str
    feature_branch: str
    initial_file: str
    merged_file: str
    feature_file: str
    working_file: str


def changeset_scope_cases() -> Iterator[ChangesetScopeCase]:
    """Generate reproducible branch and path alternatives without a fixed case bag."""
    for index in itertools.count():
        token = format(index, "x")
        yield ChangesetScopeCase(
            base_branch=f"base-{token}",
            feature_branch=f"feature/{token}",
            initial_file=f"initial/{token}.txt",
            merged_file=f"merged/{token}.txt",
            feature_file=f"feature/{token}.txt",
            working_file=f"working-{token}.py",
        )
