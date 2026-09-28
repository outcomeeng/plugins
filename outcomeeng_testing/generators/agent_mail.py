"""Generated request and record domains for the agent-mail adapter evidence."""

from __future__ import annotations

import builtins
import json
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations, product
from types import ModuleType
from typing import cast

from hypothesis import strategies as st


class RequestContractError(RuntimeError):
    """The source operation contract names a field this generator cannot produce."""


def agent_names(minimum: int = 1, maximum: int = 40) -> st.SearchStrategy[str]:
    """Agent names and other store identities the mail store admits."""
    return st.from_regex(
        rf"[A-Za-z][A-Za-z0-9_-]{{{minimum - 1},{maximum - 1}}}", fullmatch=True
    )


def program_names() -> st.SearchStrategy[str]:
    return st.from_regex(r"[a-z][a-z0-9-]{1,24}", fullmatch=True)


def unsupported_operation_names(module: ModuleType) -> st.SearchStrategy[str]:
    """Operation names outside the adapter's registry."""
    known = {operation.value for operation in module.Operation}
    return st.from_regex(r"[a-z][a-z0-9-]{1,24}", fullmatch=True).filter(
        lambda name: name not in known
    )


def store_exit_codes() -> st.SearchStrategy[int]:
    """Nonzero exit codes the store CLI can end with."""
    return st.integers(min_value=1, max_value=255)


def capture_row_ordinals() -> st.SearchStrategy[int]:
    """Ordinals a harness reduces onto the rows of a captured response."""
    return st.integers(min_value=0, max_value=1_000)


def message_texts() -> st.SearchStrategy[str]:
    """Free text a record's subject or body carries, including store-hostile marks."""
    return st.text(min_size=1, max_size=200).filter(lambda text: text.strip() == text)


def coordination_references() -> st.SearchStrategy[str]:
    return st.uuids(version=4).map(str)


def change_identities() -> st.SearchStrategy[str]:
    """Canonical Change identities, `<owner>/<repository>#<number>`.

    The separators a Change identity carries are the characters a coordination
    reference holds that the store's thread alphabet rejects.
    """
    return st.from_regex(
        r"[a-z][a-z0-9-]{0,15}/[a-z][a-z0-9-]{0,15}#[1-9][0-9]{0,5}", fullmatch=True
    )


def correlations(
    module: ModuleType, store_rejected: Sequence[str] = ()
) -> st.SearchStrategy[str]:
    """Correlations a record carries, inside and outside the store's thread alphabet.

    The domain spans identifiers the alphabet admits verbatim, Change
    identities and short arbitrary text it rejects, a correlation that opens
    with the adapter's own encoding prefix, and every correlation the store
    was observed rejecting. Arbitrary text stays short enough that its encoded
    form fits the thread length the store admits.
    """
    branches: list[st.SearchStrategy[str]] = [
        coordination_references(),
        agent_names(),
        change_identities(),
        st.text(min_size=1, max_size=10),
        agent_names().map(lambda name: f"{module.ENCODED_THREAD_PREFIX}{name}"),
    ]
    if store_rejected:
        branches.append(st.sampled_from(list(store_rejected)))
    return st.one_of(branches)


def store_message_ids() -> st.SearchStrategy[int]:
    return st.integers(min_value=1, max_value=1_000_000)


def sent_record_kinds(module: ModuleType) -> st.SearchStrategy[object]:
    return st.sampled_from(sorted(module.SENT_KINDS, key=str))


def terminal_record_kinds(module: ModuleType) -> st.SearchStrategy[object]:
    return st.sampled_from(sorted(module.TERMINAL_KINDS, key=str))


def non_terminal_record_kinds(module: ModuleType) -> st.SearchStrategy[object]:
    """Kinds a sender writes that close no delegation."""
    return st.sampled_from(sorted(module.SENT_KINDS - module.TERMINAL_KINDS, key=str))


def message_records(
    module: ModuleType, correlation: st.SearchStrategy[str] | None = None
) -> st.SearchStrategy[dict[str, object]]:
    """Records over every sent kind with generated identities, text, and ack flag."""
    return st.builds(
        lambda kind, correlation, sender, recipient, subject, body, ack_required: {
            module.RECORD_SCHEMA_FIELD: module.RECORD_SCHEMA_VERSION,
            module.KIND_FIELD: kind,
            module.CORRELATION_FIELD: correlation,
            module.SENDER_FIELD: sender,
            module.RECIPIENT_FIELD: recipient,
            module.RECORD_SUBJECT_FIELD: subject,
            module.BODY_FIELD: body,
            module.ACK_REQUIRED_FIELD: ack_required,
        },
        kind=sent_record_kinds(module),
        correlation=correlations(module) if correlation is None else correlation,
        sender=agent_names(),
        recipient=agent_names(),
        subject=message_texts(),
        body=message_texts(),
        ack_required=st.booleans(),
    )


