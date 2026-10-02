"""Native-profile evidence against the installed Codex app-server.

The installed Codex CLI is an acquired executable, so these cases sit at the
`l2` floor: each reads disposable, empty native state through the real
app-server and launches no model turn.
"""

import json

from outcomeeng.distribution.native_thread_evidence import (
    THREAD_READ_FAILED,
    NativeLookupField,
    NativeResponseField,
)
from outcomeeng_testing.harnesses.native_thread_evidence import (
    read_absent_native_child,
    read_absent_native_thread,
)


def test_real_native_read_reports_absent_thread_without_launching_a_turn() -> None:
    result = read_absent_native_thread()
    assert result.exit_code != 0
    assert THREAD_READ_FAILED in result.stderr


def test_real_native_child_listing_retains_empty_pages_without_launching() -> None:
    result = read_absent_native_child()
    document = json.loads(result.stdout)
    assert result.exit_code == 0
    assert document[NativeLookupField.CHILD_IDS] == []
    assert document[NativeLookupField.PAGES]
    assert all(
        NativeResponseField.RESULT in page for page in document[NativeLookupField.PAGES]
    )
