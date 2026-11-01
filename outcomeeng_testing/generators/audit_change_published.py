"""Requests the audit-change runner's ``read-published`` operation refuses.

The ``changes.md`` assertion for ``read-published`` states its request as
exactly an operation name and a canonical ``<owner>/<repo>#<N>`` issue
identity. Every strategy here builds a ``read-published`` request outside that
statement by construction: a request missing the identity, one carrying a field
besides the two, one whose identity is not a string, and one whose identity
string lacks a part of the canonical form — the ``/`` between owner and
repository, the ``#`` before the number, a number of decimal digits, or an
identity with nothing around it. Operation and field names come from the
runner's own registries. No strategy consults the runner's identity pattern or
acceptance check, so the refusal a linked test observes is never the
generator's own verdict.

``canonical_issue_identities`` supplies the opposite domain: identities in the
canonical form, built from owner and repository names in letters and digits and
a positive decimal number.
"""

from __future__ import annotations

import string
from types import ModuleType
from typing import Final

from hypothesis import strategies as st

from outcomeeng_testing.generators.audit_change_run import json_values

_OWNER_SEPARATOR: Final = "/"
_NUMBER_SEPARATOR: Final = "#"
_NAME_ALPHABET: Final = string.ascii_letters + string.digits
_NONZERO_DIGITS: Final = string.digits[1:]
_MAX_NAME_LENGTH: Final = 12
_MAX_NUMBER_DIGITS: Final = 6
_MAX_EXTRA_FIELDS: Final = 3
# Characters a canonical identity never carries before its owner or after its number.
_PADDING: Final = string.whitespace


def _names() -> st.SearchStrategy[str]:
    return st.text(alphabet=_NAME_ALPHABET, min_size=1, max_size=_MAX_NAME_LENGTH)


def _numbers() -> st.SearchStrategy[str]:
    return st.builds(
        lambda leading, rest: f"{leading}{rest}",
        st.sampled_from(_NONZERO_DIGITS),
        st.text(alphabet=string.digits, max_size=_MAX_NUMBER_DIGITS - 1),
    )


def canonical_issue_identities() -> st.SearchStrategy[str]:
    """Generate issue identities in the canonical ``<owner>/<repo>#<N>`` form."""
    return st.builds(
        lambda owner, repository, number: (
            f"{owner}{_OWNER_SEPARATOR}{repository}{_NUMBER_SEPARATOR}{number}"
        ),
        _names(),
        _names(),
        _numbers(),
    )


def _noncanonical_identity_strings() -> st.SearchStrategy[str]:
    """Strings that lack a part of the canonical identity form."""
    without_owner_separator = st.text(
        alphabet=st.characters(exclude_characters=_OWNER_SEPARATOR)
    )
    without_number_separator = st.text(
        alphabet=st.characters(exclude_characters=_NUMBER_SEPARATOR)
    )
    non_decimal_number = st.builds(
        lambda owner, repository, number: (
            f"{owner}{_OWNER_SEPARATOR}{repository}{_NUMBER_SEPARATOR}{number}"
        ),
        _names(),
        _names(),
        st.text(alphabet=string.ascii_letters, min_size=1),
    )
    padded = st.builds(
        lambda before, identity, after: f"{before}{identity}{after}",
        st.text(alphabet=_PADDING, min_size=1),
        canonical_issue_identities(),
        st.text(alphabet=_PADDING),
    )
    return st.one_of(
        without_owner_separator, without_number_separator, non_decimal_number, padded
    )


def _request(runner: ModuleType, members: dict[str, object]) -> dict[str, object]:
    return {
        **members,
        runner.RequestField.OPERATION.value: runner.Operation.READ_PUBLISHED.value,
    }


def malformed_published_requests(
    runner: ModuleType,
) -> st.SearchStrategy[dict[str, object]]:
    """Generate ``read-published`` request objects outside the stated request shape."""
    operation_field = runner.RequestField.OPERATION.value
    issue_field = runner.RequestField.ISSUE.value
    taken = {operation_field, issue_field}
    extra_names = st.one_of(
        st.sampled_from(
            [field.value for field in runner.RequestField if field.value not in taken]
        ),
        st.text().filter(lambda name: name not in taken),
    )
    extras = st.dictionaries(
        extra_names, json_values(), min_size=1, max_size=_MAX_EXTRA_FIELDS
    )
    without_issue = st.dictionaries(
        extra_names, json_values(), max_size=_MAX_EXTRA_FIELDS
    ).map(lambda members: _request(runner, members))
    with_extra_field = st.builds(
        lambda members, identity: _request(runner, {**members, issue_field: identity}),
        extras,
        canonical_issue_identities(),
    )
    identity_values = st.one_of(
        json_values().filter(lambda value: not isinstance(value, str)),
        _noncanonical_identity_strings(),
    )
    with_malformed_identity = identity_values.map(
        lambda identity: _request(runner, {issue_field: identity})
    )
    return st.one_of(without_issue, with_extra_field, with_malformed_identity)