def _handback_content_domains(
    module: ModuleType,
) -> dict[str, st.SearchStrategy[str]]:
    return {
        module.SENDER_FIELD: agent_names(),
        module.RECIPIENT_FIELD: agent_names(),
        module.RECORD_SUBJECT_FIELD: message_texts(),
        module.BODY_FIELD: message_texts(),
    }


def handback_contents(module: ModuleType) -> st.SearchStrategy[dict[str, str]]:
    """The content fields of a terminal handback, each generated independently."""
    return st.fixed_dictionaries(_handback_content_domains(module))


def conflicting_handback_contents(
    module: ModuleType,
) -> st.SearchStrategy[tuple[dict[str, str], dict[str, str]]]:
    """A handback's content and a second content that differs from it.

    The second content replaces a generated nonempty set of the content fields
    with other values drawn from each field's own domain and keeps the rest, so
    every combination of changed fields is reachable.
    """
    domains = _handback_content_domains(module)

    def other_value(content: dict[str, str], name: str) -> st.SearchStrategy[str]:
        held = content[name]
        return domains[name].filter(lambda value: value != held)

    def changed(content: dict[str, str]) -> st.SearchStrategy[dict[str, str]]:
        return st.sets(st.sampled_from(sorted(domains)), min_size=1).flatmap(
            lambda names: st.fixed_dictionaries(
                {name: other_value(content, name) for name in names}
            ).map(lambda replaced: {**content, **replaced})
        )

    return handback_contents(module).flatmap(
        lambda content: st.tuples(st.just(content), changed(content))
    )


def message_record_input(
    module: ModuleType, ordinal: int, kind: object, *, ack_required: bool
) -> dict[str, object]:
    suffix = str(ordinal)
    return {
        module.RECORD_SCHEMA_FIELD: module.RECORD_SCHEMA_VERSION,
        module.KIND_FIELD: kind,
        module.CORRELATION_FIELD: f"thread-{suffix}",
        module.SENDER_FIELD: f"Sender{suffix}",
        module.RECIPIENT_FIELD: f"Recipient{suffix}",
        module.RECORD_SUBJECT_FIELD: f"generated subject {suffix}",
        module.BODY_FIELD: f"generated body {suffix}",
        module.ACK_REQUIRED_FIELD: ack_required,
    }


def _request_argument_values(
    module: ModuleType, field_name: str, ordinal: int
) -> tuple[object, ...]:
    """Every value one request field takes in the generated domain: one text or
    integer value, and both values of a boolean."""
    if field_name in module.TEXT_ARGUMENT_FIELDS:
        return (f"generated-{field_name}-{ordinal}",)
    if field_name in module.INTEGER_BOUNDS:
        return (module.INTEGER_BOUNDS[field_name][0],)
    if field_name in module.BOOLEAN_ARGUMENT_FIELDS:
        return (True, False)
    raise RequestContractError(
        f"Source operation contract has no generator for {field_name}"
    )


def operation_requests(module: ModuleType) -> list[dict[str, object]]:
    """Every operation × request shape × optional subset the registry declares,
    with every boolean field — optional argument or record flag — in both of
    its values."""
    argument_names = {field: name for name, field in module.ARGUMENT_NAMES.items()}
    requests: list[dict[str, object]] = []
    ordinal = 0
    for operation in module.Operation:
        contract = module.OPERATION_CONTRACTS[operation]
        for shape in contract.request_shapes:
            optional_fields = tuple(sorted(shape.optional_fields))
            for subset_size in range(len(optional_fields) + 1):
                for optional_subset in combinations(optional_fields, subset_size):
                    fields = tuple(
                        sorted(shape.required_fields | frozenset(optional_subset))
                    )
                    if module.RECORD_FIELD in fields:
                        for kind, ack_required in product(
                            sorted(module.SENT_KINDS, key=str), (True, False)
                        ):
                            ordinal += 1
                            record = message_record_input(
                                module, ordinal, kind, ack_required=ack_required
                            )
                            requests.append(
                                module.operation_request(
                                    operation,
                                    **{argument_names[module.RECORD_FIELD]: record},
                                )
                            )
                        continue
                    ordinal += 1
                    for values in product(
                        *(
                            _request_argument_values(module, field_name, ordinal)
                            for field_name in fields
                        )
                    ):
                        arguments = {
                            argument_names[field_name]: value
                            for field_name, value in zip(fields, values, strict=True)
                        }
                        requests.append(
                            module.operation_request(operation, **arguments)
                        )
    return requests


