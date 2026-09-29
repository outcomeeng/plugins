"""Requests the audit-change runner's request contract refuses.

The runner contract in the audit-change ``SKILL.md`` declares a request as one
JSON object that names one listed operation, carries exactly the fields that
operation takes, and gives each field its declared form: ``path``,
``candidateSha256``, ``runToken``, and ``terminalStatus`` are non-empty strings;
a path, a ``runToken``, and a payload ``unitId`` carry no NUL character and no
text without a UTF-8 encoding; every operation except ``resolve-reference``
names a normalized repository-relative candidate path; a payload is an object
with a non-empty ``unitId``; a finding ``rule`` is a lowercase hyphenated ID;
``ordinal`` is an integer within the declared bounds; ``terminalStatus`` is a
listed terminal status.

A request text is also outside the contract when the runner cannot parse it
as one JSON object: a truncated object, a JSON value of another type, or an
object carrying an integer literal longer than the interpreter converts.

Every strategy builds a request outside that contract by construction, taking
every operation, field, bound, and character from the runner's own registries
and constants. None of them consults the runner's acceptance check, so the
refusal a linked test observes is never the generator's own verdict.
"""

from __future__ import annotations

import json
import string
import sys
from types import ModuleType
from typing import Final

from hypothesis import strategies as st

_PATH_SEPARATOR = "/"
_SEGMENT_ALPHABET = string.ascii_letters + string.digits + "-_"
# A path segment the contract refuses in a candidate path: the current
# directory, the parent directory, or an empty segment between separators.
_UNFIT_SEGMENTS = (".", "..", "")
_SURROGATE_CATEGORY: Final = "Cs"
_MAX_MEMBERS = 3
_MAX_LEAVES = 8
# How far past the interpreter's integer conversion limit a generated literal runs.
_MAX_EXCESS_DIGITS = 64
_NONZERO_DIGITS = string.digits[1:]
_INTEGER_SIGNS = ("", "-")
_MEMBER_SEPARATOR = ": "
_ITEM_SEPARATOR = ", "
_OBJECT_TEMPLATE = "{{{}}}"


def json_values() -> st.SearchStrategy[object]:
    """Generate any JSON value: scalars, arrays, and objects, nested."""
    scalars = st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
    )
    return st.recursive(
        scalars,
        lambda children: st.one_of(
            st.lists(children, max_size=_MAX_MEMBERS),
            st.dictionaries(st.text(), children, max_size=_MAX_MEMBERS),
        ),
        max_leaves=_MAX_LEAVES,
    )


def _non_strings() -> st.SearchStrategy[object]:
    return json_values().filter(lambda value: not isinstance(value, str))


def _not_non_empty_strings() -> st.SearchStrategy[object]:
    """Values that are not a non-empty string, the empty string included."""
    return st.one_of(_non_strings(), st.just(""))


def _text_without_system_form(runner: ModuleType) -> st.SearchStrategy[str]:
    """Text carrying the runner's NUL or a character with no encoding in its text encoding."""
    defect = st.one_of(
        st.just(runner.NUL),
        st.characters(categories=[_SURROGATE_CATEGORY]),
    )
    return st.builds(
        lambda head, character, tail: f"{head}{character}{tail}",
        st.text(),
        defect,
        st.text(),
    )


def _unfit_candidate_paths() -> st.SearchStrategy[str]:
    """Paths that are absolute, parent-traversing, or unnormalized."""
    segments = st.lists(
        st.text(alphabet=_SEGMENT_ALPHABET, min_size=1), min_size=1, max_size=4
    )

    @st.composite
    def with_unfit_segment(draw: st.DrawFn) -> str:
        parts = draw(segments)
        index = draw(st.integers(min_value=0, max_value=len(parts)))
        unfit = draw(st.sampled_from(_UNFIT_SEGMENTS))
        return _PATH_SEPARATOR.join([*parts[:index], unfit, *parts[index:]])

    rooted = segments.map(lambda parts: _PATH_SEPARATOR + _PATH_SEPARATOR.join(parts))
    return st.one_of(with_unfit_segment(), rooted)


