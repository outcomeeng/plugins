"""Compliance evidence: the owned-path alphabet excludes glob magic."""

from __future__ import annotations

import glob
from pathlib import Path
from string import printable

from outcomeeng_evals.definition import OWNED_PATH_ALPHABET, OWNED_PATHS_FIELD
from outcomeeng_testing.harnesses.eval_definition import (
    load_written_definition,
    valid_required_fields,
)


def test_owned_path_alphabet_excludes_every_glob_magic_character(
    tmp_path: Path,
) -> None:
    magic = tuple(character for character in printable if glob.has_magic(character))
    assert magic

    for index, character in enumerate(magic):
        assert OWNED_PATH_ALPHABET.fullmatch(character) is None
        loaded = load_written_definition(
            tmp_path / str(index),
            {
                **valid_required_fields(),
                OWNED_PATHS_FIELD: [f"src{character}nested"],
            },
        )

        assert loaded.definition is None
        assert OWNED_PATHS_FIELD in str(loaded.error)