def nul_positions() -> st.SearchStrategy[int]:
    """Where a NUL lands inside a text value, reduced onto its length."""
    return st.integers(min_value=0, max_value=1_000)


def _with_nul(text: str, position: int) -> str:
    index = position % (len(text) + 1)
    return f"{text[:index]}\x00{text[index:]}"


def nul_carrying_requests(
    module: ModuleType, request: dict[str, object], position: int
) -> list[tuple[str, dict[str, object]]]:
    """One variant of ``request`` per text value it carries, that value holding
    a NUL, each named by the location of the value it varies.

    Text values are read off the request itself — every string argument, and
    every string field of a record argument — so the variants cover whatever
    text the request carries rather than a list of fields to check.
    """
    arguments = dict(cast(dict[str, object], request[module.ARGUMENTS_FIELD]))
    variants: list[tuple[str, dict[str, object]]] = []
    for name, value in arguments.items():
        if isinstance(value, str):
            variants.append(
                (
                    name,
                    {
                        **request,
                        module.ARGUMENTS_FIELD: {
                            **arguments,
                            name: _with_nul(value, position),
                        },
                    },
                )
            )
        elif isinstance(value, dict):
            for field_name, field_value in value.items():
                if isinstance(field_value, str):
                    variants.append(
                        (
                            f"{name}.{field_name}",
                            {
                                **request,
                                module.ARGUMENTS_FIELD: {
                                    **arguments,
                                    name: {
                                        **value,
                                        field_name: _with_nul(field_value, position),
                                    },
                                },
                            },
                        )
                    )
    return variants


# Characters a JSON text may open with, after optional whitespace (RFC 8259,
# section 2): the opening of an object, an array, a string, a number, or one
# of the three literal names — widened by the openings of `NaN` and
# `Infinity`, which Python's reader admits beyond the standard.
JSON_VALUE_OPENINGS = frozenset('{["-0123456789tfnNI')
JSON_WHITESPACE = frozenset(" \t\n\r")


# The families of request input that name no request: text that is no JSON,
# JSON nested past the depth the reader can descend, and JSON that parses to
# something other than an object.
UNREADABLE_STRAY_OPENING = "stray-opening"
UNREADABLE_TRUNCATED_OBJECT = "truncated-object"
UNREADABLE_DEEP_ARRAY = "deep-array"
UNREADABLE_NON_OBJECT = "non-object"
UNREADABLE_INPUT_FAMILIES = (
    UNREADABLE_STRAY_OPENING,
    UNREADABLE_TRUNCATED_OBJECT,
    UNREADABLE_DEEP_ARRAY,
    UNREADABLE_NON_OBJECT,
)


class UnreadableInputError(RuntimeError):
    """The named input family is outside the generated domain."""


def unreadable_request_texts(family: str) -> st.SearchStrategy[str]:
    """Request inputs of one family: a text opening with a character no JSON
    value opens with; an object cut off after its first key; an array nesting a
    hundredfold and more past the interpreter's recursion limit, which the
    reader's stack protection refuses to descend whatever its own bound; or a
    JSON text whose value is a scalar or an array."""
    if family == UNREADABLE_STRAY_OPENING:
        return st.tuples(
            st.characters(
                exclude_characters="".join(JSON_VALUE_OPENINGS | JSON_WHITESPACE),
            ),
            st.text(max_size=40),
        ).map(lambda parts: parts[0] + parts[1])
    if family == UNREADABLE_TRUNCATED_OBJECT:
        return st.text(max_size=20).map(lambda key: "{" + json.dumps(key) + ":")
    if family == UNREADABLE_DEEP_ARRAY:
        limit = sys.getrecursionlimit()
        return st.integers(min_value=limit * 100, max_value=limit * 1_000).map(
            lambda depth: "[" * depth
        )
    if family == UNREADABLE_NON_OBJECT:
        scalars = st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=20),
        )
        return st.one_of(scalars, st.lists(scalars, max_size=5)).map(json.dumps)
    raise UnreadableInputError(f"No unreadable input family named {family!r}")


def _constructible_exception_classes() -> list[type[Exception]]:
    """Every builtin exception class a runner could raise with one message."""
    classes: list[type[Exception]] = []
    for value in vars(builtins).values():
        if (
            isinstance(value, type)
            and issubclass(value, Exception)
            and not issubclass(value, Warning)
        ):
            try:
                value("generated")
            except TypeError:
                continue
            classes.append(value)
    return sorted(classes, key=lambda cls: cls.__name__)


