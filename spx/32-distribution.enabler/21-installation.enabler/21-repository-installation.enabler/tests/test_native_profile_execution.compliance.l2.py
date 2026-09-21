"""Compliance evidence for native app-server reads against the installed Codex CLI."""

import json

from outcomeeng.distribution.native_thread_evidence import THREAD_READ_FAILED
from outcomeeng_testing.harnesses.installation import runs_real_codex
from outcomeeng_testing.harnesses.native_thread_evidence import (
    read_absent_native_child,
    read_absent_native_thread,
)


@runs_real_codex
def test_real_native_read_reports_absent_thread_without_launching_a_turn() -> None:
    result = read_absent_native_thread()
    assert result.exit_code != 0
    assert THREAD_READ_FAILED in result.stderr


@runs_real_codex
def test_real_native_child_listing_retains_empty_pages_without_launching() -> None:
    result = read_absent_native_child()
    assert result.exit_code == 0
    assert json.loads(result.stdout)["childIds"] == []
    assert all("result" in page for page in json.loads(result.stdout)["pages"])
