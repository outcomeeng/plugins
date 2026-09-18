"""Generated request and record domains for the agent-mail adapter evidence."""

from __future__ import annotations

from itertools import combinations
from types import ModuleType

from hypothesis import strategies as st


def _identity_text(minimum: int = 1, maximum: int = 40) -> st.SearchStrategy[str]:
    return st.from_regex(
        rf"[A-Za-z][A-Za-z0-9_-]{{{minimum - 1},{maximum - 1}}}", fullmatch=True
    )


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
        correlation=st.one_of(coordination_references(), _identity_text()),
        sender=_identity_text(),
        recipient=_identity_text(),
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
    raise AssertionError(f"Source operation contract has no generator for {field_name}")


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


def diagnosis_payloads(
    module: ModuleType,
) -> st.SearchStrategy[tuple[dict[str, object], str | None]]:
    """The spec's two diagnosis shapes: a main checkout path, or none."""

    def with_path(path: str) -> tuple[dict[str, object], str | None]:
        return (
            {
                module.CHECKS_FIELD: [
                    {
                        module.NAME_FIELD: module.WORKTREE_POOL_CHECK,
                        module.READINGS_FIELD: {module.MAIN_CHECKOUT_PATH_FIELD: path},
                    }
                ]
            },
            path,
        )

    def without_path(shape: str, path: str) -> tuple[dict[str, object], str | None]:
        if shape == "no-record":
            return ({module.CHECKS_FIELD: []}, None)
        if shape == "other-record":
            return (
                {
                    module.CHECKS_FIELD: [
                        {
                            module.NAME_FIELD: f"other-{path.strip('/')}",
                            module.READINGS_FIELD: {
                                module.MAIN_CHECKOUT_PATH_FIELD: path
                            },
                        }
                    ]
                },
                None,
            )
        return (
            {
                module.CHECKS_FIELD: [
                    {
                        module.NAME_FIELD: module.WORKTREE_POOL_CHECK,
                        module.READINGS_FIELD: {},
                    }
                ]
            },
            None,
        )

    return st.one_of(
        project_key_paths().map(with_path),
        st.builds(
            without_path,
            st.sampled_from(("no-record", "other-record", "empty-readings")),
            project_key_paths(),
        ),
    )