class GeneratedRunnerError(Exception):
    """An error class no library defines, so the domain reaches a class the
    adapter cannot have named."""


def runner_errors() -> st.SearchStrategy[Exception]:
    """Errors a command runner raises: every builtin exception class, the
    subprocess module's timeout, and a class no library defines."""
    message = st.text(max_size=40)
    builtin_errors = st.builds(
        lambda cls, text: cls(text),
        st.sampled_from(_constructible_exception_classes()),
        message,
    )
    timeouts = st.builds(
        lambda command, seconds: subprocess.TimeoutExpired(command, seconds),
        st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=4),
        st.floats(min_value=0.001, max_value=600),
    )
    foreign = message.map(GeneratedRunnerError)
    return st.one_of(builtin_errors, timeouts, foreign)


def activity_moments() -> st.SearchStrategy[str]:
    """Timestamps the store can report for an agent, from long past to far
    future, so a reading that judged recency would see both a stale and a
    fresh agent."""
    return st.datetimes(
        min_value=datetime(1970, 1, 2),
        max_value=datetime(2200, 1, 1),
        timezones=st.just(UTC),
    ).map(lambda moment: moment.isoformat().replace("+00:00", "Z"))


def project_key_paths() -> st.SearchStrategy[str]:
    """Absolute paths a repository's common Git directory takes.

    Every segment opens with an alphanumeric, so no generated path carries a
    `.` or `..` segment and each one is already the key its shapes resolve.
    """
    return st.from_regex(
        r"/[a-z0-9]{1,12}(?:/[a-z0-9][a-z0-9._-]{0,15}){0,5}", fullmatch=True
    )


# The shapes a listing row's subject takes, each built from its parts so the
# kind and subject the row must read back as are construction inputs rather
# than a second parse. Only a sent kind between the prefix marks, followed by
# a nonempty remainder, classifies; every other shape reads back unclassified
# with its subject verbatim.
SUBJECT_CLASSIFIED = "classified"
SUBJECT_UNPREFIXED = "unprefixed"
SUBJECT_UNKNOWN_KIND = "unknown-kind"
SUBJECT_UNSENT_KIND = "unsent-kind"
SUBJECT_EMPTY_REMAINDER = "empty-remainder"
SUBJECT_UNSEPARATED = "unseparated"
SUBJECT_EMPTY_KIND = "empty-kind"
SUBJECT_BRANCHES = (
    SUBJECT_CLASSIFIED,
    SUBJECT_UNPREFIXED,
    SUBJECT_UNKNOWN_KIND,
    SUBJECT_UNSENT_KIND,
    SUBJECT_EMPTY_REMAINDER,
    SUBJECT_UNSEPARATED,
    SUBJECT_EMPTY_KIND,
)


class SubjectShapeError(RuntimeError):
    """The named subject shape is outside the generated domain."""


@dataclass(frozen=True)
class SubjectShape:
    """A store subject, and the kind and record subject it reads back as."""

    subject: str
    kind: object
    record_subject: str


def subject_shapes(module: ModuleType, branch: str) -> st.SearchStrategy[SubjectShape]:
    """Subjects of one shape, each carrying the kind and subject it reads as."""
    opening = module.KIND_PREFIX_OPEN
    closing = module.KIND_PREFIX_CLOSE
    unclassified = module.RecordKind.UNCLASSIFIED
    kinds = {kind.value for kind in module.RecordKind}

    def verbatim(subject: str) -> SubjectShape:
        return SubjectShape(subject, unclassified, subject)

    def prefixed(
        build: Callable[[str, str], str],
    ) -> Callable[[tuple[object, str]], SubjectShape]:
        return lambda parts: verbatim(build(str(parts[0]), parts[1]))

    if branch == SUBJECT_CLASSIFIED:
        return st.tuples(sent_record_kinds(module), message_texts()).map(
            lambda parts: SubjectShape(
                f"{opening}{parts[0]}{closing}{parts[1]}", parts[0], parts[1]
            )
        )
    if branch == SUBJECT_UNPREFIXED:
        return (
            message_texts()
            .filter(lambda text: not text.startswith(opening))
            .map(verbatim)
        )
    if branch == SUBJECT_UNKNOWN_KIND:
        tokens = st.from_regex(r"[a-z][a-z-]{0,20}", fullmatch=True).filter(
            lambda token: token not in kinds
        )
        return st.tuples(tokens, message_texts()).map(
            prefixed(lambda token, rest: f"{opening}{token}{closing}{rest}")
        )
    if branch == SUBJECT_UNSENT_KIND:
        unsent = sorted(set(module.RecordKind) - module.SENT_KINDS, key=str)
        return st.tuples(st.sampled_from(unsent), message_texts()).map(
            prefixed(lambda kind, rest: f"{opening}{kind}{closing}{rest}")
        )
    if branch == SUBJECT_EMPTY_REMAINDER:
        return sent_record_kinds(module).map(
            lambda kind: verbatim(f"{opening}{kind}{closing}")
        )
    if branch == SUBJECT_UNSEPARATED:
        return st.tuples(sent_record_kinds(module), message_texts()).map(
            prefixed(lambda kind, rest: f"{opening}{kind}{closing.rstrip()}{rest}")
        )
    if branch == SUBJECT_EMPTY_KIND:
        return message_texts().map(lambda rest: verbatim(f"{opening}{closing}{rest}"))
    raise SubjectShapeError(f"No subject shape named {branch!r}")


