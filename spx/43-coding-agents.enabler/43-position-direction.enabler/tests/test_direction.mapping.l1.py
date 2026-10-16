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
    config = core.compose_configuration(
        tmp_path, tmp_path / "checkout", "Lead Director"
    )

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

    config = core.compose_configuration(
        tmp_path, tmp_path / "checkout", "Lead Director"
    )

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
        core.compose_configuration(tmp_path, tmp_path / "checkout", "Lead Director")

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
        checkout=tmp_path / "checkout",
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
        checkout=tmp_path / "checkout",
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
        checkout=tmp_path / "checkout",
    )

    result = json.loads(out.getvalue())
    assert status == 1
    assert result["status"] == "stopped"
    assert named in result["detail"]


def test_send_names_every_missing_argument(tmp_path: Path) -> None:
    out = StringIO()

    status = direction.main(
        ["send", "--position", "Lead Director", "--authority", "grant"],
        stdout=out,
        runtime=(_Mail(tmp_path), None),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
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
        core.compose_configuration(tmp_path, tmp_path / "checkout", "Lead Director")

    message = str(stop.value)
    assert "bogus" in message and "other" in message
    assert "interval_seconds" in message


def test_provider_load_stop_names_the_path_and_the_sibling_skill(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(core, "SKILLS_ROOT", tmp_path)

    with pytest.raises(core.DirectionError) as stop:
        core.load_sibling("operate-herdr", "herdr_environment")

    message = str(stop.value)
    assert str(tmp_path / "operate-herdr/scripts/herdr_environment.py") in message
    assert "coding-agents:operate-herdr" in message


def test_integer_key_stop_shows_the_value_found_and_an_accepted_form(
    tmp_path: Path,
) -> None:
    _override(tmp_path, "Lead Director", "+++\ninterval_seconds = 0\n+++\n")

    with pytest.raises(core.DirectionError) as stop:
        core.compose_configuration(tmp_path, tmp_path / "checkout", "Lead Director")

    message = str(stop.value)
    assert "interval_seconds" in message and "0" in message and "1800" in message


def test_unresolved_pane_detail_names_cwd_match_count_and_available_cwds() -> None:
    panes = [core.Pane("herdr", "w1:p1", "/work/a", None, None, None)]

    detail = core.unresolved_pane_detail(panes, "/work/missing", "Lead", "herdr")

    assert "/work/missing" in detail and "no herdr pane matched" in detail
    assert "/work/a" in detail


class _Herdr:
    SCHEMA_VERSION = 1

    def __init__(self) -> None:
        self.requests: list[dict] = []

    def execute(self, request: dict, runner: object) -> dict:
        self.requests.append(request)
        return {"status": "succeeded"}


def test_restart_relaunches_the_same_agent_kind_with_no_launch_arguments() -> None:
    herdr = _Herdr()
    envs = core.Environments(herdr, None, {"herdr": None})  # type: ignore[arg-type]
    pane = core.Pane("herdr", "w1:p1", "/work/a", "idle", "exec", "claude")

    result = envs.restart(pane, 1000)

    assert result["status"] == "succeeded"
    assert [r["operation"] for r in herdr.requests] == ["stop", "relaunch"]
    relaunch = herdr.requests[-1]
    assert relaunch["arguments"]["kind"] == "claude"
    assert "agent_arguments" not in relaunch["arguments"]


def test_prompt_without_text_stops_naming_the_argument_and_fix(
    tmp_path: Path,
) -> None:
    out = StringIO()

    status = direction.main(
        [
            "act",
            "--position",
            "Lead Director",
            "--authority",
            "grant",
            "--target",
            "x",
            "--operation",
            "prompt",
        ],
        stdout=out,
        runtime=(_Mail(tmp_path), None),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
    )

    result = json.loads(out.getvalue())
    assert status == 1
    assert "--text" in result["detail"] and "'x'" in result["detail"]


@pytest.mark.parametrize("subcommand", ["act", "send", "doorbell", "controller"])
def test_every_acting_subcommand_stops_without_authority_naming_the_fix(
    tmp_path: Path, subcommand: str
) -> None:
    out = StringIO()

    status = direction.main(
        [subcommand, "--position", "Lead Director"],
        stdout=out,
        runtime=(_Mail(tmp_path), None),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
    )

    detail = json.loads(out.getvalue())["detail"]
    assert status == 1
    assert subcommand in detail and "--authority" in detail
    assert "methodology chapter" in detail and "operator grant" in detail


@pytest.mark.parametrize(
    ("front_matter", "named"),
    [
        ("positions = 5\n", "key positions"),
        ('executor_groups = "x"\n', "key executor_groups"),
        ("launchers = 3\n", "key launchers"),
        ("untouchable_panes = 3\n", "key untouchable_panes"),
        (
            '[[positions]]\nname = "A"\nenvironment = "herdr"\ncwd = "/w"\n'
            'mail_name = "a"\nstall_minutes = "x"\ncontext_percent = 30\n',
            "positions[0].stall_minutes",
        ),
    ],
)
def test_wrong_typed_value_stops_naming_file_key_value_and_accepted_form(
    tmp_path: Path, front_matter: str, named: str
) -> None:
    path = _override(tmp_path, "Lead Director", f"+++\n{front_matter}+++\n")

    with pytest.raises(core.DirectionError) as stop:
        core.compose_configuration(tmp_path, tmp_path / "checkout", "Lead Director")

    message = str(stop.value)
    assert str(path) in message and named in message
    assert " as " in message


def test_position_entry_with_agent_arguments_is_an_unknown_field(
    tmp_path: Path,
) -> None:
    _override(
        tmp_path,
        "Lead Director",
        '+++\n[[positions]]\nname = "A"\nenvironment = "herdr"\ncwd = "/w"\n'
        'mail_name = "a"\nstall_minutes = 1\ncontext_percent = 30\n'
        "agent_arguments = []\n+++\n",
    )

    with pytest.raises(core.DirectionError) as stop:
        core.compose_configuration(tmp_path, tmp_path / "checkout", "Lead Director")

    assert "agent_arguments" in str(stop.value)


class _SentMail(_Mail):
    SCHEMA_VERSION = 1

    def __init__(self, common: Path) -> None:
        super().__init__(common)
        self.sent: list[dict] = []

    def message_record(self, **fields: object) -> dict:
        return dict(fields)

    def execute(self, request: dict, _runner: object) -> dict:
        self.sent.append(request["arguments"]["record"])
        return {"status": "succeeded"}


class _Panes:
    def __init__(self, panes: list, screen: str) -> None:
        self._panes = panes
        self._screen = screen

    def panes(self, _environment: str) -> list:
        return self._panes

    def read(self, _pane: object) -> str:
        return self._screen


def _director_file(tmp_path: Path) -> None:
    _override(
        tmp_path,
        "Lead Director",
        '+++\nadvisor = "advisor"\n[mail]\nagent = "director"\n'
        '[[positions]]\nname = "Worker"\nenvironment = "herdr"\ncwd = "/w"\n'
        'mail_name = "worker"\nstall_minutes = 0\ncontext_percent = 30\n+++\n',
    )


def test_controller_forwards_a_stalled_guarded_panes_screen_verbatim(
    tmp_path: Path,
) -> None:
    _director_file(tmp_path)
    mail = _SentMail(tmp_path)
    screen = "Do you want to proceed? (y/n)"
    pane = core.Pane("herdr", "w1:p1", "/w", "blocked", "worker", "claude")
    out = StringIO()

    status = direction.main(
        ["controller", "--position", "Lead Director", "--authority", "grant"],
        stdout=out,
        runtime=(mail, _Panes([pane], screen)),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
    )

    result = json.loads(out.getvalue())
    assert status == 0
    assert [r["body"] for r in mail.sent] == [screen]
    assert mail.sent[0]["recipient"] == "advisor"
    assert result["actions"][0]["action"] == "forward"
    assert result["actions"][0]["guards"] == ["question-or-approval-screen"]


def test_send_with_authority_sends_and_reports_the_authority(tmp_path: Path) -> None:
    _director_file(tmp_path)
    mail = _SentMail(tmp_path)
    body = tmp_path / "body.txt"
    body.write_text("hello", encoding="utf-8")
    out = StringIO()

    status = direction.main(
        [
            "send",
            "--position",
            "Lead Director",
            "--authority",
            "grant",
            "--recipient",
            "worker",
            "--subject",
            "s",
            "--correlation",
            "c",
            "--body-file",
            str(body),
        ],
        stdout=out,
        runtime=(mail, None),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
    )

    assert status == 0
    assert json.loads(out.getvalue())["authority"] == "grant"
    assert mail.sent[0]["body"] == "hello"


def test_act_on_a_guarded_pane_stops_naming_the_guard_screen_and_fix(
    tmp_path: Path,
) -> None:
    _director_file(tmp_path)
    pane = core.Pane("herdr", "w1:p1", "/w", "idle", "worker", "claude")
    out = StringIO()

    status = direction.main(
        [
            "act",
            "--position",
            "Lead Director",
            "--authority",
            "grant",
            "--target",
            "Worker",
            "--operation",
            "compact",
        ],
        stdout=out,
        runtime=(_SentMail(tmp_path), _Panes([pane], "Allow this edit? (y/n)")),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
    )

    result = json.loads(out.getvalue())
    assert status == 1
    assert result["screen"] == "Allow this edit? (y/n)"
    assert "question-or-approval-screen" in result["detail"]
    assert "w1:p1" in result["detail"]


def test_controller_with_advisor_unset_reports_forwarding_unavailable(
    tmp_path: Path,
) -> None:
    override = _override(
        tmp_path,
        "Lead Director",
        '+++\n[mail]\nagent = "director"\n'
        '[[positions]]\nname = "Worker"\nenvironment = "herdr"\ncwd = "/w"\n'
        'mail_name = "worker"\nstall_minutes = 0\ncontext_percent = 30\n+++\n',
    )
    mail = _SentMail(tmp_path)
    pane = core.Pane("herdr", "w1:p1", "/w", "idle", "worker", "claude")
    out = StringIO()

    direction.main(
        ["controller", "--position", "Lead Director", "--authority", "grant"],
        stdout=out,
        runtime=(mail, _Panes([pane], "quiet")),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
    )

    result = json.loads(out.getvalue())
    forward = result["actions"][0]
    assert mail.sent == []
    assert forward["label"] == "Worker"
    assert forward["action"] == "forward"
    assert forward["result"] == "unavailable"
    assert "advisor" in forward["detail"] and str(override) in forward["detail"]
    assert result["pace"] is None


@pytest.mark.parametrize(
    "arguments",
    [
        ["doorbell", "--authority", "grant"],
        ["inbox"],
        [
            "send",
            "--authority",
            "grant",
            "--recipient",
            "worker",
            "--subject",
            "s",
            "--correlation",
            "c",
        ],
    ],
)
def test_mail_operations_with_mail_agent_unset_report_unavailable(
    tmp_path: Path, arguments: list[str]
) -> None:
    override = tmp_path / ".spx/orchestration/lead-director.md"
    out = StringIO()

    status = direction.main(
        [arguments[0], "--position", "Lead Director", *arguments[1:]],
        stdout=out,
        runtime=(_SentMail(tmp_path), None),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
    )

    result = json.loads(out.getvalue())
    assert status == 1
    assert result["status"] == "unavailable"
    assert "mail.agent" in result["detail"] and str(override) in result["detail"]


def test_state_and_resume_note_live_in_the_invocation_checkout(tmp_path: Path) -> None:
    common = tmp_path / "common"
    checkout = tmp_path / "checkout"
    override = _override(common, "Lead Director", "+++\n+++\nExpect brevity.\n")

    config = core.compose_configuration(common, checkout, "Lead Director")

    state = checkout / ".spx/orchestration/state"
    assert config["stateDirectory"] == str(state)
    assert config["resumeNote"] == str(state / "resume-note.md")
    assert config["overrideFile"]["path"] == str(override)
    assert str(state / "resume-note.md") in config["resume_line"]
    assert str(override) in config["resume_line"]
    assert not (common / ".spx/orchestration/state").exists()


def test_send_rejects_a_body_file_outside_the_scratch_directory(tmp_path: Path) -> None:
    _director_file(tmp_path)
    mail = _SentMail(tmp_path)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    out = StringIO()

    status = direction.main(
        [
            "send",
            "--position",
            "Lead Director",
            "--authority",
            "grant",
            "--recipient",
            "worker",
            "--subject",
            "s",
            "--correlation",
            "c",
            "--body-file",
            "../outside.txt",
            "--scratch-directory",
            str(scratch),
        ],
        stdout=out,
        runtime=(mail, None),  # type: ignore[arg-type]
        checkout=tmp_path / "checkout",
    )

    result = json.loads(out.getvalue())
    assert status == 1
    assert result["status"] == "stopped"
    assert result["rejectedPath"] == "../outside.txt"
    assert result["resolvedPath"] == str(outside.resolve())
    assert result["scratchDirectory"] == str(scratch.resolve())
    assert mail.sent == []
