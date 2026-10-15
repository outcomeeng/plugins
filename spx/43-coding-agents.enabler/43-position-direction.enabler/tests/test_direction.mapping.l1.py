import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[4]
    / "src/plugins/coding-agents/skills/direct-positions/scripts"
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


core = _load("direction_core")
direction = _load("direction")


def _override(common: Path, name: str, text: str) -> Path:
    path = common / ".spx/orchestration" / core.override_file_name(name)
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_absent_override_file_composes_the_defaults(tmp_path: Path) -> None:
    config = core.compose_configuration(tmp_path, "Lead Director")

    assert config["overrideFile"]["present"] is False
    assert config["positions"] == []
    assert config["mail"] == {"channel": str(tmp_path), "agent": None}
    assert config["interval_seconds"] == core.DEFAULTS["interval_seconds"]


def test_override_file_name_lowercases_and_hyphenates() -> None:
    assert core.override_file_name("Lead Director") == "lead-director.md"


def test_set_keys_replace_defaults_and_omitted_keys_keep_them(tmp_path: Path) -> None:
    _override(
        tmp_path,
        "Lead Director",
        '+++\ninterval_seconds = 60\n[mail]\nagent = "director"\n+++\nExpect brevity.\n',
    )

    config = core.compose_configuration(tmp_path, "Lead Director")

    assert config["interval_seconds"] == 60
    assert config["mail"] == {"channel": str(tmp_path), "agent": "director"}
    assert config["compact_at_percent"] == core.DEFAULTS["compact_at_percent"]
    assert config["expectations"].strip() == "Expect brevity."


@pytest.mark.parametrize(
    "front_matter",
    ["bogus = 1\n", "interval_seconds = [\n", "interval_seconds = 0\n"],
)
def test_malformed_file_or_unknown_key_stops_naming_the_file(
    tmp_path: Path, front_matter: str
) -> None:
    path = _override(tmp_path, "Lead Director", f"+++\n{front_matter}+++\n")

    with pytest.raises(core.DirectionError) as stop:
        core.compose_configuration(tmp_path, "Lead Director")

    assert str(path) in str(stop.value)


def test_guards_name_untouchable_operator_and_question_panes() -> None:
    pane = core.Pane("herdr", "w1:p1", "/work", "idle", "worker", "claude")

    assert core.guard_reasons(pane, "ready", []) == []
    assert core.guard_reasons(pane, "ready", ["w1:p1"]) == ["untouchable"]
    assert core.guard_reasons(pane, "ready", [], "operator") == ["operator-prompt"]
    assert core.guard_reasons(pane, "Proceed? (y/n)", []) == [
        "question-or-approval-screen"
    ]
    blocked = core.Pane("herdr", "w1:p2", "/work", "blocked", "worker", "claude")
    assert core.guard_reasons(blocked, "", []) == ["question-or-approval-screen"]


def test_quiet_time_restarts_when_the_screen_changes() -> None:
    state: dict = {}

    assert core.quiet_minutes(state, "pane", "a", 0.0) == 0.0
    assert core.quiet_minutes(state, "pane", "a", 120.0) == 2.0
    assert core.quiet_minutes(state, "pane", "b", 180.0) == 0.0


def test_state_write_replaces_atomically_and_leaves_no_temporary(
    tmp_path: Path,
) -> None:
    core.write_state(tmp_path, "rungs.json", {"a": 1})
    core.write_state(tmp_path, "rungs.json", {"a": 2})

    assert core.read_state(tmp_path, "rungs.json") == {"a": 2}
    assert [p.name for p in tmp_path.iterdir()] == ["rungs.json"]


class _Mail:
    class AgentMailError(RuntimeError):
        pass

    class SubprocessRunner:
        pass

    def __init__(self, common: Path) -> None:
        self._common = common

    def resolve_project_key(self, _runner: object) -> str:
        return str(self._common)


def test_act_without_authority_stops_naming_both_absent_sources(tmp_path: Path) -> None:
    out = StringIO()

    status = direction.main(
        [
            "act",
            "--position",
            "Lead Director",
            "--target",
            "x",
            "--operation",
            "compact",
        ],
        stdout=out,
        runtime=(_Mail(tmp_path), None),  # type: ignore[arg-type]
    )

    result = json.loads(out.getvalue())
    assert status == 1
    assert result["status"] == "stopped"
    assert (
        "methodology chapter" in result["detail"]
        and "operator grant" in result["detail"]
    )


@pytest.mark.parametrize("subcommand", ["doorbell", "controller"])
def test_pass_without_authority_stops_before_any_action(
    tmp_path: Path, subcommand: str
) -> None:
    out = StringIO()

    status = direction.main(
        [subcommand, "--position", "Lead Director"],
        stdout=out,
        runtime=(_Mail(tmp_path), None),  # type: ignore[arg-type]
    )

    result = json.loads(out.getvalue())
    assert status == 1
    assert result["status"] == "stopped"
    assert (
        "methodology chapter" in result["detail"]
        and "operator grant" in result["detail"]
    )


@pytest.mark.parametrize(
    ("arguments", "named"),
    [
        (["--operation", "compact"], "--target"),
        (["--target", "x"], "--operation"),
    ],
)
def test_act_names_the_missing_argument_and_its_valid_options(
    tmp_path: Path, arguments: list[str], named: str
) -> None:
    out = StringIO()

    status = direction.main(
        ["act", "--position", "Lead Director", "--authority", "grant", *arguments],
        stdout=out,
        runtime=(_Mail(tmp_path), None),  # type: ignore[arg-type]
    )

    result = json.loads(out.getvalue())
    assert status == 1
    assert result["status"] == "stopped"
    assert named in result["detail"]


def test_send_names_every_missing_argument(tmp_path: Path) -> None:
    out = StringIO()

    status = direction.main(
        ["send", "--position", "Lead Director"],
        stdout=out,
        runtime=(_Mail(tmp_path), None),  # type: ignore[arg-type]
    )

    result = json.loads(out.getvalue())
    assert status == 1
    for name in ("--recipient", "--subject", "--correlation"):
        assert name in result["detail"]


def test_configuration_stop_names_every_unknown_key_and_the_valid_keys(
    tmp_path: Path,
) -> None:
    _override(tmp_path, "Lead Director", "+++\nbogus = 1\nother = 2\n+++\n")

    with pytest.raises(core.DirectionError) as stop:
        core.compose_configuration(tmp_path, "Lead Director")

    message = str(stop.value)
    assert "bogus" in message and "other" in message
    assert "interval_seconds" in message
