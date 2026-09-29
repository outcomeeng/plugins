"""Model identifiers no selected profile owns, derived from the owned identities.

Three construction laws vary the owned identifiers systematically, so the
domain follows every model the owning module adds:

- every single-digit edit of an owned identifier's version, the shape a newer
  or older release of an owned model takes;
- every owned Claude identifier with its family replaced by another Claude
  family, the shape of a model from a family no profile selects;
- every owned Claude identifier with its family replaced by a word of another
  owned identifier that names no Claude family, the shape of a model from a
  family the owning module does not know.

Every member lies outside the owned identities, which is the whole domain the
configuration guard must still detect without a second model inventory.
"""

from itertools import groupby
from string import digits

from outcomeeng.models import CLAUDE_MODEL_FAMILIES, MODEL_IDENTIFIERS, ClaudeModel


def _version_edits(identifier: str) -> set[str]:
    return {
        identifier[:index] + digit + identifier[index + 1 :]
        for index, character in enumerate(identifier)
        if character.isdigit()
        for digit in digits
        if digit != character
    }


def _family_of(identifier: str) -> str:
    return next(family for family in CLAUDE_MODEL_FAMILIES if family in identifier)


def _words(identifier: str) -> set[str]:
    return {
        "".join(run) for is_alpha, run in groupby(identifier, str.isalpha) if is_alpha
    }


def _family_substitutions(replacements: frozenset[str]) -> set[str]:
    return {
        str(model).replace(_family_of(model), replacement, 1)
        for model in ClaudeModel
        for replacement in replacements
    }


def unowned_model_identifiers() -> tuple[str, ...]:
    """Return every identifier the construction laws derive outside the owned set."""
    foreign_words = frozenset(
        word for identifier in MODEL_IDENTIFIERS for word in _words(identifier)
    ).difference(CLAUDE_MODEL_FAMILIES)
    derived = (
        {
            edit
            for identifier in MODEL_IDENTIFIERS
            for edit in _version_edits(identifier)
        }
        | _family_substitutions(CLAUDE_MODEL_FAMILIES)
        | _family_substitutions(foreign_words)
    )
    return tuple(sorted(derived - MODEL_IDENTIFIERS))
