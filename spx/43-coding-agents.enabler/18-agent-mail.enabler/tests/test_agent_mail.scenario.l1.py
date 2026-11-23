from typing import cast

from outcomeeng_testing.harnesses.agent_mail import (
    common_dir_seeded_runner,
    load_agent_mail,
    store_response_payload,
    store_response_result,
)

PROJECT_KEY = "/repository/pool.git"


def test_the_registrations_operation_lists_each_captured_registration() -> None:
    module = load_agent_mail()
    operation = module.Operation.REGISTRATIONS
    listing = cast(list[dict[str, object]], store_response_payload(module, operation))
    runner = common_dir_seeded_runner(
        module, PROJECT_KEY, store_response_result(module, operation)
    )

    result = module.execute(module.operation_request(operation), runner)

    assert result[module.STATUS_FIELD] == module.ExecutionStatus.SUCCEEDED
    assert result[module.PROJECT_KEY_FIELD] == PROJECT_KEY
    data = cast(dict[str, object], result[module.DATA_FIELD])
    assert data[module.REGISTRATIONS_FIELD] == [
        {
            module.AGENT_FIELD: entry[module.STORE_NAME_FIELD],
            module.DISPLAY_NAME_FIELD: entry.get(module.STORE_DISPLAY_NAME_FIELD),
        }
        for entry in listing
    ]
    store_commands = [argv for argv, _ in runner.calls[1:]]
    listing_prefix = module.PUBLIC_AM_COMMAND_PREFIXES[operation]
    assert [argv[: len(listing_prefix)] for argv in store_commands] == [listing_prefix]
    writing_prefixes = {
        module.PUBLIC_AM_COMMAND_PREFIXES[writer]
        for writer in (
            module.Operation.REGISTER,
            module.Operation.SEND,
            module.Operation.READ,
            module.Operation.ACKNOWLEDGE,
        )
    }
    assert listing_prefix not in writing_prefixes
