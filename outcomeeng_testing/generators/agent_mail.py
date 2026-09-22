"""Generated request and record domains for the agent-mail adapter evidence."""

from __future__ import annotations

from itertools import combinations
from types import ModuleType

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


def store_message_ids() -> st.SearchStrategy[int]:
    return st.integers(min_value=1, max_value=1_000_000)


def sent_record_kinds(module: ModuleType) -> st.SearchStrategy[object]:
    return st.sampled_from(sorted(module.SENT_KINDS, key=str))


def terminal_record_kinds(module: ModuleType) -> st.SearchStrategy[object]:
    return st.sampled_from(sorted(module.TERMINAL_KINDS, key=str))


def message_records(module: ModuleType) -> st.SearchStrategy[dict[str, object]]:
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
        correlation=st.one_of(coordination_references(), agent_names()),
        sender=agent_names(),
        recipient=agent_names(),
        subject=message_texts(),
        body=message_texts(),
        ack_required=st.booleans(),
    )


def message_record_input(
    module: ModuleType, ordinal: int, kind: object
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
        module.ACK_REQUIRED_FIELD: ordinal % 2 == 0,
    }


def _request_argument_value(
    module: ModuleType, field_name: str, ordinal: int
) -> object:
    if field_name in module.TEXT_ARGUMENT_FIELDS:
        return f"generated-{field_name}-{ordinal}"
    if field_name in module.INTEGER_BOUNDS:
        return module.INTEGER_BOUNDS[field_name][0]
    if field_name in module.BOOLEAN_ARGUMENT_FIELDS:
        return True
    raise RequestContractError(
        f"Source operation contract has no generator for {field_name}"
    )


def operation_requests(module: ModuleType) -> list[dict[str, object]]:
    """Every operation × request shape × optional subset the registry declares."""
    argument_names = {field: name for name, field in module.ARGUMENT_NAMES.items()}
    requests: list[dict[str, object]] = []
    ordinal = 0
    for operation in module.Operation:
        contract = module.OPERATION_CONTRACTS[operation]
        for shape in contract.request_shapes:
            optional_fields = tuple(sorted(shape.optional_fields))
            for subset_size in range(len(optional_fields) + 1):
                for optional_subset in combinations(optional_fields, subset_size):
                    fields = shape.required_fields | frozenset(optional_subset)
                    if module.RECORD_FIELD in fields:
                        for kind in sorted(module.SENT_KINDS, key=str):
                            ordinal += 1
                            record = message_record_input(module, ordinal, kind)
                            requests.append(
                                module.operation_request(
                                    operation,
                                    **{argument_names[module.RECORD_FIELD]: record},
                                )
                            )
                        continue
                    ordinal += 1
                    arguments = {
                        argument_names[field_name]: _request_argument_value(
                            module, field_name, ordinal
                        )
                        for field_name in fields
                    }
                    requests.append(module.operation_request(operation, **arguments))
    return requests


def project_key_paths() -> st.SearchStrategy[str]:
    """Absolute paths a repository's common Git directory takes.

    Every segment opens with an alphanumeric, so no generated path carries a
    `.` or `..` segment and each one is already the key its shapes resolve.
    """
    return st.from_regex(
        r"/[a-z0-9]{1,12}(?:/[a-z0-9][a-z0-9._-]{0,15}){0,5}", fullmatch=True
    )


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
