import pytest

from outcomeeng_testing.generators.native_agent_recovery import WRITABLE_ROOT_SETS
from outcomeeng_testing.harnesses.native_agent_recovery import (
    observe_writable_root_recovery,
    verify_native_agent_recovery_mappings,
    writable_root_agent_types,
)


def test_native_agent_recovery_mappings() -> None:
    assert verify_native_agent_recovery_mappings() == []


@pytest.mark.parametrize("roots", WRITABLE_ROOT_SETS)
def test_recovery_maps_supplied_roots_to_one_option_per_root(
    roots: tuple[str, ...],
) -> None:
    observation = observe_writable_root_recovery(
        {agent_type: roots for agent_type in writable_root_agent_types()}
    )

    assert observation.error_status is None
    assert observation.launches
    for launch in observation.launches:
        base = (*launch.resume_prefix, launch.resume_locator)
        assert launch.command[: len(base)] == base
        tail = launch.command[len(base) :]
        assert len(tail) == 2 * len(launch.roots)
        options = tail[0::2]
        assert len(set(options)) <= 1
        assert all(option.startswith("--") for option in options)
        assert tail[1::2] == launch.roots


def test_recovery_maps_an_empty_request_to_commands_with_no_root_option() -> None:
    observation = observe_writable_root_recovery({})

    assert observation.error_status is None
    assert observation.launches
    for launch in observation.launches:
        assert launch.command == (*launch.resume_prefix, launch.resume_locator)