# The shapes the repository lookup's output takes, each built from a generated
# canonical key so the key the shape must resolve is its construction input
# rather than a second derivation: the bare value, the value the lookup prints
# with its trailing newline, a trailing separator, a repeated separator, a
# `.` segment, and a detour through a `..` segment each resolve that key; empty
# output, blank output, a `.` alone, and a relative path resolve no repository.
COMMON_DIR_EXACT = "exact"
COMMON_DIR_TRAILING_NEWLINE = "trailing-newline"
COMMON_DIR_TRAILING_SEPARATOR = "trailing-separator"
COMMON_DIR_REPEATED_SEPARATOR = "repeated-separator"
COMMON_DIR_DOT_SEGMENT = "dot-segment"
COMMON_DIR_PARENT_DETOUR = "parent-detour"
COMMON_DIR_EMPTY = "empty"
COMMON_DIR_BLANK = "blank"
COMMON_DIR_DOT_ALONE = "dot-alone"
COMMON_DIR_RELATIVE = "relative"
COMMON_DIR_SHAPES = (
    COMMON_DIR_EXACT,
    COMMON_DIR_TRAILING_NEWLINE,
    COMMON_DIR_TRAILING_SEPARATOR,
    COMMON_DIR_REPEATED_SEPARATOR,
    COMMON_DIR_DOT_SEGMENT,
    COMMON_DIR_PARENT_DETOUR,
    COMMON_DIR_EMPTY,
    COMMON_DIR_BLANK,
    COMMON_DIR_DOT_ALONE,
    COMMON_DIR_RELATIVE,
)
# The shapes whose key resolves; every other shape names no repository.
RESOLVING_COMMON_DIR_SHAPES = frozenset(
    {
        COMMON_DIR_EXACT,
        COMMON_DIR_TRAILING_NEWLINE,
        COMMON_DIR_TRAILING_SEPARATOR,
        COMMON_DIR_REPEATED_SEPARATOR,
        COMMON_DIR_DOT_SEGMENT,
        COMMON_DIR_PARENT_DETOUR,
    }
)
DETOUR_SEGMENT = "detour"


class CommonDirShapeError(RuntimeError):
    """The named output shape is outside the generated domain."""


def common_dir_output(shape: str, path: str) -> str:
    """Build the lookup's printed output for one shape around ``path``.

    Every resolving shape is ``path`` written differently, so ``path`` is the
    key each must resolve without any normalization being restated here.
    """
    if shape == COMMON_DIR_EXACT:
        return path
    if shape == COMMON_DIR_TRAILING_NEWLINE:
        return f"{path}\n"
    if shape == COMMON_DIR_TRAILING_SEPARATOR:
        return f"{path}/"
    if shape == COMMON_DIR_REPEATED_SEPARATOR:
        return f"/{path}"
    if shape == COMMON_DIR_DOT_SEGMENT:
        return f"{path}/."
    if shape == COMMON_DIR_PARENT_DETOUR:
        head, _, tail = path.rpartition("/")
        return f"{head}/{DETOUR_SEGMENT}/../{tail}"
    if shape == COMMON_DIR_EMPTY:
        return ""
    if shape == COMMON_DIR_BLANK:
        return " \n\t "
    if shape == COMMON_DIR_DOT_ALONE:
        return "."
    if shape == COMMON_DIR_RELATIVE:
        return path.lstrip("/")
    raise CommonDirShapeError(f"No common-directory shape named {shape!r}")


def expected_project_key(shape: str, path: str) -> str | None:
    """The key one shape resolves: the path it was built around, or none."""
    return path if shape in RESOLVING_COMMON_DIR_SHAPES else None
