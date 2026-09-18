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
    return st.from_regex(r"/[a-z0-9]{1,12}(?:/[a-z0-9._-]{1,16}){0,5}", fullmatch=True)


# The diagnosis shapes the adapter decision names, each a variant of the
# captured `spx diagnose --format json` response: the capture with a generated
# absolute main checkout path resolves the key; no worktree-pool record, a
# record under another name, two records, empty readings, a relative path, a
# payload that is not an object, no check list, and a check list that is not
# an array each yield the unavailable result.
DIAGNOSIS_WITH_PATH = "with-path"
DIAGNOSIS_NO_RECORD = "no-record"
DIAGNOSIS_OTHER_RECORD = "other-record"
DIAGNOSIS_TWO_RECORDS = "two-records"
DIAGNOSIS_EMPTY_READINGS = "empty-readings"
DIAGNOSIS_RELATIVE_PATH = "relative-path"
DIAGNOSIS_NOT_OBJECT = "not-object"
DIAGNOSIS_NO_CHECKS = "no-checks"
DIAGNOSIS_CHECKS_NOT_ARRAY = "checks-not-array"
DIAGNOSIS_SHAPES = (
    DIAGNOSIS_WITH_PATH,
    DIAGNOSIS_NO_RECORD,
    DIAGNOSIS_OTHER_RECORD,
    DIAGNOSIS_TWO_RECORDS,
    DIAGNOSIS_EMPTY_READINGS,
    DIAGNOSIS_RELATIVE_PATH,
    DIAGNOSIS_NOT_OBJECT,
    DIAGNOSIS_NO_CHECKS,
    DIAGNOSIS_CHECKS_NOT_ARRAY,
)
# The one shape whose key resolves; every other shape maps to no key.
RESOLVING_DIAGNOSIS_SHAPES = frozenset({DIAGNOSIS_WITH_PATH})


def expected_project_key(shape: str, path: str) -> str | None:
    """The key the adapter decision derives for one shape: the absolute main
    checkout path of the one worktree-pool record, or none."""
    return path if shape in RESOLVING_DIAGNOSIS_SHAPES else None
