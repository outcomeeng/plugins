"""Tests for the bundled roster and monitor over controlled session inventories."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import environment  # noqa: E402
import monitor  # noqa: E402
import roster  # noqa: E402

NOW = datetime(2026, 10, 4, 0, 0, tzinfo=timezone.utc)
WATCH = {
    "position": "Director",
    "sessions": [
        {
            "position": "SPX Maintainer",
            "mail_name": "RedOwl",
            "backend": "prowl",
            "cwd": "/w/spx/maintainer",
            "context_percent": 80,
            "stall_minutes": 45,
        },
        {
            "position": "SPX Orchestrator",
            "mail_name": "BlueCrane",
            "backend": "prowl",
            "cwd": "/w/spx/orchestrator",
        },
    ],
    "groups": [
        {
            "label": "Executor",
            "backend": "herdr",
            "cwd_prefix": "/w/spx/worktrees",
            "exclude": [],
        }
    ],
}


def session(
    cwd: str, state: str, backend: str = "prowl", handle: str = "P1"
) -> environment.Session:
    return environment.Session(
        backend=backend, handle=handle, cwd=cwd, state=state, changed_at=None, detail=""
    )


def test_roster_matches_each_position_to_its_live_session_and_marks_the_absent():
    inventories = {
        "prowl": [session("/w/spx/maintainer", "idle")],
        "herdr": [session("/w/spx/worktrees/change-1", "working", "herdr", "change-1")],
    }
    text = roster.render(WATCH, inventories, NOW, read_context=lambda s: "42%")
    assert (
        "| SPX Maintainer | RedOwl | prowl | /w/spx/maintainer | P1 | idle | 42% |"
        in text
    )
    assert (
        "| SPX Orchestrator | BlueCrane | prowl | /w/spx/orchestrator | - | absent | - |"
        in text
    )
    assert (
        "| Executor change-1 | - | herdr | /w/spx/worktrees/change-1 | change-1 | working | 42% |"
        in text
    )


def test_roster_reports_a_failed_inventory_instead_of_absence():
    text = roster.render(
        WATCH,
        {"prowl": "prowl_environment.py: no answer within 30s", "herdr": []},
        NOW,
        read_context=lambda s: "?",
    )
    assert "inventory failed: prowl_environment.py: no answer within 30s" in text
    assert "absent" not in text


def test_roster_rejects_a_watch_file_without_a_position(tmp_path, capsys):
    path = tmp_path / "watch.json"
    path.write_text(json.dumps({"sessions": []}))
    assert roster.main([str(path)]) == 2
    assert "lacks the top-level 'position'" in capsys.readouterr().err


def test_roster_names_a_missing_watch_file(tmp_path, capsys):
    assert roster.main([str(tmp_path / "absent.json")]) == 2
    assert "no watch file at" in capsys.readouterr().err


def poll(
    monkeypatch, inventories: dict, state: dict, text: str = "", now: datetime = NOW
) -> list[str]:
    monkeypatch.setattr(
        environment.BACKENDS["prowl"], "sessions", lambda: inventories.get("prowl", [])
    )
    monkeypatch.setattr(
        environment.BACKENDS["herdr"], "sessions", lambda: inventories.get("herdr", [])
    )
    monkeypatch.setattr(environment.BACKENDS["prowl"], "read", lambda s, lines=15: text)
    monkeypatch.setattr(environment.BACKENDS["herdr"], "read", lambda s, lines=15: text)
    return monitor.poll(WATCH, state, now)


def test_monitor_reports_a_blocked_position_at_once_and_again_after_the_reminder(
    monkeypatch,
):
    state: dict = {}
    first = poll(
        monkeypatch, {"prowl": [session("/w/spx/maintainer", "blocked")]}, state
    )
    assert any("BLOCKED SPX Maintainer" in line for line in first)
    quiet = poll(
        monkeypatch,
        {"prowl": [session("/w/spx/maintainer", "blocked")]},
        state,
        now=NOW + timedelta(minutes=5),
    )
    assert not any("BLOCKED" in line for line in quiet)
    again = poll(
        monkeypatch,
        {"prowl": [session("/w/spx/maintainer", "blocked")]},
        state,
        now=NOW + timedelta(minutes=16),
    )
    assert any(
        "BLOCKED SPX Maintainer" in line and "for 16 min" in line for line in again
    )


def test_monitor_reports_went_idle_only_on_the_working_to_idle_edge(monkeypatch):
    state: dict = {}
    poll(monkeypatch, {"prowl": [session("/w/spx/maintainer", "working")]}, state)
    lines = poll(monkeypatch, {"prowl": [session("/w/spx/maintainer", "idle")]}, state)
    assert any("WENT-IDLE SPX Maintainer" in line for line in lines)
    assert not any(
        "WENT-IDLE" in line
        for line in poll(
            monkeypatch, {"prowl": [session("/w/spx/maintainer", "idle")]}, state
        )
    )


def test_monitor_reports_a_compaction_tier_once_per_five_percent(monkeypatch):
    state: dict = {}
    pane = "(860k/1M tokens) 86%"
    first = poll(
        monkeypatch,
        {"prowl": [session("/w/spx/maintainer", "working")]},
        state,
        text=pane,
    )
    assert any("COMPACT-NOW SPX Maintainer 86%" in line for line in first)
    assert not any(
        "COMPACT" in line
        for line in poll(
            monkeypatch,
            {"prowl": [session("/w/spx/maintainer", "working")]},
            state,
            text=pane,
        )
    )


def test_monitor_reports_an_absent_position_once(monkeypatch):
    state: dict = {}
    first = poll(monkeypatch, {"prowl": []}, state)
    assert sum("ABSENT SPX Orchestrator" in line for line in first) == 1
    assert not any(
        "ABSENT SPX Orchestrator" in line
        for line in poll(monkeypatch, {"prowl": []}, state)
    )


def test_monitor_reports_a_broken_inventory_and_keeps_polling(monkeypatch):
    def broken():
        raise environment.AdapterError("prowl_environment.py: no answer within 30s")

    monkeypatch.setattr(environment.BACKENDS["prowl"], "sessions", broken)
    monkeypatch.setattr(environment.BACKENDS["herdr"], "sessions", lambda: [])
    state: dict = {}
    assert not any("WATCH-BROKEN" in line for line in monitor.poll(WATCH, state, NOW))
    lines = monitor.poll(WATCH, state, NOW)
    assert any("WATCH-BROKEN prowl inventory" in line for line in lines)


def test_monitor_names_the_disposition_for_each_mail_subject():
    assert monitor.mail_rule("note written") == monitor.RULES["note"]
    assert monitor.mail_rule("[shape review] #305 draft") == monitor.RULES["shape"]
    assert monitor.mail_rule("STATUS #320 06:19Z") == monitor.RULES["status"]
    assert monitor.mail_rule("Re 8620: two successors drafted; slice separate") == monitor.RULES["other"]
    assert monitor.mail_rule("Correction to 8636: shape review is 8635") != monitor.RULES["shape"]
    assert (
        monitor.mail_rule("[status] resumed; #320 Frame delta in shape review")
        == monitor.RULES["status"]
    )
    assert monitor.mail_rule("#343: test-evidence audit rejected") == monitor.GATE
    assert monitor.mail_rule("Close #74 now?") == monitor.RULES["question"]
    assert monitor.mail_rule("#320 merged") == monitor.RULES["other"]


def test_monitor_leaves_executor_legs_to_their_orchestrator(monkeypatch):
    state: dict = {}
    executor = session("/w/spx/worktrees/change-1", "working", "herdr", "change-1")
    poll(monkeypatch, {"herdr": [executor]}, state)
    idle = session("/w/spx/worktrees/change-1", "idle", "herdr", "change-1")
    assert not any("Executor" in line for line in poll(monkeypatch, {"herdr": [idle]}, state))
    assert not any("Executor" in line for line in poll(monkeypatch, {"herdr": []}, state))


def test_monitor_reports_an_executor_block_only_after_the_reminder(monkeypatch):
    state: dict = {}
    blocked = session("/w/spx/worktrees/change-1", "blocked", "herdr", "change-1")
    assert not any("BLOCKED" in line for line in poll(monkeypatch, {"herdr": [blocked]}, state))
    late = poll(monkeypatch, {"herdr": [blocked]}, state, now=NOW + timedelta(minutes=16))
    assert any("BLOCKED Executor change-1" in line and monitor.RULES["executor"] in line for line in late)


def test_monitor_signals_no_compaction_below_seventy_five_percent(monkeypatch):
    state: dict = {}
    lines = poll(
        monkeypatch,
        {"prowl": [session("/w/spx/maintainer", "idle")]},
        state,
        text="(600k/1M tokens) 60%",
    )
    assert not any("COMPACT" in line for line in lines)
