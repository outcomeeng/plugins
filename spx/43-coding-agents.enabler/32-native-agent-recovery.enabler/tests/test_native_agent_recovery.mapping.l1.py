import pytest

from outcomeeng_testing.generators.native_agent_recovery import (
    NATIVE_HOME_PATH,
    WRITABLE_ROOT_SETS,
)
from outcomeeng_testing.harnesses.native_agent_recovery import (
    native_home_agent_type,
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


@pytest.mark.parametrize("roots", WRITABLE_ROOT_SETS)
def test_recovery_places_supplied_roots_after_the_session_id_of_a_native_home_launch(
    roots: tuple[str, ...],
) -> None:
    home_agent_type = native_home_agent_type()
    observation = observe_writable_root_recovery(
        {agent_type: roots for agent_type in writable_root_agent_types()},
        native_homes_by_agent_type={home_agent_type: NATIVE_HOME_PATH},
    )

    assert observation.error_status is None
    home_launches = [
        launch
        for launch in observation.launches
        if launch.agent_type == home_agent_type
    ]
    assert home_launches
    for launch in home_launches:
        assert launch.native_home == NATIVE_HOME_PATH
        base = (
            "env",
            f"CODEX_HOME={NATIVE_HOME_PATH}",
            *launch.resume_prefix,
            launch.resume_locator,
        )
        assert launch.command[: len(base)] == base
        tail = launch.command[len(base) :]
        assert len(tail) == 2 * len(launch.roots)
        assert len(set(tail[0::2])) <= 1
        assert all(option.startswith("--") for option in tail[0::2])
        assert tail[1::2] == launch.roots