def _non_rule_ids(runner: ModuleType) -> st.SearchStrategy[object]:
    """Values that are not a lowercase hyphenated ID in the runner's alphabet."""
    alphabet = runner.RULE_ID_ALPHABET
    separator = runner.RULE_ID_SEPARATOR
    id_text = st.text(alphabet=alphabet + separator)
    foreign = st.characters().filter(
        lambda character: character not in alphabet + separator
    )
    with_foreign = st.builds(
        lambda head, character, tail: f"{head}{character}{tail}",
        id_text,
        foreign,
        id_text,
    )
    part = st.text(alphabet=alphabet, min_size=1)
    misplaced_separator = st.one_of(
        part.map(lambda text: separator + text),
        part.map(lambda text: text + separator),
        st.builds(lambda head, tail: f"{head}{separator * 2}{tail}", part, part),
    )
    return st.one_of(_not_non_empty_strings(), with_foreign, misplaced_separator)


def _malformed_payloads(
    runner: ModuleType, operation: object
) -> st.SearchStrategy[object]:
    """Payloads that are not an object with a well-formed ``unitId`` and rule."""
    unit_id = runner.SpxField.UNIT_ID.value
    rule = runner.SpxField.RULE.value
    other_members = st.dictionaries(
        st.text().filter(lambda key: key not in {unit_id, rule}),
        json_values(),
        max_size=_MAX_MEMBERS,
    )
    not_objects = json_values().filter(lambda value: not isinstance(value, dict))
    bad_unit_ids = st.one_of(
        _not_non_empty_strings(), _text_without_system_form(runner)
    )
    with_bad_unit_id = st.builds(
        lambda members, value: {**members, unit_id: value},
        other_members,
        bad_unit_ids,
    )
    payloads = st.one_of(not_objects, other_members, with_bad_unit_id)
    if operation == runner.Operation.ADD_FINDING:
        with_bad_rule = st.builds(
            lambda members, unit, value: {**members, unit_id: unit, rule: value},
            other_members,
            st.text(min_size=1),
            _non_rule_ids(runner),
        )
        payloads = st.one_of(payloads, with_bad_rule)
    return payloads


def _malformed_values(
    runner: ModuleType, operation: object, field: object
) -> st.SearchStrategy[object]:
    """Values outside the declared form of ``field`` in a request for ``operation``."""
    fields = runner.RequestField
    if field == fields.PATH:
        paths = st.one_of(_not_non_empty_strings(), _text_without_system_form(runner))
        if operation != runner.Operation.RESOLVE_REFERENCE:
            paths = st.one_of(paths, _unfit_candidate_paths())
        return paths
    if field == fields.RUN_TOKEN:
        return st.one_of(_not_non_empty_strings(), _text_without_system_form(runner))
    if field == fields.CANDIDATE_SHA256:
        return _not_non_empty_strings()
    if field == fields.TERMINAL_STATUS:
        listed = {status.value for status in runner.TerminalStatus}
        return st.one_of(
            _not_non_empty_strings(),
            st.text(min_size=1).filter(lambda text: text not in listed),
        )
    if field == fields.ORDINAL:
        return st.one_of(
            json_values().filter(
                lambda value: not isinstance(value, int) or isinstance(value, bool)
            ),
            st.integers(max_value=runner.MIN_FINDING_ORDINAL - 1),
            st.integers(min_value=runner.MAX_FINDING_ORDINAL + 1),
        )
    if field == fields.PAYLOAD:
        return _malformed_payloads(runner, operation)
    raise ValueError(f"no declared form for request field {field!r}")


def _unlisted_operation_requests(
    runner: ModuleType,
) -> st.SearchStrategy[dict[str, object]]:
    """Objects whose ``operation`` is absent or names no listed operation."""
    operation_field = runner.RequestField.OPERATION.value
    listed = {operation.value for operation in runner.Operation}
    other_fields = st.dictionaries(
        st.sampled_from([field.value for field in runner.RequestField]).filter(
            lambda name: name != operation_field
        ),
        json_values(),
        max_size=_MAX_MEMBERS,
    )
    unlisted = st.one_of(
        _non_strings(), st.text().filter(lambda name: name not in listed)
    )
    named = st.builds(
        lambda fields, name: {**fields, operation_field: name}, other_fields, unlisted
    )
    return st.one_of(named, other_fields)


