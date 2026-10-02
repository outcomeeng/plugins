"""Native-profile row evidence against the installed Codex app-server.

The installed Codex CLI is an acquired executable, so these cases sit at the
`l2` floor: each Codex row's child read runs through the real app-server in
the row's disposable state, and no model turn is launched.
"""

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.native_profile_execution import native_profile_rows
from outcomeeng.distribution.native_thread_evidence import NativeEvidenceCondition
from outcomeeng_testing.harnesses.native_profile_launch import (
    native_profile_absent_child,
)


def test_a_row_whose_child_the_real_listing_lacks_records_the_absent_thread_once() -> (
    None
):
    with native_profile_absent_child() as observation:
        assert len(observation.rows) == sum(
            row.target is Target.CODEX for row in native_profile_rows()
        )
        for item in observation.rows:
            row = item.observation.row
            launches = [
                call
                for call in item.calls
                if set(row.launch_commands[0]) <= set(call.argv)
            ]
            assert len(launches) == 1, (row.identifier, launches)
            assert item.observation.launch_exit_code == 0, row.identifier
            assert (
                item.observation.terminal_condition
                == NativeEvidenceCondition.THREAD_ABSENT
            ), row.identifier
            assert row.definition_path.is_file()
            assert row.loading_path.is_file()
            assert row.result_path.is_file()
            assert not row.state_root.exists()
