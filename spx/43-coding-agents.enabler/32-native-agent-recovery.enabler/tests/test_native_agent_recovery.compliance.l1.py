import pytest

from outcomeeng_testing.generators.native_agent_recovery import (
    NON_ABSOLUTE_WRITABLE_ROOTS,
    VERBATIM_WRITABLE_ROOTS,
)
from outcomeeng_testing.harnesses.native_agent_recovery import (
    observe_writable_root_recovery,
    recovery_result_status,
    rootless_agent_types,
    verify_native_agent_recovery_compliance,
    writable_root_agent_types,
)


def test_native_agent_recovery_compliance() -> None:
    assert verify_native_agent_recovery_compliance() == []


def test_recovery_preserves_each_absolute_root_verbatim_and_records_none() -> None:
    observation = observe_writable_root_recovery(
        {
            agent_type: VERBATIM_WRITABLE_ROOTS
            for agent_type in writable_root_agent_types()
        }
    )

    assert observation.error_status is None
    assert any(launch.roots for launch in observation.launches)
    for launch in observation.launches:
        base = (*launch.resume_prefix, launch.resume_locator)
        assert launch.command[len(base) :][1::2] == launch.roots
    assert observation.prepared_after == observation.prepared_before
    for root in VERBATIM_WRITABLE_ROOTS:
        assert root not in observation.prepared_after


@pytest.mark.parametrize("root", NON_ABSOLUTE_WRITABLE_ROOTS)
def test_recovery_rejects_a_non_absolute_root_before_any_launch(root: str) -> None:
    observation = observe_writable_root_recovery(
        {
            agent_type: ("/srv/absolute-root", root)
            for agent_type in writable_root_agent_types()
        }
    )

    assert observation.error_status == recovery_result_status().INVALID_SCHEMA
    assert observation.launches == ()


@pytest.mark.parametrize("agent_type", rootless_agent_types())
def test_recovery_launches_nothing_for_an_agent_type_that_accepts_no_root(
    agent_type: str,
) -> None:
    observation = observe_writable_root_recovery({agent_type: ("/srv/supplied-root",)})

    assert observation.error_status == recovery_result_status().INVALID_TARGET
    assert observation.launches == ()


@pytest.mark.parametrize("agent_type", rootless_agent_types())
def test_recovery_reports_an_occupied_pane_before_a_rootless_agent_root_rejection(
    agent_type: str,
) -> None:
    observation = observe_writable_root_recovery(
        {agent_type: ("/srv/supplied-root",)}, occupy_first_pane=True
    )

    assert observation.error_status is None
    assert observation.plan_status == recovery_result_status().PANE_OCCUPIED
    assert observation.launches == ()