@st.composite
def _wrong_field_set_requests(draw: st.DrawFn, runner: ModuleType) -> dict[str, object]:
    """Objects naming a listed operation with a field missing or one it does not take."""
    operation = draw(st.sampled_from(tuple(runner.Operation)))
    operation_field = runner.RequestField.OPERATION.value
    required = sorted(field.value for field in runner.REQUIRED_FIELDS[operation])
    taken = {*required, operation_field}
    dropped = draw(st.sets(st.sampled_from(required))) if required else set()
    undeclared = st.one_of(
        st.sampled_from(
            [field.value for field in runner.RequestField if field.value not in taken]
        ),
        st.text().filter(lambda name: name not in taken),
    )
    extra = draw(
        st.sets(undeclared, min_size=0 if dropped else 1, max_size=_MAX_MEMBERS)
    )
    present = [name for name in required if name not in dropped] + sorted(extra)
    values = draw(st.fixed_dictionaries({name: json_values() for name in present}))
    return {**values, operation_field: operation.value}


@st.composite
def _malformed_field_requests(draw: st.DrawFn, runner: ModuleType) -> dict[str, object]:
    """Objects carrying exactly an operation's fields, one outside its declared form."""
    operation = draw(
        st.sampled_from(
            [
                operation
                for operation in runner.Operation
                if runner.REQUIRED_FIELDS[operation]
            ]
        )
    )
    required = sorted(runner.REQUIRED_FIELDS[operation], key=str)
    malformed = draw(st.sampled_from(required))
    others = draw(
        st.fixed_dictionaries(
            {field.value: json_values() for field in required if field != malformed}
        )
    )
    value = draw(_malformed_values(runner, operation, malformed))
    return {
        **others,
        malformed.value: value,
        runner.RequestField.OPERATION.value: operation.value,
    }


def malformed_request_objects(
    runner: ModuleType,
) -> st.SearchStrategy[dict[str, object]]:
    """Generate JSON objects the runner's request contract refuses."""
    return st.one_of(
        _unlisted_operation_requests(runner),
        _wrong_field_set_requests(runner),
        _malformed_field_requests(runner),
    )


@st.composite
def _truncated_request_texts(draw: st.DrawFn, runner: ModuleType) -> str:
    """A proper prefix of a serialized request object, which lacks its closing brace."""
    request = draw(
        st.dictionaries(
            st.sampled_from([field.value for field in runner.RequestField]),
            json_values(),
            max_size=len(runner.RequestField),
        )
    )
    text = json.dumps(request)
    return text[: draw(st.integers(min_value=0, max_value=len(text) - 1))]


@st.composite
def _oversized_integer_request_texts(draw: st.DrawFn, runner: ModuleType) -> str:
    """A request object text with one member an integer literal too long to convert.

    The interpreter refuses to convert an integer literal with more digits
    than its conversion limit, so the text parses as no JSON value there
    although its syntax is one JSON object.
    """
    field_names = [field.value for field in runner.RequestField]
    oversized = draw(st.sampled_from(field_names))
    others = draw(
        st.dictionaries(
            st.sampled_from([name for name in field_names if name != oversized]),
            json_values(),
            max_size=_MAX_MEMBERS,
        )
    )
    digit_count = _integer_digit_limit() + draw(
        st.integers(min_value=1, max_value=_MAX_EXCESS_DIGITS)
    )
    leading = draw(st.sampled_from(_NONZERO_DIGITS))
    filler = draw(st.sampled_from(string.digits))
    sign = draw(st.sampled_from(_INTEGER_SIGNS))
    literal = f"{sign}{leading}{filler * (digit_count - 1)}"
    member = f"{json.dumps(oversized)}{_MEMBER_SEPARATOR}{literal}"
    return _OBJECT_TEMPLATE.format(
        _ITEM_SEPARATOR.join(
            [
                *(
                    f"{json.dumps(name)}{_MEMBER_SEPARATOR}{json.dumps(value)}"
                    for name, value in others.items()
                ),
                member,
            ]
        )
    )


def _integer_digit_limit() -> int:
    """The interpreter's integer conversion digit limit, or its default when disabled."""
    return sys.get_int_max_str_digits() or sys.int_info.default_max_str_digits


def unparseable_request_texts(runner: ModuleType) -> st.SearchStrategy[str]:
    """Generate request texts the runner cannot parse as one JSON object."""
    other_values = json_values().filter(lambda value: not isinstance(value, dict))
    return st.one_of(
        other_values.map(json.dumps),
        _truncated_request_texts(runner),
        _oversized_integer_request_texts(runner),
    )
